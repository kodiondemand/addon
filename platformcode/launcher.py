# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Launcher (xbmc / kodi)
# ------------------------------------------------------------

import os
import sys
import urllib2
import time
import updater
from core import channeltools
from core import scrapertools
from core import servertools
from core import videolibrarytools
from core import trakt_tools
from core.item import Item
from platformcode import config, logger
from platformcode import platformtools
from platformcode.logger import WebErrorException


def start():
    """ Primera funcion que se ejecuta al entrar en el plugin.
    Dentro de esta funcion deberian ir todas las llamadas a las
    funciones que deseamos que se ejecuten nada mas abrir el plugin.
    """
    logger.info()
    #config.set_setting('show_once', True)
    # Test if all the required directories are created
    config.verify_directories_created()


def run(item=None):
    logger.info()
    if not item:
        # Extract item from sys.argv
        if sys.argv[2]:
            item = Item().fromurl(sys.argv[2])

        # If no item, this is mainlist
        else:
            if config.get_setting("start_page"):

                if not config.get_setting("custom_start"):
                    dictCategory = {
                        config.get_localized_string(70137): 'peliculas',
                        config.get_localized_string(30123): 'series',
                        config.get_localized_string(30124): 'anime',
                        config.get_localized_string(70018): 'infantiles',
                        config.get_localized_string(60513): 'documentales',
                        config.get_localized_string(70013): 'terror',
                        config.get_localized_string(30124): 'castellano',
                        config.get_localized_string(59976): 'latino',
                        config.get_localized_string(70171): 'torrent',
                    }
                    category = dictCategory[config.get_setting("category")]
                    item = Item(channel="news", action="novedades", extra=category, mode = 'silent')
                else:
                    from channels import side_menu
                    item= Item()
                    item = side_menu.check_user_home(item)
                    item.start = True
            else:
                item = Item(channel="channelselector", action="getmainlist", viewmode="movie")
        if not config.get_setting('show_once'):
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.ask_set_content(1)
            config.set_setting('show_once', True)

    logger.info(item.tostring())

    try:
        # If item has no action, stops here
        if item.action == "":
            logger.info("Item sin accion")
            return
        
        if item.action == "update":
            updater.update()

        # Action for main menu in channelselector
        elif item.action == "getmainlist":
            import channelselector

            itemlist = channelselector.getmainlist()

            platformtools.render_items(itemlist, item)

        # Action for channel types on channelselector: movies, series, etc.
        elif item.action == "getchanneltypes":
            import channelselector
            itemlist = channelselector.getchanneltypes()

            platformtools.render_items(itemlist, item)

        # Action for channel listing on channelselector
        elif item.action == "filterchannels":
            import channelselector
            itemlist = channelselector.filterchannels(item.channel_type)

            platformtools.render_items(itemlist, item)

        # Special action for playing a video from the library
        elif item.action == "play_from_library":
            play_from_library(item)
            return

        elif item.action == "keymap":
            from platformcode import keymaptools
            if item.open:
                return keymaptools.open_shortcut_menu()
            else:
                return keymaptools.set_key()

        elif item.action == "script":
            from core import tmdb
            if tmdb.drop_bd():
                platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(60011), time=2000, sound=False)

        # Action in certain channel specified in "action" and "channel" parameters
        else:
            # Entry point for a channel is the "mainlist" action, so here we check parental control
            if item.action == "mainlist":
                #updater.checkforupdates() beta version checking for update, still disabled

                # Parental control
                # If it is an adult channel, and user has configured pin, asks for it
                if channeltools.is_adult(item.channel) and config.get_setting("adult_request_password"):
                    tecleado = platformtools.dialog_input("", config.get_localized_string(60334), True)
                    if tecleado is None or tecleado != config.get_setting("adult_password"):
                        return
            # # Actualiza el canal individual
            # if (item.action == "mainlist" and item.channel != "channelselector" and
            #             config.get_setting("check_for_channel_updates") == True):
            #     from core import updater
            #     updater.update_channel(item.channel)

            # Checks if channel exists
            channel_file = os.path.join(config.get_runtime_path(),
                                        'channels', item.channel + ".py")
            logger.info("channel_file=%s" % channel_file)

            channel = None

            if os.path.exists(channel_file):
                try:
                    channel = __import__('channels.%s' % item.channel, None,
                                         None, ["channels.%s" % item.channel])
                except ImportError:
                    exec "import channels." + item.channel + " as channel"

            logger.info("Running channel %s | %s" % (channel.__name__, channel.__file__))

            # Special play action
            if item.action == "play":
                #define la info para trakt
                try:
                    trakt_tools.set_trakt_info(item)
                except:
                    pass
                logger.info("item.action=%s" % item.action.upper())
                # logger.debug("item_toPlay: " + "\n" + item.tostring('\n'))

                # First checks if channel has a "play" function
                if hasattr(channel, 'play'):
                    logger.info("Executing channel 'play' method")
                    itemlist = channel.play(item)
                    b_favourite = item.isFavourite
                    # Play should return a list of playable URLS
                    if len(itemlist) > 0 and isinstance(itemlist[0], Item):
                        item = itemlist[0]
                        if b_favourite:
                            item.isFavourite = True
                        platformtools.play_video(item)

                    # Permitir varias calidades desde play en el canal
                    elif len(itemlist) > 0 and isinstance(itemlist[0], list):
                        item.video_urls = itemlist
                        platformtools.play_video(item)

                    # If not, shows user an error message
                    else:
                        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(60339))

                # If player don't have a "play" function, not uses the standard play from platformtools
                else:
                    logger.info("Executing core 'play' method")
                    platformtools.play_video(item)

            # Special action for findvideos, where the plugin looks for known urls
            elif item.action == "findvideos":

                # First checks if channel has a "findvideos" function
                if hasattr(channel, 'findvideos'):
                    itemlist = getattr(channel, item.action)(item)
                    itemlist = servertools.filter_servers(itemlist)

                # If not, uses the generic findvideos function
                else:
                    logger.info("No channel 'findvideos' method, "
                                "executing core method")
                    itemlist = servertools.find_video_items(item)

                if config.get_setting("max_links", "videolibrary") != 0:
                    itemlist = limit_itemlist(itemlist)

                from platformcode import subtitletools
                subtitletools.saveSubtitleName(item)

                platformtools.render_items(itemlist, item)

            # Special action for adding a movie to the library
            elif item.action == "add_pelicula_to_library":
                videolibrarytools.add_movie(item)

            # Special action for adding a serie to the library
            elif item.action == "add_serie_to_library":
                videolibrarytools.add_tvshow(item, channel)

            # Special action for downloading all episodes from a serie
            elif item.action == "download_all_episodes":
                from channels import downloads
                item.action = item.extra
                del item.extra
                downloads.save_download(item)

            # Special action for searching, first asks for the words then call the "search" function
            elif item.action == "search":
                logger.info("item.action=%s" % item.action.upper())

                last_search = ""
                last_search_active = config.get_setting("last_search", "search")
                if last_search_active:
                    try:
                        current_saved_searches_list = list(config.get_setting("saved_searches_list", "search"))
                        last_search = current_saved_searches_list[0]
                    except:
                        pass

                tecleado = platformtools.dialog_input(last_search)
                if tecleado is not None:
                    if last_search_active and not tecleado.startswith("http"):
                        from channels import search
                        search.save_search(tecleado)

                    itemlist = channel.search(item, tecleado)
                else:
                    return

                platformtools.render_items(itemlist, item)

            # For all other actions
            else:
                logger.info("Executing channel '%s' method" % item.action)
                itemlist = getattr(channel, item.action)(item)
                if config.get_setting('trakt_sync'):
                    token_auth = config.get_setting("token_trakt", "trakt")
                    if not token_auth:
                        trakt_tools.auth_trakt()
                    else:
                        import xbmc
                        if not xbmc.getCondVisibility('System.HasAddon(script.trakt)') and config.get_setting(
                                'install_trakt'):
                            trakt_tools.ask_install_script()
                    itemlist = trakt_tools.trakt_check(itemlist)
                else:
                    config.set_setting('install_trakt', True)

                platformtools.render_items(itemlist, item)

    except urllib2.URLError, e:
        import traceback
        logger.error(traceback.format_exc())

        # Grab inner and third party errors
        if hasattr(e, 'reason'):
            logger.error("Razon del error, codigo: %s | Razon: %s" % (str(e.reason[0]), str(e.reason[1])))
            texto = config.get_localized_string(30050)  # "No se puede conectar con el sitio web"
            platformtools.dialog_ok("alfa", texto)

        # Grab server response errors
        elif hasattr(e, 'code'):
            logger.error("Codigo de error HTTP : %d" % e.code)
            # "El sitio web no funciona correctamente (error http %d)"
            platformtools.dialog_ok("alfa", config.get_localized_string(30051) % e.code)
    except WebErrorException, e:
        import traceback
        logger.error(traceback.format_exc())

        patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\",
                                                                                            "\\\\") + '([^.]+)\.py"'
        canal = scrapertools.find_single_match(traceback.format_exc(), patron)

        platformtools.dialog_ok(
            config.get_localized_string(59985) + canal,
            config.get_localized_string(60013) %(e))
    except:
        import traceback
        logger.error(traceback.format_exc())

        patron = 'File "' + os.path.join(config.get_runtime_path(), "channels", "").replace("\\",
                                                                                            "\\\\") + '([^.]+)\.py"'
        canal = scrapertools.find_single_match(traceback.format_exc(), patron)

        try:
            import xbmc
            if config.get_platform(True)['num_version'] < 14:
                log_name = "xbmc.log"
            else:
                log_name = "kodi.log"
            log_message = config.get_localized_string(50004) + xbmc.translatePath("special://logpath") + log_name
        except:
            log_message = ""

        if canal:
            platformtools.dialog_ok(
                config.get_localized_string(60087) %canal,
                config.get_localized_string(60014),
                log_message)
        else:
            platformtools.dialog_ok(
                config.get_localized_string(60038),
                config.get_localized_string(60015),
                log_message)



