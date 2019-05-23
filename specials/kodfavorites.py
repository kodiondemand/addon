# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Alfa favoritos
# ==============
# - Lista de enlaces guardados como favoritos, solamente en Alfa, no Kodi.
# - Los enlaces se organizan en carpetas (virtuales) que puede definir el usuario.
# - Se utiliza un sólo fichero para guardar todas las carpetas y enlaces: alfavorites-default.json
# - Se puede copiar alfavorites-default.json a otros dispositivos ya que la única dependencia local es el thumbnail asociado a los enlaces,
#   pero se detecta por código y se ajusta al dispositivo actual.
# - Se pueden tener distintos ficheros de alfavoritos y alternar entre ellos, pero solamente uno de ellos es la "lista activa".
# - Los ficheros deben estar en config.get_data_path() y empezar por alfavorites- y terminar en .json

# Requerimientos en otros módulos para ejecutar este canal:
# - Añadir un enlace a este canal en channelselector.py
# - Modificar platformtools.py para controlar el menú contextual y añadir "Guardar enlace" en set_context_commands
# ------------------------------------------------------------

import os, re
from datetime import datetime

from core.item import Item
from platformcode import config, logger, platformtools

from core import filetools, jsontools


def fechahora_actual():
    return datetime.now().strftime('%Y-%m-%d %H:%M')

# Helpers para listas
# -------------------

PREFIJO_LISTA = 'kodfavorites-'

# Devuelve el nombre de la lista activa (Ej: alfavorites-default.json)
def get_lista_activa():
    return config.get_setting('lista_activa', default = PREFIJO_LISTA + 'default.json')

# Extrae nombre de la lista del fichero, quitando prefijo y sufijo (Ej: alfavorites-Prueba.json => Prueba)
def get_name_from_filename(filename):
    return filename.replace(PREFIJO_LISTA, '').replace('.json', '')

# Componer el fichero de lista a partir de un nombre, añadiendo prefijo y sufijo (Ej: Prueba => alfavorites-Prueba.json)
def get_filename_from_name(name):
    return PREFIJO_LISTA + name + '.json'

# Apuntar en un fichero de log los códigos de los ficheros que se hayan compartido
def save_log_lista_shared(msg):
    msg = fechahora_actual() + ': ' + msg + os.linesep
    fullfilename = os.path.join(config.get_data_path(), 'alfavorites_shared.log')
    with open(fullfilename, 'a') as f: f.write(msg); f.close()

# Limpiar texto para usar como nombre de fichero
def text_clean(txt, disallowed_chars = '[^a-zA-Z0-9\-_()\[\]. ]+', blank_char = ' '):
    import unicodedata
    try:
        txt = unicode(txt, 'utf-8')
    except NameError: # unicode is a default on python 3 
        pass
    txt = unicodedata.normalize('NFKD', txt).encode('ascii', 'ignore')
    txt = txt.decode('utf-8').strip()
    if blank_char != ' ': txt = txt.replace(' ', blank_char)
    txt = re.sub(disallowed_chars, '', txt)
    return str(txt)



