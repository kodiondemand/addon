# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Service for updating new episodes on library series
# ------------------------------------------------------------

import datetime, imp, math, threading, traceback, sys



from platformcode import config
try:
    import xbmc, os
    librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
    sys.path.append(librerias)
except:
    import os
    librerias = os.path.join(config.get_runtime_path(), 'lib')
    sys.path.append(librerias)




from core import channeltools, filetools, videolibrarytools
from platformcode import logger
from platformcode import platformtools
from specials import videolibrary
from lib import generictools


def update(path, p_dialog, i, t, serie, overwrite):
    logger.info("Actualizando " + path)
    insertados_total = 0
      
    head_nfo, it = videolibrarytools.read_nfo(path + '/tvshow.nfo')
    category = serie.category

    # logger.debug("%s: %s" %(serie.contentSerieName,str(list_canales) ))
    for channel, url in serie.library_urls.items():
        serie.channel = channel
        serie.url = url
        
        ###### Redirección al canal NewPct1.py si es un clone, o a otro canal y url si ha intervención judicial
        try:
            head_nfo, it = videolibrarytools.read_nfo(path + '/tvshow.nfo')         #Refresca el .nfo para recoger actualizaciones
            if it.emergency_urls:
                serie.emergency_urls = it.emergency_urls
            serie.category = category
        except:
            logger.error(traceback.format_exc())

        channel_enabled = channeltools.is_enabled(serie.channel)

        if channel_enabled:

            heading = config.get_localized_string(60389)
            p_dialog.update(int(math.ceil((i + 1) * t)), heading, "%s: %s" % (serie.contentSerieName,
                                                                              serie.channel.capitalize()))
            try:
                pathchannels = filetools.join(config.get_runtime_path(), "channels", serie.channel + '.py')
                logger.info("Cargando canal: " + pathchannels + " " +
                            serie.channel)

                if serie.library_filter_show:
                    serie.show = serie.library_filter_show.get(serie.channel, serie.contentSerieName)

                obj = imp.load_source(serie.channel, pathchannels)
                itemlist = obj.episodios(serie)

                try:
                    if int(overwrite) == 3:
                        # Sobrescribir todos los archivos (tvshow.nfo, 1x01.nfo, 1x01 [canal].json, 1x01.strm, etc...)
                        insertados, sobreescritos, fallidos, notusedpath = videolibrarytools.save_tvshow(serie, itemlist)
                        #serie= videolibrary.check_season_playcount(serie, serie.contentSeason)
                        #if filetools.write(path + '/tvshow.nfo', head_nfo + it.tojson()):
                        #    serie.infoLabels['playcount'] = serie.playcount
                    else:
                        insertados, sobreescritos, fallidos = videolibrarytools.save_episodes(path, itemlist, serie,
                                                                                              silent=True,
                                                                                              overwrite=overwrite)
                        #it = videolibrary.check_season_playcount(it, it.contentSeason)
                        #if filetools.write(path + '/tvshow.nfo', head_nfo + it.tojson()):
                        #    serie.infoLabels['playcount'] = serie.playcount
                    insertados_total += insertados

                except Exception, ex:
                    logger.error("Error al guardar los capitulos de la serie")
                    template = "An exception of type %s occured. Arguments:\n%r"
                    message = template % (type(ex).__name__, ex.args)
                    logger.error(message)

            except Exception, ex:
                logger.error("Error al obtener los episodios de: %s" % serie.show)
                template = "An exception of type %s occured. Arguments:\n%r"
                message = template % (type(ex).__name__, ex.args)
                logger.error(message)

        else:
            logger.debug("Canal %s no activo no se actualiza" % serie.channel)

    #Sincronizamos los episodios vistos desde la videoteca de Kodi con la de Alfa
    try:
        if config.is_xbmc():                #Si es Kodi, lo hacemos
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.mark_content_as_watched_on_alfa(path + '/tvshow.nfo')
    except:
        logger.error(traceback.format_exc())
    
    return insertados_total > 0