def reorder_itemlist(itemlist):
    logger.info()
    # logger.debug("Inlet itemlist size: %i" % len(itemlist))

    new_list = []
    mod_list = []
    not_mod_list = []

    modified = 0
    not_modified = 0

    to_change = [[config.get_localized_string(60335), '[V]'],
                 [config.get_localized_string(60336), '[D]']]

    for item in itemlist:
        old_title = unicode(item.title, "utf8").lower().encode("utf8")
        for before, after in to_change:
            if before in item.title:
                item.title = item.title.replace(before, after)
                break

        new_title = unicode(item.title, "utf8").lower().encode("utf8")
        if old_title != new_title:
            mod_list.append(item)
            modified += 1
        else:
            not_mod_list.append(item)
            not_modified += 1

            # logger.debug("OLD: %s | NEW: %s" % (old_title, new_title))

    new_list.extend(mod_list)
    new_list.extend(not_mod_list)

    logger.info("Titulos modificados:%i | No modificados:%i" % (modified, not_modified))

    if len(new_list) == 0:
        new_list = itemlist

    # logger.debug("Outlet itemlist size: %i" % len(new_list))
    return new_list


def limit_itemlist(itemlist):
    logger.info()
    # logger.debug("Inlet itemlist size: %i" % len(itemlist))

    try:
        opt = config.get_setting("max_links", "videolibrary")
        if opt == 0:
            new_list = itemlist
        else:
            i_max = 30 * opt
            new_list = itemlist[:i_max]

        # logger.debug("Outlet itemlist size: %i" % len(new_list))
        return new_list
    except:
        return itemlist