# Clase para cargar y guardar en el fichero de Alfavoritos
# --------------------------------------------------------
class AlfavoritesData:

    def __init__(self, filename = None):

        # Si no se especifica ningún fichero se usa la lista_activa (si no la hay se crea)
        if filename == None:
            filename = get_lista_activa()

        self.user_favorites_file = os.path.join(config.get_data_path(), filename)

        if not os.path.exists(self.user_favorites_file):
            fichero_anterior = os.path.join(config.get_data_path(), 'user_favorites.json')
            if os.path.exists(fichero_anterior): # formato anterior, convertir (a eliminar después de algunas versiones)
                jsondata = jsontools.load(filetools.read(fichero_anterior))
                self.user_favorites = jsondata
                self.info_lista = {}
                self.save()
                filetools.remove(fichero_anterior)
            else:
                self.user_favorites = []
        else:
            jsondata = jsontools.load(filetools.read(self.user_favorites_file))
            if not 'user_favorites' in jsondata or not 'info_lista' in jsondata: # formato incorrecto
                self.user_favorites = []
            else:
                self.user_favorites = jsondata['user_favorites']
                self.info_lista = jsondata['info_lista']


        if len(self.user_favorites) == 0:
            self.info_lista = {}
            
            # Crear algunas carpetas por defecto
            self.user_favorites.append({ 'title': config.get_localized_string(30122), 'items': [] })
            self.user_favorites.append({ 'title': config.get_localized_string(30123), 'items': [] })
            self.user_favorites.append({ 'title': config.get_localized_string(70149), 'items': [] })

            self.save()

    def save(self):
        if 'created' not in self.info_lista: 
            self.info_lista['created'] = fechahora_actual()
        self.info_lista['updated'] = fechahora_actual()

        jsondata = {}
        jsondata['user_favorites'] = self.user_favorites
        jsondata['info_lista'] = self.info_lista
        if not filetools.write(self.user_favorites_file, jsontools.dump(jsondata)):
            platformtools.dialog_ok('Alfa', config.get_localized_string(70614), os.path.basename(self.user_favorites_file))


# ============================
# Añadir desde menú contextual
# ============================

def addFavourite(item):
    logger.info()
    alfav = AlfavoritesData()

    # Si se llega aquí mediante el menú contextual, hay que recuperar los parámetros action y channel
    if item.from_action:
        item.__dict__['action'] = item.__dict__.pop('from_action')
    if item.from_channel:
        item.__dict__['channel'] = item.__dict__.pop('from_channel')

    # Limpiar título
    item.title = re.sub(r'\[COLOR [^\]]*\]', '', item.title.replace('[/COLOR]', '')).strip()
    if item.text_color:
        item.__dict__.pop('text_color')

    # Diálogo para escoger/crear carpeta
    i_perfil = _selecciona_perfil(alfav, config.get_localized_string(70546))
    if i_perfil == -1: return False

    # Detectar que el mismo enlace no exista ya en la carpeta
    campos = ['channel','action','url','extra','list_type'] # si todos estos campos coinciden se considera que el enlace ya existe
    for enlace in alfav.user_favorites[i_perfil]['items']:
        it = Item().fromurl(enlace)
        repe = True
        for prop in campos:
            if prop in it.__dict__ and prop in item.__dict__ and it.__dict__[prop] != item.__dict__[prop]:
                repe = False
                break
        if repe:
            platformtools.dialog_notification(config.get_localized_string(70615), config.get_localized_string(70616))
            return False

    # Si es una película/serie, completar información de tmdb si no se tiene activado tmdb_plus_info (para season/episodio no hace falta pq ya se habrá hecho la "segunda pasada")
    if (item.contentType == 'movie' or item.contentType == 'tvshow') and not config.get_setting('tmdb_plus_info', default=False):
        from core import tmdb
        tmdb.set_infoLabels(item, True) # obtener más datos en "segunda pasada" (actores, duración, ...)

    # Añadir fecha en que se guarda
    item.date_added = fechahora_actual()

    # Guardar
    alfav.user_favorites[i_perfil]['items'].append(item.tourl())
    alfav.save()

    platformtools.dialog_notification(config.get_localized_string(70531), config.get_localized_string(70532) % alfav.user_favorites[i_perfil]['title'])
    
    return True


# ====================
# NAVEGACIÓN
# ====================

