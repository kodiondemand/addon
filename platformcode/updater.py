# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------

import os, sys
import time
import threading
import traceback
import urllib
import json
import xbmc


from platformcode import config, logger, platformtools

from core import httptools
from core import jsontools
from core import downloadtools
from core import ziptools
from core import filetools

REMOTE_FILE = "https://github.com/kodiondemand/addon/archive/master.zip"
DESTINATION_FOLDER = xbmc.translatePath("special://home/addons") + "/plugin.video.kod"
REMOTE_VERSION_FILE = "https://raw.githubusercontent.com/kodiondemand/addon/master/version.json"

def check_addon_init():
    logger.info()
    
    # Subtarea de monitor.  Se activa cada X horas para comprobar si hay FIXES al addon
    def check_addon_monitor():
        logger.info()
        
        # Obtiene el íntervalo entre actualizaciones y si se quieren mensajes
        try:
            timer = int(config.get_setting('addon_update_timer'))       # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                return                                                  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message')
        except:
            timer = 12                                                  # Por defecto cada 12 horas
            verbose = False                                             # Por defecto, sin mensajes
        timer = timer * 3600                                            # Lo pasamos a segundos

        if config.get_platform(True)['num_version'] >= 14:              # Si es Kodi, lanzamos el monitor
            import xbmc
            monitor = xbmc.Monitor()
        else:                                                           # Lanzamos solo una actualización y salimos
            check_addon_updates(verbose)                                # Lanza la actualización
            return
            
        while not monitor.abortRequested():                             # Loop infinito hasta cancelar Kodi

            check_addon_updates(verbose)                                # Lanza la actualización
            
            if monitor.waitForAbort(timer):                             # Espera el tiempo programado o hasta que cancele Kodi
                break                                                   # Cancelación de Kodi, salimos
                
        return
                
    # Lanzamos en Servicio de actualización de FIXES
    try:
        threading.Thread(target=check_addon_monitor).start()            # Creamos un Thread independiente, hasta el fin de Kodi
        time.sleep(5)                                                   # Dejamos terminar la primera verificación...
    except:                                                             # Si hay problemas de threading, se llama una sola vez
        try:
            timer = int(config.get_setting('addon_update_timer'))       # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                return                                                  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message')
        except:
            verbose = False                                             # Por defecto, sin mensajes
            pass
        check_addon_updates(verbose)                                    # Lanza la actualización, en Ajustes de Alfa
        time.sleep(5)                                                   # Dejamos terminar la primera verificación...
              
    return