def play_from_library(item):
    """
        Los .strm al reproducirlos desde kodi, este espera que sea un archivo "reproducible" asi que no puede contener
        más items, como mucho se puede colocar un dialogo de seleccion.
        Esto lo solucionamos "engañando a kodi" y haciendole creer que se ha reproducido algo, asi despues mediante
        "Container.Update()" cargamos el strm como si un item desde dentro del addon se tratara, quitando todas
        las limitaciones y permitiendo reproducir mediante la funcion general sin tener que crear nuevos métodos para
        la videoteca.
        @type item: item
        @param item: elemento con información
    """
    logger.info()
    #logger.debug("item: \n" + item.tostring('\n'))

    import xbmcgui
    import xbmcplugin
    import xbmc
    from time import sleep
    
    # Intentamos reproducir una imagen (esto no hace nada y ademas no da error)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True,
                              xbmcgui.ListItem(
                                  path=os.path.join(config.get_runtime_path(), "resources", "subtitle.mp4")))

    # Por si acaso la imagen hiciera (en futuras versiones) le damos a stop para detener la reproduccion
    sleep(0.5)              ### Si no se pone esto se bloquea Kodi
    xbmc.Player().stop()

    # modificamos el action (actualmente la videoteca necesita "findvideos" ya que es donde se buscan las fuentes
    item.action = "findvideos"

    window_type = config.get_setting("window_type", "videolibrary")

    # y volvemos a lanzar kodi
    if xbmc.getCondVisibility('Window.IsMedia') and not window_type == 1:
        # Ventana convencional
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")

    else:
        # Ventana emergente
        from channels import videolibrary
        p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(70004))
        p_dialog.update(0, '')

        itemlist = videolibrary.findvideos(item)


        while platformtools.is_playing():
                # Ventana convencional
                sleep(5)
        p_dialog.update(50, '')

        '''# Se filtran los enlaces segun la lista negra
        if config.get_setting('filter_servers', "servers"):
            itemlist = servertools.filter_servers(itemlist)'''

        # Se limita la cantidad de enlaces a mostrar
        if config.get_setting("max_links", "videolibrary") != 0:
            itemlist = limit_itemlist(itemlist)

        # Se "limpia" ligeramente la lista de enlaces
        if config.get_setting("replace_VD", "videolibrary") == 1:
            itemlist = reorder_itemlist(itemlist)


        import time
        p_dialog.update(100, '')
        time.sleep(0.5)
        p_dialog.close()


        if len(itemlist) > 0:
            while not xbmc.Monitor().abortRequested():
                # El usuario elige el mirror
                opciones = []
                for item in itemlist:
                    opciones.append(item.title)

                # Se abre la ventana de seleccion
                if (item.contentSerieName != "" and
                            item.contentSeason != "" and
                            item.contentEpisodeNumber != ""):
                    cabecera = ("%s - %sx%s -- %s" %
                                (item.contentSerieName,
                                 item.contentSeason,
                                 item.contentEpisodeNumber,
                                 config.get_localized_string(30163)))
                else:
                    cabecera = config.get_localized_string(30163)

                seleccion = platformtools.dialog_select(cabecera, opciones)

                if seleccion == -1:
                    return
                else:
                    item = videolibrary.play(itemlist[seleccion])[0]
                    platformtools.play_video(item)

                from channels import autoplay
                if (platformtools.is_playing() and item.action) or item.server == 'torrent' or autoplay.is_active(item.contentChannel):
                    break