def mainlist(item):
    logger.info()
    alfav = AlfavoritesData()
    item.category = get_name_from_filename(os.path.basename(alfav.user_favorites_file))

    itemlist = []
    last_i = len(alfav.user_favorites) - 1

    for i_perfil, perfil in enumerate(alfav.user_favorites):
        context = []

        context.append({'title': config.get_localized_string(70533), 'channel': item.channel, 'action': 'editar_perfil_titulo',
                        'i_perfil': i_perfil})
        context.append({'title': config.get_localized_string(70534), 'channel': item.channel, 'action': 'eliminar_perfil',
                        'i_perfil': i_perfil})

        if i_perfil > 0:
            context.append({'title': config.get_localized_string(70535), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'top'})
            context.append({'title': config.get_localized_string(70536), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'arriba'})
        if i_perfil < last_i:
            context.append({'title': config.get_localized_string(70537), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'abajo'})
            context.append({'title': config.get_localized_string(70538), 'channel': item.channel, 'action': 'mover_perfil',
                            'i_perfil': i_perfil, 'direccion': 'bottom'})

        plot = '%d enlaces en la carpeta' % len(perfil['items'])
        itemlist.append(Item(channel=item.channel, action='mostrar_perfil', title=perfil['title'], plot=plot, i_perfil=i_perfil, context=context))

    itemlist.append(item.clone(action='crear_perfil', title=config.get_localized_string(70542), folder=False))
    
    itemlist.append(item.clone(action='mainlist_listas', title=config.get_localized_string(70603)))

    return itemlist


def mostrar_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    itemlist = []

    i_perfil = item.i_perfil
    if not alfav.user_favorites[i_perfil]: return itemlist
    last_i = len(alfav.user_favorites[i_perfil]['items']) - 1

    ruta_runtime = config.get_runtime_path()

    for i_enlace, enlace in enumerate(alfav.user_favorites[i_perfil]['items']):

        it = Item().fromurl(enlace)
        it.context = [ {'title': '[COLOR blue]'+config.get_localized_string(70617)+'[/COLOR]', 'channel': item.channel, 'action': 'acciones_enlace',
                        'i_enlace': i_enlace, 'i_perfil': i_perfil} ]

        it.plot += '[CR][CR][COLOR blue]Canal:[/COLOR] ' + it.channel + ' [COLOR blue]Action:[/COLOR] ' + it.action
        if it.extra != '': it.plot += ' [COLOR blue]Extra:[/COLOR] ' + it.extra
        it.plot += '[CR][COLOR blue]Url:[/COLOR] ' + it.url if isinstance(it.url, str) else '...'
        if it.date_added != '': it.plot += '[CR][COLOR blue]Added:[/COLOR] ' + it.date_added

        # Si no es una url, ni tiene la ruta del sistema, convertir el path ya que se habrá copiado de otro dispositivo.
        # Sería más óptimo que la conversión se hiciera con un menú de importar, pero de momento se controla en run-time.
        if it.thumbnail and '://' not in it.thumbnail and not it.thumbnail.startswith(ruta_runtime):
            ruta, fichero = filetools.split(it.thumbnail)
            if ruta == '' and fichero == it.thumbnail: # en linux el split con un path de windows no separa correctamente
                ruta, fichero = filetools.split(it.thumbnail.replace('\\','/'))
            if 'channels' in ruta and 'thumb' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'channels', 'thumb', fichero)
            elif 'themes' in ruta and 'default' in ruta: 
                it.thumbnail = filetools.join(ruta_runtime, 'resources', 'media', 'themes', 'default', fichero)

        itemlist.append(it)

    return itemlist


# Rutinas internas compartidas
# ----------------------------

# Diálogo para seleccionar/crear una carpeta. Devuelve índice de la carpeta en user_favorites (-1 si cancel)
def _selecciona_perfil(alfav, titulo='Seleccionar carpeta', i_actual=-1):
    acciones = [(perfil['title'] if i_p != i_actual else '[I][COLOR pink]%s[/COLOR][/I]' % perfil['title']) for i_p, perfil in enumerate(alfav.user_favorites)]
    acciones.append('Crear nueva carpeta')

    i_perfil = -1
    while i_perfil == -1: # repetir hasta seleccionar una carpeta o cancelar
        ret = platformtools.dialog_select(titulo, acciones)
        if ret == -1: return -1 # pedido cancel
        if ret < len(alfav.user_favorites):
            i_perfil = ret
        else: # crear nueva carpeta
            if _crea_perfil(alfav):
                i_perfil = len(alfav.user_favorites) - 1

    return i_perfil