def check_for_update(overwrite=True):
    logger.info("Actualizando series...")
    p_dialog = None
    serie_actualizada = False
    update_when_finished = False
    hoy = datetime.date.today()
    estado_verify_playcount_series = False
    
    try:
        if config.get_setting("update", "videolibrary") != 0 or overwrite:
            config.set_setting("updatelibrary_last_check", hoy.strftime('%Y-%m-%d'), "videolibrary")

            heading = config.get_localized_string(60389)
            p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), heading)
            p_dialog.update(0, '')
            show_list = []

            for path, folders, files in filetools.walk(videolibrarytools.TVSHOWS_PATH):
                show_list.extend([filetools.join(path, f) for f in files if f == "tvshow.nfo"])

            if show_list:
                t = float(100) / len(show_list)

            for i, tvshow_file in enumerate(show_list):
                head_nfo, serie = videolibrarytools.read_nfo(tvshow_file)
                path = filetools.dirname(tvshow_file)
                    
                logger.info("serie=" + serie.contentSerieName)
                p_dialog.update(int(math.ceil((i + 1) * t)), heading, serie.contentSerieName)
                
                #Verificamos el estado del serie.library_playcounts de la Serie por si está incompleto
                try:
                    estado = False
                    #Si no hemos hecho la verificación o no tiene playcount, entramos
                    estado = config.get_setting("verify_playcount", "videolibrary")
                    if not estado or estado == False or not serie.library_playcounts:               #Si no se ha pasado antes, lo hacemos ahora
                        serie, estado = videolibrary.verify_playcount_series(serie, path)           #También se pasa si falta un PlayCount por completo
                except:
                    logger.error(traceback.format_exc())
                else:
                    if estado:                                                                      #Si ha tenido éxito la actualización...
                        estado_verify_playcount_series = True                                       #... se marca para cambiar la opción de la Videoteca

                interval = int(serie.active)  # Podria ser del tipo bool

                if not serie.active:
                    # si la serie no esta activa descartar
                    if overwrite_forced == False:
                        #Sincronizamos los episodios vistos desde la videoteca de Kodi con la de Alfa, aunque la serie esté desactivada
                        try:
                            if config.is_xbmc():                #Si es Kodi, lo hacemos
                                from platformcode import xbmc_videolibrary
                                xbmc_videolibrary.mark_content_as_watched_on_alfa(path + '/tvshow.nfo')
                        except:
                            logger.error(traceback.format_exc())
                    
                        continue

                # obtenemos las fecha de actualizacion y de la proxima programada para esta serie
                update_next = serie.update_next
                if update_next:
                    y, m, d = update_next.split('-')
                    update_next = datetime.date(int(y), int(m), int(d))
                else:
                    update_next = hoy

                update_last = serie.update_last
                if update_last:
                    y, m, d = update_last.split('-')
                    update_last = datetime.date(int(y), int(m), int(d))
                else:
                    update_last = hoy

                # si la serie esta activa ...
                if overwrite or config.get_setting("updatetvshows_interval", "videolibrary") == 0:
                    # ... forzar actualizacion independientemente del intervalo
                    serie_actualizada = update(path, p_dialog, i, t, serie, overwrite)
                    if not serie_actualizada:
                        update_next = hoy + datetime.timedelta(days=interval)

                elif interval == 1 and update_next <= hoy:
                    # ...actualizacion diaria
                    serie_actualizada = update(path, p_dialog, i, t, serie, overwrite)
                    if not serie_actualizada and update_last <= hoy - datetime.timedelta(days=7):
                        # si hace una semana q no se actualiza, pasar el intervalo a semanal
                        interval = 7
                        update_next = hoy + datetime.timedelta(days=interval)

                elif interval == 7 and update_next <= hoy:
                    # ...actualizacion semanal
                    serie_actualizada = update(path, p_dialog, i, t, serie, overwrite)
                    if not serie_actualizada:
                        if update_last <= hoy - datetime.timedelta(days=14):
                            # si hace 2 semanas q no se actualiza, pasar el intervalo a mensual
                            interval = 30

                        update_next += datetime.timedelta(days=interval)

                elif interval == 30 and update_next <= hoy:
                    # ...actualizacion mensual
                    serie_actualizada = update(path, p_dialog, i, t, serie, overwrite)
                    if not serie_actualizada:
                        update_next += datetime.timedelta(days=interval)
                        
                if serie_actualizada:
                    update_last = hoy
                    update_next = hoy + datetime.timedelta(days=interval)

                head_nfo, serie = videolibrarytools.read_nfo(tvshow_file)                       #Vuelve a leer el.nfo, que ha sido modificado
                if interval != int(serie.active) or update_next.strftime('%Y-%m-%d') != serie.update_next or update_last.strftime('%Y-%m-%d') != serie.update_last:
                    serie.update_last = update_last.strftime('%Y-%m-%d')
                    if update_next > hoy:
                        serie.update_next = update_next.strftime('%Y-%m-%d')
                    serie.active = interval
                    serie.channel = "videolibrary"
                    serie.action = "get_seasons"
                    filetools.write(tvshow_file, head_nfo + serie.tojson())

                if serie_actualizada:
                    if config.get_setting("search_new_content", "videolibrary") == 0:
                        # Actualizamos la videoteca de Kodi: Buscar contenido en la carpeta de la serie
                        if config.is_xbmc():
                            from platformcode import xbmc_videolibrary
                            xbmc_videolibrary.update(folder=filetools.basename(path))
                    else:
                        update_when_finished = True

            if estado_verify_playcount_series:                                                  #Si se ha cambiado algún playcount, ...
                estado = config.set_setting("verify_playcount", True, "videolibrary")           #... actualizamos la opción de Videolibrary
            
            if config.get_setting("search_new_content", "videolibrary") == 1 and update_when_finished:
                # Actualizamos la videoteca de Kodi: Buscar contenido en todas las series
                if config.is_xbmc():
                    from platformcode import xbmc_videolibrary
                    xbmc_videolibrary.update()

            p_dialog.close()

        else:
            logger.info("No actualiza la videoteca, está desactivado en la configuración de alfa")

    except Exception, ex:
        logger.error("Se ha producido un error al actualizar las series")
        template = "An exception of type %s occured. Arguments:\n%r"
        message = template % (type(ex).__name__, ex.args)
        logger.error(message)

        if p_dialog:
            p_dialog.close()
            
    from core.item import Item
    item_dummy = Item()
    videolibrary.list_movies(item_dummy, silent=True)