def checkforupdates(plugin_mode=True):
    logger.info("kodiondemand.core.updater checkforupdates")

    response = urllib.urlopen(REMOTE_VERSION_FILE)
    data = json.loads(response.read())

    '''    
    {
	"update": {
		"name": "Kodi on Demand",
		"tag": "1.0.0",
		"version": "1000",
		"date": "03/05/2019",
		"changes": "Added Updater"
	    }
    }   
    '''
    # remote is addon version without dots
    remote_version = data["update"]["version"]
    # tag version is version with dots used to a betterview gui
    tag_version = data["update"]["tag"]
    logger.info("kodiondemand.core.updater version remota="+tag_version+" "+remote_version)
    
    '''
    # Lee el fichero con la versión instalada
    localFileName = LOCAL_VERSION_FILE
    logger.info("kodiondemand.core.updater fichero local version: "+localFileName)
    infile = open( localFileName )
    data = infile.read()
    infile.close()
    #logger.info("xml local="+data)
    '''
    path_local = xbmc.translatePath("special://home/addons/") + "plugin.video.kod/version.json"
    data = json.loads(open(path_local).read())

    version_local = data["update"]["version"]
    tag_local = data["update"]["tag"]
    logger.info("kodiondemand.core.updater version local="+tag_local+" "+version_local)

    try:
        numero_remote_version = int(remote_version)
        numero_version_local = int(version_local)
    except:
        import traceback
        logger.info(traceback.format_exc())
        remote_version = ""
        version_local = ""

    if remote_version=="" or version_local=="":
        arraydescargada = tag_version.split(".")
        arraylocal = tag_local.split(".")

        # local 2.8.0 - descargada 2.8.0 -> no descargar
        # local 2.9.0 - descargada 2.8.0 -> no descargar
        # local 2.8.0 - descargada 2.9.0 -> descargar
        if len(arraylocal) == len(arraydescargada):
            logger.info("caso 1")
            hayqueactualizar = False
            for i in range(0, len(arraylocal)):
                print arraylocal[i], arraydescargada[i], int(arraydescargada[i]) > int(arraylocal[i])
                if int(arraydescargada[i]) > int(arraylocal[i]):
                    hayqueactualizar = True
        # local 2.8.0 - descargada 2.8 -> no descargar
        # local 2.9.0 - descargada 2.8 -> no descargar
        # local 2.8.0 - descargada 2.9 -> descargar
        if len(arraylocal) > len(arraydescargada):
            logger.info("caso 2")
            hayqueactualizar = False
            for i in range(0, len(arraydescargada)):
                #print arraylocal[i], arraydescargada[i], int(arraydescargada[i]) > int(arraylocal[i])
                if int(arraydescargada[i]) > int(arraylocal[i]):
                    hayqueactualizar = True
        # local 2.8 - descargada 2.8.8 -> descargar
        # local 2.9 - descargada 2.8.8 -> no descargar
        # local 2.10 - descargada 2.9.9 -> no descargar
        # local 2.5 - descargada 3.0.0
        if len(arraylocal) < len(arraydescargada):
            logger.info("caso 3")
            hayqueactualizar = True
            for i in range(0, len(arraylocal)):
                #print arraylocal[i], arraydescargada[i], int(arraylocal[i])>int(arraydescargada[i])
                if int(arraylocal[i]) > int(arraydescargada[i]):
                    hayqueactualizar =  False
                elif int(arraylocal[i]) < int(arraydescargada[i]):
                    hayqueactualizar =  True
                    break
    else:
        hayqueactualizar = (numero_remote_version > numero_version_local)

    if hayqueactualizar:
    
        if plugin_mode:
    
            logger.info("kodiondemand.core.updater actualizacion disponible")
            
            # Añade al listado de XBMC
            import xbmcgui
            #thumbnail = IMAGES_PATH+"Crystal_Clear_action_info.png"
            thumbnail = os.path.join(config.get_runtime_path() , "resources" , "images", "service_update.png")
            logger.info("thumbnail="+thumbnail)
            listitem = xbmcgui.ListItem( "Scarica la versione "+tag_version, thumbnailImage=thumbnail )
            itemurl = '%s?action=update&version=%s' % ( sys.argv[ 0 ] , tag_version )
            import xbmcplugin
            xbmcplugin.addDirectoryItem( handle = int(sys.argv[ 1 ]), url = itemurl , listitem=listitem, isFolder=True)
            
            # Avisa con un popup
            dialog = xbmcgui.Dialog()
            dialog.ok("Versione "+tag_version+" disponibile","E' possibile scaricare la nuova versione del plugin\nattraverso l'opzione nel menù principale.")

        else:

            import xbmcgui
            yes_pressed = xbmcgui.Dialog().yesno( "Versione "+tag_version+" disponibile" , "Installarla?" )

            if yes_pressed:
                params = {"version":tag_version}
                update(params)


def update():
    # Descarga el ZIP
    logger.info("kodiondemand.core.updater update")
    remotefilename = REMOTE_FILE
    localfilename = xbmc.translatePath("special://home/addons/") + "plugin.video.kod/addon-master.zip"
    logger.info("kodiondemand.core.updater remotefilename=%s" % remotefilename)
    logger.info("kodiondemand.core.updater localfilename=%s" % localfilename)
    logger.info("kodiondemand.core.updater descarga fichero...")
    
    #urllib.urlretrieve(remotefilename,localfilename)
    from core import downloadtools
    downloadtools.downloadfile(remotefilename, localfilename, continuar=False)
    
    # Lo descomprime
    logger.info("kodiondemand.core.updater descomprime fichero...")
    unzipper = ziptools.ziptools()
    destpathname = xbmc.translatePath("special://home/addons/") + "plugin.video.kod"
    logger.info("kodiondemand.core.updater destpathname=%s" % destpathname)
    unzipper.extract(localfilename,destpathname)
    
    # Borra el zip descargado
    logger.info("kodiondemand.core.updater borra fichero...")
    os.remove(localfilename)
    logger.info("kodiondemand.core.updater ...fichero borrado")

    