# Diálogo para crear una carpeta
def _crea_perfil(alfav):
    titulo = platformtools.dialog_input(default='', heading=config.get_localized_string(70551))
    if titulo is None or titulo == '':
        return False

    alfav.user_favorites.append({'title': titulo, 'items': []})
    alfav.save()

    return True


# Gestión de perfiles y enlaces
# -----------------------------

def crear_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    if not _crea_perfil(alfav): return False

    platformtools.itemlist_refresh()
    return True


def editar_perfil_titulo(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False

    titulo = platformtools.dialog_input(default=alfav.user_favorites[item.i_perfil]['title'], heading=config.get_localized_string(70533))
    if titulo is None or titulo == '' or titulo == alfav.user_favorites[item.i_perfil]['title']:
        return False

    alfav.user_favorites[item.i_perfil]['title'] = titulo
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False

    # Pedir confirmación
    if not platformtools.dialog_yesno(config.get_localized_string(70618), config.get_localized_string(70619)): return False

    del alfav.user_favorites[item.i_perfil]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def acciones_enlace(item):
    logger.info()

    acciones = [config.get_localized_string(70620), config.get_localized_string(70621), config.get_localized_string(70622), config.get_localized_string(70623),
                config.get_localized_string(70624), config.get_localized_string(70548), config.get_localized_string(70625),
                config.get_localized_string(70626), config.get_localized_string(70627), config.get_localized_string(70628)]

    ret = platformtools.dialog_select('Acción a ejecutar', acciones)
    if ret == -1: 
        return False # pedido cancel
    elif ret == 0:
        return editar_enlace_titulo(item)
    elif ret == 1:
        return editar_enlace_color(item)
    elif ret == 2:
        return editar_enlace_thumbnail(item)
    elif ret == 3:
        return editar_enlace_carpeta(item)
    elif ret == 4:
        return editar_enlace_lista(item)
    elif ret == 5:
        return eliminar_enlace(item)
    elif ret == 6:
        return mover_enlace(item.clone(direccion='top'))
    elif ret == 7:
        return mover_enlace(item.clone(direccion='arriba'))
    elif ret == 8:
        return mover_enlace(item.clone(direccion='abajo'))
    elif ret == 9:
        return mover_enlace(item.clone(direccion='bottom'))


def editar_enlace_titulo(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    titulo = platformtools.dialog_input(default=it.title, heading='Cambiar título del enlace')
    if titulo is None or titulo == '' or titulo == it.title:
        return False
    
    it.title = titulo

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_color(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    colores = ['green','yellow','red','blue','white','orange','lime','aqua','pink','violet','purple','tomato','olive','antiquewhite','gold']
    opciones = ['[COLOR %s]%s[/COLOR]' % (col, col) for col in colores]

    ret = platformtools.dialog_select('Seleccionar color:', opciones)

    if ret == -1: return False # pedido cancel
    it.text_color = colores[ret]

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_thumbnail(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    it = Item().fromurl(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    
    # A partir de Kodi 17 se puede usar xbmcgui.Dialog().select con thumbnails (ListItem & useDetails=True)
    is_kodi17 = (config.get_platform(True)['num_version'] >= 17.0)
    if is_kodi17:
        import xbmcgui

    # Diálogo para escoger thumbnail (el del canal o iconos predefinidos)
    opciones = []
    ids = []
    try:
        from core import channeltools
        channel_parameters = channeltools.get_channel_parameters(it.channel)
        if channel_parameters['thumbnail'] != '':
            nombre = 'Canal %s' % it.channel
            if is_kodi17:
                it_thumb = xbmcgui.ListItem(nombre)
                it_thumb.setArt({ 'thumb': channel_parameters['thumbnail'] })
                opciones.append(it_thumb)
            else:
                opciones.append(nombre)
            ids.append(channel_parameters['thumbnail'])
    except:
        pass
    
    resource_path = os.path.join(config.get_runtime_path(), 'resources', 'media', 'themes', 'default')
    for f in sorted(os.listdir(resource_path)):
        if f.startswith('thumb_') and not f.startswith('thumb_intervenido') and f != 'thumb_back.png':
            nombre = f.replace('thumb_', '').replace('_', ' ').replace('.png', '')
            if is_kodi17:
                it_thumb = xbmcgui.ListItem(nombre)
                it_thumb.setArt({ 'thumb': os.path.join(resource_path, f) })
                opciones.append(it_thumb)
            else:
                opciones.append(nombre)
            ids.append(os.path.join(resource_path, f))

    if is_kodi17:
        ret = xbmcgui.Dialog().select('Seleccionar thumbnail:', opciones, useDetails=True)
    else:
        ret = platformtools.dialog_select('Seleccionar thumbnail:', opciones)

    if ret == -1: return False # pedido cancel

    it.thumbnail = ids[ret]

    alfav.user_favorites[item.i_perfil]['items'][item.i_enlace] = it.tourl()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_carpeta(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    # Diálogo para escoger/crear carpeta
    i_perfil = _selecciona_perfil(alfav, 'Mover enlace a:', item.i_perfil)
    if i_perfil == -1 or i_perfil == item.i_perfil: return False

    alfav.user_favorites[i_perfil]['items'].append(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    del alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def editar_enlace_lista(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    # Diálogo para escoger lista
    opciones = []
    itemlist_listas = mainlist_listas(item)
    for it in itemlist_listas:
        if it.lista != '' and '[<---]' not in it.title: # descarta item crear y lista activa
            opciones.append(it.lista)

    if len(opciones) == 0:
        platformtools.dialog_ok('Alfa', 'No hay otras listas dónde mover el enlace.', 'Puedes crearlas desde el menú Gestionar listas de enlaces')
        return False

    ret = platformtools.dialog_select('Seleccionar lista destino', opciones)

    if ret == -1: 
        return False # pedido cancel

    alfav_destino = AlfavoritesData(opciones[ret])

    # Diálogo para escoger/crear carpeta en la lista de destino
    i_perfil = _selecciona_perfil(alfav_destino, 'Seleccionar carpeta destino', -1)
    if i_perfil == -1: return False

    alfav_destino.user_favorites[i_perfil]['items'].append(alfav.user_favorites[item.i_perfil]['items'][item.i_enlace])
    del alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]
    alfav_destino.save()
    alfav.save()

    platformtools.itemlist_refresh()
    return True


def eliminar_enlace(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    if not alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]: return False

    del alfav.user_favorites[item.i_perfil]['items'][item.i_enlace]
    alfav.save()

    platformtools.itemlist_refresh()
    return True


# Mover perfiles y enlaces (arriba, abajo, top, bottom)
# ------------------------
def mover_perfil(item):
    logger.info()
    alfav = AlfavoritesData()

    alfav.user_favorites = _mover_item(alfav.user_favorites, item.i_perfil, item.direccion)
    alfav.save()

    platformtools.itemlist_refresh()
    return True

def mover_enlace(item):
    logger.info()
    alfav = AlfavoritesData()

    if not alfav.user_favorites[item.i_perfil]: return False
    alfav.user_favorites[item.i_perfil]['items'] = _mover_item(alfav.user_favorites[item.i_perfil]['items'], item.i_enlace, item.direccion)
    alfav.save()

    platformtools.itemlist_refresh()
    return True


# Mueve un item determinado (numérico) de una lista (arriba, abajo, top, bottom) y devuelve la lista modificada
def _mover_item(lista, i_selected, direccion):
    last_i = len(lista) - 1
    if i_selected > last_i or i_selected < 0: return lista # índice inexistente en lista

    if direccion == 'arriba':
        if i_selected == 0: # Ya está arriba de todo
            return lista
        lista.insert(i_selected - 1, lista.pop(i_selected))

    elif direccion == 'abajo':
        if i_selected == last_i: # Ya está abajo de todo
            return lista
        lista.insert(i_selected + 1, lista.pop(i_selected))

    elif direccion == 'top':
        if i_selected == 0: # Ya está arriba de todo
            return lista
        lista.insert(0, lista.pop(i_selected))

    elif direccion == 'bottom':
        if i_selected == last_i: # Ya está abajo de todo
            return lista
        lista.insert(last_i, lista.pop(i_selected))

    return lista


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Gestionar diferentes listas de alfavoritos
# ------------------------------------------

def mainlist_listas(item):
    logger.info()
    itemlist = []
    item.category = 'Listas'

    lista_activa = get_lista_activa()
    
    import glob

    path = os.path.join(config.get_data_path(), PREFIJO_LISTA+'*.json')
    for fichero in glob.glob(path):
        lista = os.path.basename(fichero)
        nombre = get_name_from_filename(lista)
        titulo = nombre if lista != lista_activa else '[COLOR gold]%s[/COLOR] [<---]' % nombre
        
        itemlist.append(item.clone(action='acciones_lista', lista=lista, title=titulo, folder=False))

    itemlist.append(item.clone(action='acciones_nueva_lista', title=config.get_localized_string(70642), folder=False))
    
    return itemlist


def acciones_lista(item):
    logger.info()

    acciones = [config.get_localized_string(70604), config.get_localized_string(70629),
                config.get_localized_string(70605), config.get_localized_string(70606), config.get_localized_string(70607)]

    ret = platformtools.dialog_select(item.lista, acciones)

    if ret == -1: 
        return False # pedido cancel
    elif ret == 0:
        return activar_lista(item)
    elif ret == 1:
        return renombrar_lista(item)
    elif ret == 2:
        return compartir_lista(item)
    elif ret == 3:
        return eliminar_lista(item)
    elif ret == 4:
        return informacion_lista(item)


def activar_lista(item):
    logger.info()

    fullfilename = os.path.join(config.get_data_path(), item.lista)
    if not os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70630), item.lista)
        return False

    config.set_setting('lista_activa', item.lista)

    from channelselector import get_thumb
    item_inicio = Item(title=config.get_localized_string(70527), channel="alfavorites", action="mainlist",
                       thumbnail=get_thumb("mylink.png"),
                       category=config.get_localized_string(70527), viewmode="thumbnails")
    platformtools.itemlist_update(item_inicio, replace=True)
    return True


def renombrar_lista(item):
    logger.info()

    fullfilename_current = os.path.join(config.get_data_path(), item.lista)
    if not os.path.exists(fullfilename_current):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70630), fullfilename_current)
        return False
    
    nombre = get_name_from_filename(item.lista)
    titulo = platformtools.dialog_input(default=nombre, heading=config.get_localized_string(70612))
    if titulo is None or titulo == '' or titulo == nombre:
        return False
    titulo = text_clean(titulo, blank_char='_')

    filename = get_filename_from_name(titulo)
    fullfilename = os.path.join(config.get_data_path(), filename)

    # Comprobar que el nuevo nombre no exista
    if os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70613), fullfilename)
        return False

    # Rename del fichero
    if not filetools.rename(fullfilename_current, filename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70631), fullfilename)
        return False

    # Update settings si es la lista activa
    if item.lista == get_lista_activa():
        config.set_setting('lista_activa', filename)


    platformtools.itemlist_refresh()
    return True


