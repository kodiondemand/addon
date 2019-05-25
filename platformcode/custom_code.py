# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------

import json
import os
import traceback

import xbmc
import xbmcaddon

from core import filetools
from core import jsontools
from platformcode import config, logger, platformtools

json_data_file_name = 'custom_code.json'


def init():
    logger.info()

    """
    Todo el código añadido al add-on se borra con cada actualización.  Esta función permite restaurarlo automáticamente con cada actualización.
    Esto permite al usuario tener su propio código, bajo su responsabilidad, y restaurarlo al add-on cada vez que se actualiza.
    
    El mecanismo funciona copiando el contenido de la carpeta-arbol ".\userdata\addon_data\plugin.video.alfa\custom_code\..." sobre
    las carpetas de código del add-on.  No verifica el contenido, solo vuelca(reemplaza) el contenido de "custom_code".
    
    El usuario almacenará en las subcarpetas de "custom_code" su código actualizado y listo para ser copiado en cualquier momento.
    Si no se desea que copie algo, simplemente se borra de "custom_code" y ya no se copiará en la próxima actualización.
    
    Los pasos que sigue esta función, son los siguientes:
    
    1.- La función se llama desde videolibrary_service.py, desde la función inicial:
            # Copia Custom code a las carpetas de Alfa desde la zona de Userdata
            from platformcode import custom_code
            custom_code.init()
            
    2.- En el inicio de Kodi, comprueba si existe la carpeta "custom_code" en ".\userdata\addon_data\plugin.video.alfa\".  
        Si no existe, la crea y sale sin más, dando al ususario la posibilidad de copiar sobre esa estructura su código, 
        y que la función la vuelque sobre el add-on en el próximo inicio de Kodi.
        
    3.- En el siguiente inicio de Kodi, comprueba si existe el custom_code.json en la carpeta root del add-on.
        Si no existe, lo crea con el número de versión del add-on vacío, para permitir que se copien los archivos en esta pasada.
        
    4.- Verifica que el número de versión del add-on es diferente de el de custom_code.json.  Si es la misma versión, 
        se sale porque ya se realizo la copia anteriormente.
        Si la versión es distinta, se realiza el volcado de todos los archivos de la carpeta-árbol "custom_code" sobre el add-on.
        Si la carpeta de destino no existe, dará un error y se cancelará la copia.  Se considera que no tienen sentido nuevas carpetas.
        
    5.- Si la copia ha terminado con éxito, se actualiza el custom_code.json con el número de versión del add-on,
        para que en inicios sucesivos de Kodi no se realicen las copias, hasta que el add-on cambie de versión.
        En el número de versión del add-on no se considera el número de fix.
        
    Tiempos:    Copiando 7 archivos de prueba, el proceso ha tardado una décima de segundo.
    """
    
    try:
        #Verifica si Kodi tiene algún achivo de Base de Datos de Vídeo de versiones anteriores, entonces los borra
        verify_Kodi_video_DB()
        
        #QUASAR: Preguntamos si se hacen modificaciones a Quasar
        if not filetools.exists(os.path.join(config.get_data_path(), "quasar.json")) and not config.get_setting('addon_quasar_update', default=False):
            question_update_external_addon("quasar")
        
        #QUASAR: Hacemos las modificaciones a Quasar, si está permitido, y si está instalado
        if config.get_setting('addon_quasar_update', default=False):
            if not update_external_addon("quasar"):
                platformtools.dialog_notification("Actualización Quasar", "Ha fallado. Consulte el log")
        
        #Existe carpeta "custom_code" ? Si no existe se crea y se sale
        custom_code_dir = os.path.join(config.get_data_path(), 'custom_code')
        if os.path.exists(custom_code_dir) == False:
            create_folder_structure(custom_code_dir)
            return
        
        else:
            #Existe "custom_code.json" ? Si no existe se crea
            custom_code_json_path = config.get_runtime_path()
            custom_code_json = os.path.join(custom_code_json_path, 'custom_code.json')
            if os.path.exists(custom_code_json) == False:
                create_json(custom_code_json_path)
            
            #Se verifica si la versión del .json y del add-on son iguales.  Si es así se sale.  Si no se copia "custom_code" al add-on
            verify_copy_folders(custom_code_dir, custom_code_json_path)
    except:
        logger.error(traceback.format_exc())
            

def create_folder_structure(custom_code_dir):
    logger.info()

    #Creamos todas las carpetas.  La importante es "custom_code".  Las otras sirven meramente de guía para evitar errores de nombres...
    os.mkdir(custom_code_dir)
    os.mkdir(filetools.join(custom_code_dir, 'channels'))
    os.mkdir(filetools.join(custom_code_dir, 'core'))
    os.mkdir(filetools.join(custom_code_dir, 'lib'))
    os.mkdir(filetools.join(custom_code_dir, 'platformcode'))
    os.mkdir(filetools.join(custom_code_dir, 'resources'))
    os.mkdir(filetools.join(custom_code_dir, 'servers'))

    return