def start(thread=True):
    if thread:
        t = threading.Thread(target=start, args=[False])
        t.setDaemon(True)
        t.start()
    else:
        import time

        update_wait = [0, 10000, 20000, 30000, 60000]
        wait = update_wait[int(config.get_setting("update_wait", "videolibrary"))]
        if wait > 0:
            time.sleep(wait)

        if not config.get_setting("update", "videolibrary") == 2:
            check_for_update(overwrite=False)

        # Se ejecuta ciclicamente
        while True:
            monitor_update()
            time.sleep(3600)  # cada hora


def monitor_update():
    update_setting = config.get_setting("update", "videolibrary")

    # "Actualizar "Una sola vez al dia" o "al inicar Kodi y al menos una vez al dia"

    if update_setting == 2 or update_setting == 3:
        hoy = datetime.date.today()
        last_check = config.get_setting("updatelibrary_last_check", "videolibrary")
        if last_check:
            y, m, d = last_check.split('-')
            last_check = datetime.date(int(y), int(m), int(d))
        else:
            last_check = hoy - datetime.timedelta(days=1)

        update_start = config.get_setting("everyday_delay", "videolibrary") * 4

        # logger.info("Ultima comprobacion: %s || Fecha de hoy:%s || Hora actual: %s" %
        #             (last_check, hoy, datetime.datetime.now().hour))
        # logger.info("Atraso del inicio del dia: %i:00" % update_start)

        if last_check <= hoy and datetime.datetime.now().hour == int(update_start):
            logger.info("Inicio actualizacion programada para las %s h.: %s" % (update_start, datetime.datetime.now()))
            check_for_update(overwrite=False)


if __name__ == "__main__":
    # Se ejecuta en cada inicio
    import xbmc
    import time


    # modo adulto:
    # sistema actual 0: Nunca, 1:Siempre, 2:Solo hasta que se reinicie Kodi
    # si es == 2 lo desactivamos.
    if config.get_platform(True)['num_version'] >= 17.0:
        from lib.alfaresolver import updated, update_now
        if not updated():
            update_now()
    if config.get_setting("adult_mode") == 2:
        config.set_setting("adult_mode", 0)

    update_wait = [0, 10000, 20000, 30000, 60000]
    wait = update_wait[int(config.get_setting("update_wait", "videolibrary"))]
    if wait > 0:
        xbmc.sleep(wait)


    # Verificar quick-fixes al abrirse Kodi, y dejarlo corriendo como Thread
    if not os.path.isdir(config.get_runtime_path() + '/.git'):
        logger.info("DEV MODE OFF")
        from platformcode import updater
        updater.check_addon_init()
    else:
        logger.info("DEV MODE ON")

    # Copia Custom code a las carpetas de Alfa desde la zona de Userdata
    from platformcode import custom_code
    custom_code.init()

    # Identifica la dirección Proxy y la lista de alternativas
    from core import proxytools
    proxytools.get_proxy_list()
    if not config.get_setting("update", "videolibrary") == 2:
        check_for_update(overwrite=False)
    

    # Se ejecuta ciclicamente
    if config.get_platform(True)['num_version'] >= 14:
        monitor = xbmc.Monitor()  # For Kodi >= 14
    else:
        monitor = None  # For Kodi < 14

    if monitor:
        while not monitor.abortRequested():
            monitor_update()
            if monitor.waitForAbort(3600):  # cada hora
                break
    else:
        while not xbmc.abortRequested:
            monitor_update()
            xbmc.sleep(3600)