def eliminar_lista(item):
    logger.info()

    fullfilename = os.path.join(config.get_data_path(), item.lista)
    if not os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70630), item.lista)
        return False

    if item.lista == get_lista_activa():
        platformtools.dialog_ok('Alfa', config.get_localized_string(70632), item.lista)
        return False

    if not platformtools.dialog_yesno(config.get_localized_string(70606), config.get_localized_string(70633) + ' %s ?' % item.lista): return False
    filetools.remove(fullfilename)

    platformtools.itemlist_refresh()
    return True


def informacion_lista(item):
    logger.info()
    
    fullfilename = os.path.join(config.get_data_path(), item.lista)
    if not os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70630), item.lista)
        return False

    alfav = AlfavoritesData(item.lista)
    
    txt = 'Lista: [COLOR gold]%s[/COLOR]' % item.lista
    txt += '[CR]' + config.get_localized_string(70634) + ' ' + alfav.info_lista['created'] + ' ' + config.get_localized_string(70635) + ' ' + alfav.info_lista['updated']

    if 'downloaded_date' in alfav.info_lista:
        txt += '[CR]' + config.get_localized_string(70636) + ' ' + alfav.info_lista['downloaded_date'] + ' ' + alfav.info_lista['downloaded_from'] + ' ' + config.get_localized_string(70637)

    if 'tinyupload_date' in alfav.info_lista:
        txt += '[CR]' + config.get_localized_string(70638) + ' ' + alfav.info_lista['tinyupload_date'] + ' ' + config.get_localized_string(70639) + ' [COLOR blue]' + alfav.info_lista['tinyupload_code'] + '[/COLOR]'
    
    txt += '[CR]' + config.get_localized_string(70640) + ' ' + len(alfav.user_favorites)
    for perfil in alfav.user_favorites:
        txt += '[CR]- %s (%d %s)' % (perfil['title'], len(perfil['items']), config.get_localized_string(70641))

    platformtools.dialog_textviewer(config.get_localized_string(70607), txt)
    return True