'''
def check_addon_updates(verbose=False):
    logger.info()

    ADDON_UPDATES_JSON = 'https://extra.alfa-addon.com/addon_updates/updates.json'
    ADDON_UPDATES_ZIP = 'https://extra.alfa-addon.com/addon_updates/updates.zip'

    try:
        last_fix_json = os.path.join(config.get_runtime_path(), 'last_fix.json')   # información de la versión fixeada del usuario
        # Se guarda en get_runtime_path en lugar de get_data_path para que se elimine al cambiar de versión

        # Descargar json con las posibles actualizaciones
        # -----------------------------------------------
        data = httptools.downloadpage(ADDON_UPDATES_JSON, timeout=2).data
        if data == '': 
            logger.info('No se encuentran actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification(config.get_localized_string(70667), config.get_localized_string(70668))
            return False

        data = jsontools.load(data)
        if 'addon_version' not in data or 'fix_version' not in data: 
            logger.info('No hay actualizaciones del addon')
            if verbose:
                platformtools.dialog_notification(config.get_localized_string(70667), config.get_localized_string(70668))
            return False

        # Comprobar versión que tiene instalada el usuario con versión de la actualización
        # --------------------------------------------------------------------------------
        current_version = config.get_addon_version(with_fix=False)
        if current_version != data['addon_version']:
            logger.info('No hay actualizaciones para la versión %s del addon' % current_version)
            if verbose:
                platformtools.dialog_notification(config.get_localized_string(70667), config.get_localized_string(70668))
            return False

        if os.path.exists(last_fix_json):
            try:
                lastfix =  {} 
                lastfix = jsontools.load(filetools.read(last_fix_json))
                if lastfix['addon_version'] == data['addon_version'] and lastfix['fix_version'] == data['fix_version']:
                    logger.info(config.get_localized_string(70670) % (data['addon_version'], data['fix_version']))
                    if verbose:
                        platformtools.dialog_notification(config.get_localized_string(70667), config.get_localized_string(70671) % (data['addon_version'], data['fix_version']))
                    return False
            except:
                if lastfix:
                    logger.error('last_fix.json: ERROR en: ' + str(lastfix))
                else:
                    logger.error('last_fix.json: ERROR desconocido')
                lastfix =  {}

        # Descargar zip con las actualizaciones
        # -------------------------------------
        localfilename = os.path.join(config.get_data_path(), 'temp_updates.zip')
        if os.path.exists(localfilename): os.remove(localfilename)

        downloadtools.downloadfile(ADDON_UPDATES_ZIP, localfilename, silent=True)
        
        # Descomprimir zip dentro del addon
        # ---------------------------------
        try:
            unzipper = ziptools.ziptools()
            unzipper.extract(localfilename, config.get_runtime_path())
        except:
            import xbmc
            xbmc.executebuiltin('XBMC.Extract("%s", "%s")' % (localfilename, config.get_runtime_path()))
            time.sleep(1)
        
        # Borrar el zip descargado
        # ------------------------
        os.remove(localfilename)
        
        # Guardar información de la versión fixeada
        # -----------------------------------------
        if 'files' in data: data.pop('files', None)
        filetools.write(last_fix_json, jsontools.dump(data))
        
        logger.info(config.get_localized_string(70672) % (data['addon_version'], data['fix_version']))
        if verbose:
            platformtools.dialog_notification(config.get_localized_string(70673), config.get_localized_string(70671) % (data['addon_version'], data['fix_version']))
        return True

    except:
        logger.error('Error al comprobar actualizaciones del addon!')
        logger.error(traceback.format_exc())
        if verbose:
            platformtools.dialog_notification(config.get_localized_string(70674), config.get_localized_string(70675))
        return False
'''