def create_json(custom_code_json_path, json_name=json_data_file_name):
    logger.info()

    #Guardamaos el json con la versión de Alfa vacía, para permitir hacer la primera copia
    json_data_file = filetools.join(custom_code_json_path, json_name)
    json_file = open(json_data_file, "a+")
    json_file.write(json.dumps({"addon_version": ""}))
    json_file.close()
    
    return


def verify_copy_folders(custom_code_dir, custom_code_json_path):
    logger.info()
    
    #verificamos si es una nueva versión de Alfa instalada o era la existente.  Si es la existente, nos vamos sin hacer nada
    json_data_file = filetools.join(custom_code_json_path, json_data_file_name)
    json_data = jsontools.load(filetools.read(json_data_file))
    current_version = config.get_addon_version(with_fix=False)
    if current_version == json_data['addon_version']:
        return
    
    #Ahora copiamos los archivos desde el área de Userdata, Custom_code, sobre las carpetas del add-on
    for root, folders, files in os.walk(custom_code_dir):
        for file in files:
            input_file = filetools.join(root, file)
            output_file = input_file.replace(custom_code_dir, custom_code_json_path)
            if filetools.copy(input_file, output_file, silent=True) == False:
                return
    
    #Guardamaos el json con la versión actual de Alfa, para no volver a hacer la copia hasta la nueva versión
    json_data['addon_version'] = current_version
    filetools.write(json_data_file, jsontools.dump(json_data))

    return

    
def question_update_external_addon(addon_name):
    logger.info(addon_name)
    
    #Verificamos que el addon está instalado
    stat = False
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s")' % addon_name):
        #Si es la primera vez que se pregunta por la actualización del addon externo, recogemos la respuesta,  
        # guardaos un .json en userdat/alfa para no volver a preguntar otra vez, y se actualiza el setting en Alfa.
        stat = platformtools.dialog_yesno('Actualización de %s' % addon_name.capitalize(), '¿Quiere que actualicemos Quasar para que sea compatible con las últimas versiones de Kodi? (recomendado: SÍ)', '', 'Si actualiza Quasar, reinicie Kodi en un par de minutos')

        #Con la respuesta actualizamos la variable en Alfa settings.xml.  Se puede cambiar en Ajustes de Alfa, Otros
        if stat:
            config.set_setting('addon_quasar_update', True)
        else:
            config.set_setting('addon_quasar_update', False)
            
        #Creamos un .json en userdata para no volver a preguntar otra vez
        create_json(config.get_data_path(), "%s.json" % addon_name)
    
    return stat
    
def update_external_addon(addon_name):
    logger.info(addon_name)
    
    #Verificamos que el addon está instalado
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s")' % addon_name):
        #Path de actuali<aciones de Alfa
        alfa_addon_updates = filetools.join(config.get_runtime_path(), filetools.join("lib", addon_name))
        
        #Path de destino en addon externo
        __settings__ = xbmcaddon.Addon(id="plugin.video." + addon_name)
        if addon_name.lower() in ['quasar', 'elementum']:
            addon_path = filetools.join(xbmc.translatePath(__settings__.getAddonInfo('Path')), filetools.join("resources", filetools.join("site-packages", addon_name)))
        else:
            addon_path = ''
        
        #Hay modificaciones en Alfa? Las copiamos al addon
        if filetools.exists(alfa_addon_updates) and filetools.exists(addon_path):
            for root, folders, files in os.walk(alfa_addon_updates):
                for file in files:
                    input_file = filetools.join(root, file)
                    output_file = input_file.replace(alfa_addon_updates, addon_path)
                    if filetools.copy(input_file, output_file, silent=True) == False:
                        logger.error('Error en la copia: Input: %s o Output: %s' % (input_file, output_file))
                        return False
            return True
        else:
            logger.error('Alguna carpeta no existe: Alfa: %s o %s: %s' % (alfa_addon_updates, addon_name, addon_path))
    
    return False
    
    
def verify_Kodi_video_DB():
    logger.info()
    import random
    
    platform = {}
    path = ''
    db_files = []
    
    try:
        path = filetools.join(xbmc.translatePath("special://masterprofile/"), "Database")
        if filetools.exists(path):
            platform = config.get_platform(full_version=True)
            if platform:
                db_files = filetools.walk(path)
                if filetools.exists(filetools.join(path, platform['video_db'])):
                    for root, folders, files in db_files:
                        for file in files:
                            if file != platform['video_db']:
                                if file.startswith('MyVideos'):
                                    randnum = str(random.randrange(1, 999999))
                                    filetools.rename(filetools.join(path, file), 'OLD_' + randnum +'_' + file)
                                    logger.error('BD obsoleta: ' + file)
                    
                else:
                    logger.error('Video_DB: ' + str(platform['video_db']) + ' para versión Kodi ' + str(platform['num_version']) + ' NO EXISTE. Analizar carpeta: ' + str(db_files))
            else:
                logger.error('Estructura de get_platform(full_version=True) incorrecta')
        else:
            logger.error('Path a Userdata/Database (' + path + ') no encontrado')
        
    except:
        logger.error('Platform: ' + str(platform) + ' / Path: ' + str(path) + ' / Files: ' + str(db_files))
        logger.error(traceback.format_exc())
        
    return