def compartir_lista(item):
    logger.info()

    fullfilename = os.path.join(config.get_data_path(), item.lista)
    if not os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70630), fullfilename)
        return False

    try:
        progreso = platformtools.dialog_progress_bg(config.get_localized_string(70643), config.get_localized_string(70644))
        
        # Acceso a la página principal de tinyupload para obtener datos necesarios
        from core import httptools, scrapertools
        data = httptools.downloadpage('http://s000.tinyupload.com/index.php').data
        upload_url = scrapertools.find_single_match(data, 'form action="([^"]+)')
        sessionid = scrapertools.find_single_match(upload_url, 'sid=(.+)')
        
        progreso.update(10, config.get_localized_string(70645), config.get_localized_string(70646))

        # Envío del fichero a tinyupload mediante multipart/form-data 
        from lib import MultipartPostHandler
        import urllib2
        opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
        params = { 'MAX_FILE_SIZE' : '52428800', 'file_description' : '', 'sessionid' : sessionid, 'uploaded_file' : open(fullfilename, 'rb') }
        handle = opener.open(upload_url, params)
        data = handle.read()
        
        progreso.close()

        if not 'File was uploaded successfuly' in data:
            logger.debug(data)
            platformtools.dialog_ok('Alfa', config.get_localized_string(70647))
            return False

        codigo = scrapertools.find_single_match(data, 'href="index\.php\?file_id=([^"]+)')

    except:
        platformtools.dialog_ok('Alfa', config.get_localized_string(70647), item.lista)
        return False

    # Apuntar código en fichero de log y dentro de la lista
    save_log_lista_shared(config.get_localized_string(70648) + ' ' + item.lista + ' ' + codigo + ' ' + config.get_localized_string(70649))
    
    alfav = AlfavoritesData(item.lista)
    alfav.info_lista['tinyupload_date'] = fechahora_actual()
    alfav.info_lista['tinyupload_code'] = codigo
    alfav.save()

    platformtools.dialog_ok('Alfa', config.get_localized_string(70650), codigo)
    return True
        


def acciones_nueva_lista(item):
    logger.info()

    acciones = [config.get_localized_string(70651),
                config.get_localized_string(70652),
                config.get_localized_string(70653),
                config.get_localized_string(70654)]

    ret = platformtools.dialog_select(config.get_localized_string(70608), acciones)

    if ret == -1: 
        return False # pedido cancel

    elif ret == 0:
        return crear_lista(item)

    elif ret == 1:
        codigo = platformtools.dialog_input(default='', heading=config.get_localized_string(70609)) # 05370382084539519168
        if codigo is None or codigo == '':
            return False
        return descargar_lista(item, 'http://s000.tinyupload.com/?file_id=' + codigo)

    elif ret == 2:
        url = platformtools.dialog_input(default='https://', heading=config.get_localized_string(70610))
        if url is None or url == '':
            return False
        return descargar_lista(item, url)

    elif ret == 3:
        txt = config.get_localized_string(70611)
        platformtools.dialog_textviewer(config.get_localized_string(70607), txt)
        return False


def crear_lista(item):
    logger.info()

    titulo = platformtools.dialog_input(default='', heading=config.get_localized_string(70612))
    if titulo is None or titulo == '':
        return False
    titulo = text_clean(titulo, blank_char='_')

    filename = get_filename_from_name(titulo)
    fullfilename = os.path.join(config.get_data_path(), filename)

    # Comprobar que el fichero no exista ya
    if os.path.exists(fullfilename):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70613), fullfilename)
        return False

    # Provocar que se guarde con las carpetas vacías por defecto
    alfav = AlfavoritesData(filename)

    platformtools.itemlist_refresh()
    return True


def descargar_lista(item, url):
    logger.info()
    from core import httptools, scrapertools
    
    if 'tinyupload.com/' in url:
        try:
            from urlparse import urlparse
            data = httptools.downloadpage(url).data
            logger.debug(data)
            down_url, url_name = scrapertools.find_single_match(data, ' href="(download\.php[^"]*)"><b>([^<]*)')
            url_json = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url)) + down_url
        except:
            platformtools.dialog_ok('Alfa', config.get_localized_string(70655), url)
            return False

    elif 'zippyshare.com/' in url:
        from core import servertools
        video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing('zippyshare', url)
        
        if not puedes:
            platformtools.dialog_ok('Alfa', config.get_localized_string(70655), motivo)
            return False
        url_json = video_urls[0][1] # https://www58.zippyshare.com/d/qPzzQ0UM/25460/alfavorites-testeanding.json
        url_name = url_json[url_json.rfind('/')+1:]

    elif 'friendpaste.com/' in url:
        url_json = url if url.endswith('/raw') else url + '/raw'
        url_name = 'friendpaste'

    else:
        url_json = url
        url_name = url[url.rfind('/')+1:]


    # Download json
    data = httptools.downloadpage(url_json).data
    
    # Verificar formato json de alfavorites y añadir info de la descarga
    jsondata = jsontools.load(data)
    if 'user_favorites' not in jsondata or 'info_lista' not in jsondata:
        logger.debug(data)
        platformtools.dialog_ok('Alfa', config.get_localized_string(70656))
        return False

    jsondata['info_lista']['downloaded_date'] = fechahora_actual()
    jsondata['info_lista']['downloaded_from'] = url
    data = jsontools.dump(jsondata)

    # Pedir nombre para la lista descargada
    nombre = get_name_from_filename(url_name)
    titulo = platformtools.dialog_input(default=nombre, heading=config.get_localized_string(70657))
    if titulo is None or titulo == '':
        return False
    titulo = text_clean(titulo, blank_char='_')

    filename = get_filename_from_name(titulo)
    fullfilename = os.path.join(config.get_data_path(), filename)

    # Si el nuevo nombre ya existe pedir confirmación para sobrescribir
    if os.path.exists(fullfilename):
        if not platformtools.dialog_yesno('Alfa', config.get_localized_string(70613), config.get_localized_string(70658), filename):
            return False
    
    if not filetools.write(fullfilename, data):
        platformtools.dialog_ok('Alfa', config.get_localized_string(70659), filename)

    platformtools.dialog_ok('Alfa', config.get_localized_string(70660), filename)
    platformtools.itemlist_refresh()
    return True
