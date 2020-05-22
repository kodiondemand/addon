# -*- coding: utf-8 -*-

#from future import standard_library
#standard_library.install_aliases()
#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

from future.builtins import range
from future.builtins import object

import ast

import copy
import re
import sqlite3
import time

import xbmcaddon

from core import filetools
from core import httptools
from core import jsontools
from core import scrapertools
from core.item import InfoLabels
from platformcode import config
from platformcode import logger

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]

# -----------------------------------------------------------------------------------------------------------
# Conjunto de funciones relacionadas con las infoLabels.
#   version 1.0:
#       Version inicial
#
#   Incluyen:
#       set_infoLabels(source, seekTmdb, idioma_busqueda): Obtiene y fija (item.infoLabels) los datos extras de una o
# varias series, capitulos o peliculas.
#       set_infoLabels_item(item, seekTmdb, idioma_busqueda): Obtiene y fija (item.infoLabels) los datos extras de una
# serie, capitulo o pelicula.
#       set_infoLabels_itemlist(item_list, seekTmdb, idioma_busqueda): Obtiene y fija (item.infoLabels) los datos
# extras de una lista de series, capitulos o peliculas.
#       infoLabels_tostring(item): Retorna un str con la lista ordenada con los infoLabels del item
#
#   Uso:
#       tmdb.set_infoLabels(item, seekTmdb = True)
#
#       Obtener datos basicos de una pelicula:
#           Antes de llamar al metodo set_infoLabels el titulo a buscar debe estar en item.contentTitle
#           y el año en item.infoLabels['year'].
#
#       Obtener datos basicos de una serie:
#           Antes de llamar al metodo set_infoLabels el titulo a buscar debe estar en item.show o en
# item.contentSerieName.
#
#       Obtener mas datos de una pelicula o serie:
#           Despues de obtener los datos basicos en item.infoLabels['tmdb'] tendremos el codigo de la serie o pelicula.
#           Tambien podriamos directamente fijar este codigo, si se conoce, o utilizar los codigo correspondientes de:
#           IMDB (en item.infoLabels['IMDBNumber'] o item.infoLabels['code'] o item.infoLabels['imdb_id']), TVDB
# (solo series, en item.infoLabels['tvdb_id']),
#           Freebase (solo series, en item.infoLabels['freebase_mid']),TVRage (solo series, en
# item.infoLabels['tvrage_id'])
#
#       Obtener datos de una temporada:
#           Antes de llamar al metodo set_infoLabels el titulo de la serie debe estar en item.show o en
# item.contentSerieName,
#           el codigo TMDB de la serie debe estar en item.infoLabels['tmdb'] (puede fijarse automaticamente mediante
# la consulta de datos basica)
#           y el numero de temporada debe estar en item.infoLabels['season'].
#
#       Obtener datos de un episodio:
#           Antes de llamar al metodo set_infoLabels el titulo de la serie debe estar en item.show o en
# item.contentSerieName,
#           el codigo TMDB de la serie debe estar en item.infoLabels['tmdb'] (puede fijarse automaticamente mediante la
# consulta de datos basica),
#           el numero de temporada debe estar en item.infoLabels['season'] y el numero de episodio debe estar en
# item.infoLabels['episode'].
#
#
# --------------------------------------------------------------------------------------------------------------

otmdb_global = None
fname = filetools.join(config.get_data_path(), "kod_db.sqlite")

def create_bd():
    conn = sqlite3.connect(fname)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS tmdb_cache (url TEXT PRIMARY KEY, response TEXT, added TEXT)')
    conn.commit()
    conn.close()


def drop_bd():
    conn = sqlite3.connect(fname)
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS tmdb_cache')
    conn.commit()
    conn.close()

    return True


create_bd()


# El nombre de la funcion es el nombre del decorador y recibe la funcion que decora.
def cache_response(fn):
    logger.info()

    # import time
    # start_time = time.time()

    def wrapper(*args):
        import base64

        def check_expired(ts):
            import datetime

            valided = False

            cache_expire = config.get_setting("tmdb_cache_expire", default=0)

            saved_date = datetime.datetime.fromtimestamp(ts)
            current_date = datetime.datetime.fromtimestamp(time.time())
            elapsed = current_date - saved_date

            # 1 day
            if cache_expire == 0:
                if elapsed > datetime.timedelta(days=1):
                    valided = False
                else:
                    valided = True
            # 7 days
            elif cache_expire == 1:
                if elapsed > datetime.timedelta(days=7):
                    valided = False
                else:
                    valided = True

            # 15 days
            elif cache_expire == 2:
                if elapsed > datetime.timedelta(days=15):
                    valided = False
                else:
                    valided = True

            # 1 month - 30 days
            elif cache_expire == 3:
                # no tenemos en cuenta febrero o meses con 31 días
                if elapsed > datetime.timedelta(days=30):
                    valided = False
                else:
                    valided = True
            # no expire
            elif cache_expire == 4:
                valided = True

            return valided

        result = {}
        try:

            # no está activa la cache
            if not config.get_setting("tmdb_cache", default=False):
                result = fn(*args)
            else:

                conn = sqlite3.connect(fname, timeout=15)
                c = conn.cursor()
                url = re.sub('&year=-', '', args[0])
                if PY3: url = str.encode(url)
                url_base64 = base64.b64encode(url)
                c.execute("SELECT response, added FROM tmdb_cache WHERE url=?", (url_base64,))
                row = c.fetchone()

                if row and check_expired(float(row[1])):
                    result = eval(base64.b64decode(row[0]))

                # si no se ha obtenido información, llamamos a la funcion
                if not result:
                    result = fn(*args)
                    result = str(result)
                    if PY3: result = str.encode(result)
                    result_base64 = base64.b64encode(result)
                    c.execute("INSERT OR REPLACE INTO tmdb_cache (url, response, added) VALUES (?, ?, ?)",
                              (url_base64, result_base64, time.time()))

                    conn.commit()

                conn.close()

            # elapsed_time = time.time() - start_time
            # logger.debug("TARDADO %s" % elapsed_time)

        # error al obtener los datos
        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error in: %s" % message)

        return result

    return wrapper


def set_infoLabels(source, seekTmdb=True, idioma_busqueda=def_lang, forced=False):
    """
    Dependiendo del tipo de dato de source obtiene y fija (item.infoLabels) los datos extras de una o varias series,
    capitulos o peliculas.

    @param source: variable que contiene la información para establecer infoLabels
    @type source: list, item
    @param seekTmdb: si es True hace una busqueda en www.themoviedb.org para obtener los datos, en caso contrario
        obtiene los datos del propio Item.
    @type seekTmdb: bool
    @param idioma_busqueda: fija el valor de idioma en caso de busqueda en www.themoviedb.org
    @type idioma_busqueda: str
    @return: un numero o lista de numeros con el resultado de las llamadas a set_infoLabels_item
    @rtype: int, list
    """

    if not config.get_setting('tmdb_active') and not forced:
        return

    start_time = time.time()
    if type(source) == list:
        ret = set_infoLabels_itemlist(source, seekTmdb, idioma_busqueda)
        logger.debug("The data of %i links were obtained in %f seconds" % (len(source), time.time() - start_time))
    else:
        ret = set_infoLabels_item(source, seekTmdb, idioma_busqueda)
        logger.debug("The data were obtained in %f seconds" % (time.time() - start_time))
    return ret


def set_infoLabels_itemlist(item_list, seekTmdb=False, idioma_busqueda=def_lang, forced=False):
    """
    De manera concurrente, obtiene los datos de los items incluidos en la lista item_list.

    La API tiene un limite de 40 peticiones por IP cada 10'' y por eso la lista no deberia tener mas de 30 items
    para asegurar un buen funcionamiento de esta funcion.

    @param item_list: listado de objetos Item que representan peliculas, series o capitulos. El atributo
        infoLabels de cada objeto Item sera modificado incluyendo los datos extras localizados.
    @type item_list: list
    @param seekTmdb: Si es True hace una busqueda en www.themoviedb.org para obtener los datos, en caso contrario
        obtiene los datos del propio Item si existen.
    @type seekTmdb: bool
    @param idioma_busqueda: Codigo del idioma segun ISO 639-1, en caso de busqueda en www.themoviedb.org.
    @type idioma_busqueda: str

    @return: Una lista de numeros cuyo valor absoluto representa la cantidad de elementos incluidos en el atributo
        infoLabels de cada Item. Este numero sera positivo si los datos se han obtenido de www.themoviedb.org y
        negativo en caso contrario.
    @rtype: list
    """

    if not config.get_setting('tmdb_active') and not forced:
        return
    import threading

    threads_num = config.get_setting("tmdb_threads", default=20)
    semaforo = threading.Semaphore(threads_num)
    lock = threading.Lock()
    r_list = list()
    i = 0
    l_hilo = list()

    def sub_thread(_item, _i, _seekTmdb):
        semaforo.acquire()
        ret = set_infoLabels_item(_item, _seekTmdb, idioma_busqueda, lock)
        # logger.debug(str(ret) + "item: " + _item.tostring())
        semaforo.release()
        r_list.append((_i, _item, ret))

    for item in item_list:
        t = threading.Thread(target=sub_thread, args=(item, i, seekTmdb))
        t.start()
        i += 1
        l_hilo.append(t)

    # esperar q todos los hilos terminen
    for x in l_hilo:
        x.join()

    # Ordenar lista de resultados por orden de llamada para mantener el mismo orden q item_list
    r_list.sort(key=lambda i: i[0])

    # Reconstruir y devolver la lista solo con los resultados de las llamadas individuales
    return [ii[2] for ii in r_list]


def set_infoLabels_item(item, seekTmdb=True, idioma_busqueda=def_lang, lock=None):
    """
    Obtiene y fija (item.infoLabels) los datos extras de una serie, capitulo o pelicula.

    @param item: Objeto Item que representa un pelicula, serie o capitulo. El atributo infoLabels sera modificado
        incluyendo los datos extras localizados.
    @type item: Item
    @param seekTmdb: Si es True hace una busqueda en www.themoviedb.org para obtener los datos, en caso contrario
        obtiene los datos del propio Item si existen.
    @type seekTmdb: bool
    @param idioma_busqueda: Codigo del idioma segun ISO 639-1, en caso de busqueda en www.themoviedb.org.
    @type idioma_busqueda: str
    @param lock: para uso de threads cuando es llamado del metodo 'set_infoLabels_itemlist'
    @return: Un numero cuyo valor absoluto representa la cantidad de elementos incluidos en el atributo item.infoLabels.
        Este numero sera positivo si los datos se han obtenido de www.themoviedb.org y negativo en caso contrario.
    @rtype: int
    """
    global otmdb_global

    def __leer_datos(otmdb_aux):
        item.infoLabels = otmdb_aux.get_infoLabels(item.infoLabels)
        if item.infoLabels['thumbnail']:
            item.thumbnail = item.infoLabels['thumbnail']
        if item.infoLabels['fanart']:
            item.fanart = item.infoLabels['fanart']

    if seekTmdb:
        # Comprobamos q tipo de contenido es...
        if item.contentType == 'movie':
            tipo_busqueda = 'movie'
        else:
            tipo_busqueda = 'tv'

        if item.infoLabels['season']:
            try:
                numtemporada = int(item.infoLabels['season'])
            except ValueError:
                logger.debug("The season number is not valid.")
                return -1 * len(item.infoLabels)

            if lock:
                lock.acquire()

            if not otmdb_global or (item.infoLabels['tmdb_id']
                                    and str(otmdb_global.result.get("id")) != item.infoLabels['tmdb_id']) \
                    or (otmdb_global.texto_buscado and otmdb_global.texto_buscado != item.infoLabels['tvshowtitle']):
                if item.infoLabels['tmdb_id']:
                    otmdb_global = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda,
                                        idioma_busqueda=idioma_busqueda)
                else:
                    otmdb_global = Tmdb(texto_buscado=item.infoLabels['tvshowtitle'], tipo=tipo_busqueda,
                                        idioma_busqueda=idioma_busqueda, year=item.infoLabels['year'])

                __leer_datos(otmdb_global)

            # 4l3x87 - fix for overlap infoLabels if there is episode or season
            # if lock and lock.locked():
            #     lock.release()

            if item.infoLabels['episode']:
                try:
                    episode = int(item.infoLabels['episode'])
                except ValueError:
                    logger.debug("The episode number (%s) is not valid" % repr(item.infoLabels['episode']))
                    return -1 * len(item.infoLabels)

                # Tenemos numero de temporada y numero de episodio validos...
                # ... buscar datos episodio
                item.infoLabels['mediatype'] = 'episode'
                episodio = otmdb_global.get_episodio(numtemporada, episode)

                if episodio:
                    # Actualizar datos
                    __leer_datos(otmdb_global)
                    item.infoLabels['title'] = episodio['episodio_titulo']
                    if episodio['episodio_sinopsis']:
                        item.infoLabels['plot'] = episodio['episodio_sinopsis']
                    if episodio['episodio_imagen']:
                        item.infoLabels['poster_path'] = episodio['episodio_imagen']
                        item.thumbnail = item.infoLabels['poster_path']
                    if episodio['episodio_air_date']:
                        item.infoLabels['aired'] = episodio['episodio_air_date']
                    if episodio['episodio_vote_average']:
                        item.infoLabels['rating'] = episodio['episodio_vote_average']
                        item.infoLabels['votes'] = episodio['episodio_vote_count']

                    # 4l3x87 - fix for overlap infoLabels if there is episode or season
                    if lock and lock.locked():
                        lock.release()

                    return len(item.infoLabels)

            else:
                # Tenemos numero de temporada valido pero no numero de episodio...
                # ... buscar datos temporada
                item.infoLabels['mediatype'] = 'season'
                temporada = otmdb_global.get_temporada(numtemporada)
                if not isinstance(temporada, dict):
                    temporada = ast.literal_eval(temporada.decode('utf-8'))

                if temporada:
                    # Actualizar datos
                    __leer_datos(otmdb_global)
                    item.infoLabels['title'] = temporada['name'] if 'name' in temporada else ''
                    if 'overview' in  temporada and temporada['overview']:
                        item.infoLabels['plot'] = temporada['overview']
                    if 'air_date' in temporada and temporada['air_date']:
                        date = temporada['air_date'].split('-')
                        item.infoLabels['aired'] = date[2] + "/" + date[1] + "/" + date[0]
                    if 'poster_path' in temporada and temporada['poster_path']:
                        item.infoLabels['poster_path'] = 'http://image.tmdb.org/t/p/original' + temporada['poster_path']
                        item.thumbnail = item.infoLabels['poster_path']

                    # 4l3x87 - fix for overlap infoLabels if there is episode or season
                    if lock and lock.locked():
                        lock.release()

                    return len(item.infoLabels)

            # 4l3x87 - fix for overlap infoLabels if there is episode or season
            if lock and lock.locked():
                lock.release()

        # Buscar...
        else:
            otmdb = copy.copy(otmdb_global)
            # Busquedas por ID...
            if item.infoLabels['tmdb_id']:
                # ...Busqueda por tmdb_id
                otmdb = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda,
                             idioma_busqueda=idioma_busqueda)

            elif item.infoLabels['imdb_id']:
                # ...Busqueda por imdb code
                otmdb = Tmdb(external_id=item.infoLabels['imdb_id'], external_source="imdb_id",
                             tipo=tipo_busqueda,
                             idioma_busqueda=idioma_busqueda)

            elif tipo_busqueda == 'tv':  # buscar con otros codigos
                if item.infoLabels['tvdb_id']:
                    # ...Busqueda por tvdb_id
                    otmdb = Tmdb(external_id=item.infoLabels['tvdb_id'], external_source="tvdb_id", tipo=tipo_busqueda,
                                 idioma_busqueda=idioma_busqueda)
                elif item.infoLabels['freebase_mid']:
                    # ...Busqueda por freebase_mid
                    otmdb = Tmdb(external_id=item.infoLabels['freebase_mid'], external_source="freebase_mid",
                                 tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)
                elif item.infoLabels['freebase_id']:
                    # ...Busqueda por freebase_id
                    otmdb = Tmdb(external_id=item.infoLabels['freebase_id'], external_source="freebase_id",
                                 tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)
                elif item.infoLabels['tvrage_id']:
                    # ...Busqueda por tvrage_id
                    otmdb = Tmdb(external_id=item.infoLabels['tvrage_id'], external_source="tvrage_id",
                                 tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)

            #if otmdb is None:
            if not item.infoLabels['tmdb_id'] and not item.infoLabels['imdb_id'] and not item.infoLabels['tvdb_id'] and not item.infoLabels['freebase_mid'] and not item.infoLabels['freebase_id'] and not item.infoLabels['tvrage_id']:
                # No se ha podido buscar por ID...
                # hacerlo por titulo
                if tipo_busqueda == 'tv':
                    # Busqueda de serie por titulo y filtrando sus resultados si es necesario
                    otmdb = Tmdb(texto_buscado=item.infoLabels['tvshowtitle'], tipo=tipo_busqueda,
                                 idioma_busqueda=idioma_busqueda, filtro=item.infoLabels.get('filtro', {}),
                                 year=item.infoLabels['year'])
                else:
                    # Busqueda de pelicula por titulo...
                    # if item.infoLabels['year'] or item.infoLabels['filtro']:
                    # ...y año o filtro
                    searched_title = item.contentTitle if item.contentTitle else item.fulltitle
                    otmdb = Tmdb(texto_buscado=searched_title, tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda,
                                    filtro=item.infoLabels.get('filtro', {}), year=item.infoLabels['year'])
                if otmdb is not None:
                    if otmdb.get_id() and config.get_setting("tmdb_plus_info", default=False):
                        # Si la busqueda ha dado resultado y no se esta buscando una lista de items,
                        # realizar otra busqueda para ampliar la informacion
                        otmdb = Tmdb(id_Tmdb=otmdb.result.get("id"), tipo=tipo_busqueda, idioma_busqueda=idioma_busqueda)

            if lock and lock.locked():
                lock.release()

            if otmdb is not None and otmdb.get_id():
                # La busqueda ha encontrado un resultado valido
                __leer_datos(otmdb)
                return len(item.infoLabels)
    # La busqueda en tmdb esta desactivada o no ha dado resultado
    # item.contentType = item.infoLabels['mediatype']
    return -1 * len(item.infoLabels)


def find_and_set_infoLabels(item):
    logger.info()

    global otmdb_global
    tmdb_result = None

    if item.contentType == "movie":
        tipo_busqueda = "movie"
        tipo_contenido = config.get_localized_string(60247)
        title = item.contentTitle
    else:
        tipo_busqueda = "tv"
        tipo_contenido = config.get_localized_string(60298)
        title = item.contentSerieName

    # Si el titulo incluye el (año) se lo quitamos
    year = scrapertools.find_single_match(title, "^.+?\s*(\(\d{4}\))$")
    if year:
        title = title.replace(year, "").strip()
        item.infoLabels['year'] = year[1:-1]

    if not item.infoLabels.get("tmdb_id") or not item.infoLabels.get("tmdb_id")[0].isdigit():
        if not item.infoLabels.get("imdb_id"):
            otmdb_global = Tmdb(texto_buscado=title, tipo=tipo_busqueda, year=item.infoLabels['year'])
        else:
            otmdb_global = Tmdb(external_id=item.infoLabels.get("imdb_id"), external_source="imdb_id",
                                tipo=tipo_busqueda)
    elif not otmdb_global or str(otmdb_global.result.get("id")) != item.infoLabels['tmdb_id']:
        otmdb_global = Tmdb(id_Tmdb=item.infoLabels['tmdb_id'], tipo=tipo_busqueda, idioma_busqueda=def_lang)

    results = otmdb_global.get_list_resultados()

    if len(results) > 1:
        from platformcode import platformtools
        tmdb_result = platformtools.show_video_info(results, item=item,
                                                    caption= tipo_contenido % title)
    elif len(results) > 0:
        tmdb_result = results[0]

    if isinstance(item.infoLabels, InfoLabels):
        infoLabels = item.infoLabels
    else:
        infoLabels = InfoLabels()

    if tmdb_result:
        infoLabels['tmdb_id'] = tmdb_result['id']
        # todo mirar si se puede eliminar y obtener solo desde get_nfo()
        infoLabels['url_scraper'] = ["https://www.themoviedb.org/%s/%s" % (tipo_busqueda, infoLabels['tmdb_id'])]
        if infoLabels['tvdb_id']:
            infoLabels['url_scraper'].append("http://thetvdb.com/index.php?tab=series&id=%s" % infoLabels['tvdb_id'])
        item.infoLabels = infoLabels
        set_infoLabels_item(item)

        return True

    else:
        item.infoLabels = infoLabels
        return False


def get_nfo(item):
    """
    Devuelve la información necesaria para que se scrapee el resultado en la videoteca de kodi, para tmdb funciona
    solo pasandole la url.
    @param item: elemento que contiene los datos necesarios para generar la info
    @type item: Item
    @rtype: str
    @return:
    """
    if "season" in item.infoLabels and "episode" in item.infoLabels:
        info_nfo = "https://www.themoviedb.org/tv/%s/season/%s/episode/%s\n" % \
                   (item.infoLabels['tmdb_id'], item.contentSeason, item.contentEpisodeNumber)
    else:
        info_nfo = ', '.join(item.infoLabels['url_scraper']) + "\n"

    return info_nfo


def completar_codigos(item):
    """
    Si es necesario comprueba si existe el identificador de tvdb y sino existe trata de buscarlo
    """
    if item.contentType != "movie" and not item.infoLabels['tvdb_id']:
        # Lanzar busqueda por imdb_id en tvdb
        from core.tvdb import Tvdb
        ob = Tvdb(imdb_id=item.infoLabels['imdb_id'])
        item.infoLabels['tvdb_id'] = ob.get_id()
    if item.infoLabels['tvdb_id']:
        url_scraper = "http://thetvdb.com/index.php?tab=series&id=%s" % item.infoLabels['tvdb_id']
        if url_scraper not in item.infoLabels['url_scraper']:
            item.infoLabels['url_scraper'].append(url_scraper)


def discovery(item, dict_=False, cast=False):
    from core.item import Item

    if dict_:
        listado = Tmdb(discover = dict_, cast=cast)

    elif item.search_type == 'discover':
        listado = Tmdb(discover={'url':'discover/%s' % item.type, 'with_genres':item.list_type, 'language':def_lang,
                                 'page':item.page})

    elif item.search_type == 'list':
        if item.page == '':
            item.page = '1'
        listado = Tmdb(discover={'url': item.list_type, 'language':def_lang, 'page':item.page})

    return listado

def get_genres(type):
    lang = def_lang
    genres = Tmdb(tipo=type)

    return genres.dic_generos[lang]


# Clase auxiliar
class ResultDictDefault(dict):
    # Python 2.4
    def __getitem__(self, key):
        try:
            return super(ResultDictDefault, self).__getitem__(key)
        except:
            return self.__missing__(key)

    def __missing__(self, key):
        """
        valores por defecto en caso de que la clave solicitada no exista
        """
        if key in ['genre_ids', 'genre', 'genres']:
            return list()
        elif key == 'images_posters':
            posters = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and \
                            'posters' in super(ResultDictDefault, self).__getitem__('images'):
                posters = super(ResultDictDefault, self).__getitem__('images')['posters']
                super(ResultDictDefault, self).__setattr__("images_posters", posters)

            return posters

        elif key == "images_backdrops":
            backdrops = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and \
                            'backdrops' in super(ResultDictDefault, self).__getitem__('images'):
                backdrops = super(ResultDictDefault, self).__getitem__('images')['backdrops']
                super(ResultDictDefault, self).__setattr__("images_backdrops", backdrops)

            return backdrops

        elif key == "images_profiles":
            profiles = dict()
            if 'images' in list(super(ResultDictDefault, self).keys()) and \
                            'profiles' in super(ResultDictDefault, self).__getitem__('images'):
                profiles = super(ResultDictDefault, self).__getitem__('images')['profiles']
                super(ResultDictDefault, self).__setattr__("images_profiles", profiles)

            return profiles

        else:
            # El resto de claves devuelven cadenas vacias por defecto
            return ""

    def __str__(self):
        return self.tostring(separador=',\n')

    def tostring(self, separador=',\n'):
        ls = []
        for i in list(super(ResultDictDefault, self).items()):
            i_str = str(i)[1:-1]
            if isinstance(i[0], str):
                old = i[0] + "',"
                new = i[0] + "':"
            else:
                old = str(i[0]) + ","
                new = str(i[0]) + ":"
            ls.append(i_str.replace(old, new, 1))

        return "{%s}" % separador.join(ls)


# ---------------------------------------------------------------------------------------------------------------
# class Tmdb:
#   Scraper para el addon basado en el Api de https://www.themoviedb.org/
#   version 1.4:
#       - Documentada limitacion de uso de la API (ver mas abajo).
#       - Añadido metodo get_temporada()
#   version 1.3:
#       - Corregido error al devolver None el path_poster y el backdrop_path
#       - Corregido error que hacia que en el listado de generos se fueran acumulando de una llamada a otra
#       - Añadido metodo get_generos()
#       - Añadido parametros opcional idioma_alternativo al metodo get_sinopsis()
#
#
#   Uso:
#   Metodos constructores:
#    Tmdb(texto_buscado, tipo)
#        Parametros:
#            texto_buscado:(str) Texto o parte del texto a buscar
#            tipo: ("movie" o "tv") Tipo de resultado buscado peliculas o series. Por defecto "movie"
#            (opcional) idioma_busqueda: (str) codigo del idioma segun ISO 639-1
#            (opcional) include_adult: (bool) Se incluyen contenidos para adultos en la busqueda o no. Por defecto
# 'False'
#            (opcional) year: (str) Año de lanzamiento.
#            (opcional) page: (int) Cuando hay muchos resultados para una busqueda estos se organizan por paginas.
#                            Podemos cargar la pagina que deseemos aunque por defecto siempre es la primera.
#        Return:
#            Esta llamada devuelve un objeto Tmdb que contiene la primera pagina del resultado de buscar 'texto_buscado'
#            en la web themoviedb.org. Cuantos mas parametros opcionales se incluyan mas precisa sera la busqueda.
#            Ademas el objeto esta inicializado con el primer resultado de la primera pagina de resultados.
#    Tmdb(id_Tmdb,tipo)
#       Parametros:
#           id_Tmdb: (str) Codigo identificador de una determinada pelicula o serie en themoviedb.org
#           tipo: ("movie" o "tv") Tipo de resultado buscado peliculas o series. Por defecto "movie"
#           (opcional) idioma_busqueda: (str) codigo del idioma segun ISO 639-1
#       Return:
#           Esta llamada devuelve un objeto Tmdb que contiene el resultado de buscar una pelicula o serie con el
# identificador id_Tmd
#           en la web themoviedb.org.
#    Tmdb(external_id, external_source, tipo)
#       Parametros:
#           external_id: (str) Codigo identificador de una determinada pelicula o serie en la web referenciada por
# 'external_source'.
#           external_source: (Para series:"imdb_id","freebase_mid","freebase_id","tvdb_id","tvrage_id"; Para
# peliculas:"imdb_id")
#           tipo: ("movie" o "tv") Tipo de resultado buscado peliculas o series. Por defecto "movie"
#           (opcional) idioma_busqueda: (str) codigo del idioma segun ISO 639-1
#       Return:
#           Esta llamada devuelve un objeto Tmdb que contiene el resultado de buscar una pelicula o serie con el
# identificador 'external_id' de
#           la web referenciada por 'external_source' en la web themoviedb.org.
#
#   Metodos principales:
#    get_id(): Retorna un str con el identificador Tmdb de la pelicula o serie cargada o una cadena vacia si no hubiese
# nada cargado.
#    get_sinopsis(idioma_alternativo): Retorna un str con la sinopsis de la serie o pelicula cargada.
#    get_poster (tipo_respuesta,size): Obtiene el poster o un listado de posters.
#    get_backdrop (tipo_respuesta,size): Obtiene una imagen de fondo o un listado de imagenes de fondo.
#    get_temporada(temporada): Obtiene un diccionario con datos especificos de la temporada.
#    get_episodio (temporada, capitulo): Obtiene un diccionario con datos especificos del episodio.
#    get_generos(): Retorna un str con la lista de generos a los que pertenece la pelicula o serie.
#
#
#   Otros metodos:
#    load_resultado(resultado, page): Cuando la busqueda devuelve varios resultados podemos seleccionar que resultado
# concreto y de que pagina cargar los datos.
#
#   Limitaciones:
#   El uso de la API impone un limite de 20 conexiones simultaneas (concurrencia) o 30 peticiones en 10 segundos por IP
# Informacion sobre la api : http://docs.themoviedb.apiary.io
# -------------------------------------------------------------------------------------------------------------------


class Tmdb(object):
    # Atributo de clase
    dic_generos = {}
    '''
    dic_generos={"id_idioma1": {"tv": {"id1": "name1",
                                       "id2": "name2"
                                      },
                                "movie": {"id1": "name1",
                                          "id2": "name2"
                                          }
                                }
                }
    '''
    dic_country = {"AD": "Andorra", "AE": "Emiratos Árabes Unidos", "AF": "Afganistán", "AG": "Antigua y Barbuda",
                   "AI": "Anguila", "AL": "Albania", "AM": "Armenia", "AN": "Antillas Neerlandesas", "AO": "Angola",
                   "AQ": "Antártida", "AR": "Argentina", "AS": "Samoa Americana", "AT": "Austria", "AU": "Australia",
                   "AW": "Aruba", "AX": "Islas de Åland", "AZ": "Azerbayán", "BA": "Bosnia y Herzegovina",
                   "BD": "Bangladesh", "BE": "Bélgica", "BF": "Burkina Faso", "BG": "Bulgaria", "BI": "Burundi",
                   "BJ": "Benín", "BL": "San Bartolomé", "BM": "Islas Bermudas", "BN": "Brunéi", "BO": "Bolivia",
                   "BR": "Brasil", "BS": "Bahamas", "BT": "Bhután", "BV": "Isla Bouvet", "BW": "Botsuana",
                   "BY": "Bielorrusia", "BZ": "Belice", "CA": "Canadá", "CC": "Islas Cocos (Keeling)", "CD": "Congo",
                   "CF": "República Centroafricana", "CG": "Congo", "CH": "Suiza", "CI": "Costa de Marfil",
                   "CK": "Islas Cook", "CL": "Chile", "CM": "Camerún", "CN": "China", "CO": "Colombia",
                   "CR": "Costa Rica", "CU": "Cuba", "CV": "Cabo Verde", "CX": "Isla de Navidad", "CY": "Chipre",
                   "CZ": "República Checa", "DE": "Alemania", "DJ": "Yibuti", "DK": "Dinamarca", "DZ": "Algeria",
                   "EC": "Ecuador", "EE": "Estonia", "EG": "Egipto", "EH": "Sahara Occidental", "ER": "Eritrea",
                   "ES": "España", "ET": "Etiopía", "FI": "Finlandia", "FJ": "Fiyi", "FK": "Islas Malvinas",
                   "FM": "Micronesia", "FO": "Islas Feroe", "FR": "Francia", "GA": "Gabón", "GB": "Gran Bretaña",
                   "GD": "Granada", "GE": "Georgia", "GF": "Guayana Francesa", "GG": "Guernsey", "GH": "Ghana",
                   "GI": "Gibraltar", "GL": "Groenlandia", "GM": "Gambia", "GN": "Guinea", "GP": "Guadalupe",
                   "GQ": "Guinea Ecuatorial", "GR": "Grecia", "GS": "Islas Georgias del Sur y Sandwich del Sur",
                   "GT": "Guatemala", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong kong",
                   "HM": "Islas Heard y McDonald", "HN": "Honduras", "HR": "Croacia", "HT": "Haití", "HU": "Hungría",
                   "ID": "Indonesia", "IE": "Irlanda", "IM": "Isla de Man", "IN": "India",
                   "IO": "Territorio Británico del Océano Índico", "IQ": "Irak", "IR": "Irán", "IS": "Islandia",
                   "IT": "Italia", "JE": "Jersey", "JM": "Jamaica", "JO": "Jordania", "JP": "Japón", "KG": "Kirgizstán",
                   "KH": "Camboya", "KM": "Comoras", "KP": "Corea del Norte", "KR": "Corea del Sur", "KW": "Kuwait",
                   "KY": "Islas Caimán", "KZ": "Kazajistán", "LA": "Laos", "LB": "Líbano", "LC": "Santa Lucía",
                   "LI": "Liechtenstein", "LK": "Sri lanka", "LR": "Liberia", "LS": "Lesoto", "LT": "Lituania",
                   "LU": "Luxemburgo", "LV": "Letonia", "LY": "Libia", "MA": "Marruecos", "MC": "Mónaco",
                   "MD": "Moldavia", "ME": "Montenegro", "MF": "San Martín (Francia)", "MG": "Madagascar",
                   "MH": "Islas Marshall", "MK": "Macedônia", "ML": "Mali", "MM": "Birmania", "MN": "Mongolia",
                   "MO": "Macao", "MP": "Islas Marianas del Norte", "MQ": "Martinica", "MR": "Mauritania",
                   "MS": "Montserrat", "MT": "Malta", "MU": "Mauricio", "MV": "Islas Maldivas", "MW": "Malawi",
                   "MX": "México", "MY": "Malasia", "NA": "Namibia", "NE": "Niger", "NG": "Nigeria", "NI": "Nicaragua",
                   "NL": "Países Bajos", "NO": "Noruega", "NP": "Nepal", "NR": "Nauru", "NU": "Niue",
                   "NZ": "Nueva Zelanda", "OM": "Omán", "PA": "Panamá", "PE": "Perú", "PF": "Polinesia Francesa",
                   "PH": "Filipinas", "PK": "Pakistán", "PL": "Polonia", "PM": "San Pedro y Miquelón",
                   "PN": "Islas Pitcairn", "PR": "Puerto Rico", "PS": "Palestina", "PT": "Portugal", "PW": "Palau",
                   "PY": "Paraguay", "QA": "Qatar", "RE": "Reunión", "RO": "Rumanía", "RS": "Serbia", "RU": "Rusia",
                   "RW": "Ruanda", "SA": "Arabia Saudita", "SB": "Islas Salomón", "SC": "Seychelles", "SD": "Sudán",
                   "SE": "Suecia", "SG": "Singapur", "SH": "Santa Elena", "SI": "Eslovenia",
                   "SJ": "Svalbard y Jan Mayen",
                   "SK": "Eslovaquia", "SL": "Sierra Leona", "SM": "San Marino", "SN": "Senegal", "SO": "Somalia",
                   "SV": "El Salvador", "SY": "Siria", "SZ": "Swazilandia", "TC": "Islas Turcas y Caicos", "TD": "Chad",
                   "TF": "Territorios Australes y Antárticas Franceses", "TG": "Togo", "TH": "Tailandia",
                   "TJ": "Tadjikistán", "TK": "Tokelau", "TL": "Timor Oriental", "TM": "Turkmenistán", "TN": "Tunez",
                   "TO": "Tonga", "TR": "Turquía", "TT": "Trinidad y Tobago", "TV": "Tuvalu", "TW": "Taiwán",
                   "TZ": "Tanzania", "UA": "Ucrania", "UG": "Uganda",
                   "UM": "Islas Ultramarinas Menores de Estados Unidos",
                   "UY": "Uruguay", "UZ": "Uzbekistán", "VA": "Ciudad del Vaticano",
                   "VC": "San Vicente y las Granadinas",
                   "VE": "Venezuela", "VG": "Islas Vírgenes Británicas", "VI": "Islas Vírgenes de los Estados Unidos",
                   "VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis y Futuna", "WS": "Samoa", "YE": "Yemen",
                   "YT": "Mayotte", "ZA": "Sudáfrica", "ZM": "Zambia", "ZW": "Zimbabue", "BB": "Barbados",
                   "BH": "Bahrein",
                   "DM": "Dominica", "DO": "República Dominicana", "GU": "Guam", "IL": "Israel", "KE": "Kenia",
                   "KI": "Kiribati", "KN": "San Cristóbal y Nieves", "MZ": "Mozambique", "NC": "Nueva Caledonia",
                   "NF": "Isla Norfolk", "PG": "Papúa Nueva Guinea", "SR": "Surinám", "ST": "Santo Tomé y Príncipe",
                   "US": "EEUU"}

    def __init__(self, **kwargs):
        self.page = kwargs.get('page', 1)
        self.index_results = 0
        self.cast = kwargs.get('cast', False)
        self.results = []
        self.result = ResultDictDefault()
        self.total_pages = 0
        self.total_results = 0

        self.temporada = {}
        self.texto_buscado = kwargs.get('texto_buscado', '')

        self.busqueda_id = kwargs.get('id_Tmdb', '')
        self.busqueda_texto = re.sub('\[\\\?(B|I|COLOR)\s?[^\]]*\]', '', self.texto_buscado).strip()
        self.busqueda_tipo = kwargs.get('tipo', '')
        self.busqueda_idioma = kwargs.get('idioma_busqueda', def_lang)
        # self.busqueda_include_adult = kwargs.get('include_adult', False)
        self.busqueda_year = kwargs.get('year', '')
        self.busqueda_filtro = kwargs.get('filtro', {})
        self.discover = kwargs.get('discover', {})

        # Reellenar diccionario de generos si es necesario
        if (self.busqueda_tipo == 'movie' or self.busqueda_tipo == "tv") and \
                (self.busqueda_idioma not in Tmdb.dic_generos or
                         self.busqueda_tipo not in Tmdb.dic_generos[self.busqueda_idioma]):
            self.rellenar_dic_generos(self.busqueda_tipo, self.busqueda_idioma)

        if not self.busqueda_tipo:
            self.busqueda_tipo = 'movie'

        if self.busqueda_id:
            # Busqueda por identificador tmdb
            self.__by_id()

        elif self.busqueda_texto:
            # Busqueda por texto
            self.__search(page=self.page)

        elif 'external_source' in kwargs and 'external_id' in kwargs:
            # Busqueda por identificador externo segun el tipo.
            # TV Series: imdb_id, freebase_mid, freebase_id, tvdb_id, tvrage_id
            # Movies: imdb_id
            if (self.busqueda_tipo == 'movie' and kwargs.get('external_source') == "imdb_id") or \
                    (self.busqueda_tipo == 'tv' and kwargs.get('external_source') in (
                            "imdb_id", "freebase_mid", "freebase_id", "tvdb_id", "tvrage_id")):
                self.busqueda_id = kwargs.get('external_id')
                self.__by_id(source=kwargs.get('external_source'))

        elif self.discover:
            self.__discover()

        else:
            logger.debug("Created empty object")

    @staticmethod
    @cache_response
    def get_json(url):

        try:
            result = httptools.downloadpage(url, cookies=False, ignore_response_code=True)

            res_headers = result.headers
            dict_data = jsontools.load(result.data)
            #logger.debug("result_data es %s" % dict_data)

            if "status_code" in dict_data:
                #logger.debug("\nError de tmdb: %s %s" % (dict_data["status_code"], dict_data["status_message"]))

                if dict_data["status_code"] == 25:
                    while "status_code" in dict_data and dict_data["status_code"] == 25:
                        wait = int(res_headers['retry-after'])
                        #logger.error("Limite alcanzado, esperamos para volver a llamar en ...%s" % wait)
                        time.sleep(wait)
                        # logger.debug("RE Llamada #%s" % d)
                        result = httptools.downloadpage(url, cookies=False)

                        res_headers = result.headers
                        # logger.debug("res_headers es %s" % res_headers)
                        dict_data = jsontools.load(result.data)
                        # logger.debug("result_data es %s" % dict_data)

        # error al obtener los datos
        except Exception as ex:
            message = "An exception of type %s occured. Arguments:\n%s" % (type(ex).__name__, repr(ex.args))
            logger.error("error in: %s" % message)
            dict_data = {}

        return dict_data

    @classmethod
    def rellenar_dic_generos(cls, tipo='movie', idioma=def_lang):
        # Rellenar diccionario de generos del tipo e idioma pasados como parametros
        if idioma not in cls.dic_generos:
            cls.dic_generos[idioma] = {}

        if tipo not in cls.dic_generos[idioma]:
            cls.dic_generos[idioma][tipo] = {}
            url = ('http://api.themoviedb.org/3/genre/%s/list?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s'
                   % (tipo, idioma))
            try:
                logger.info("[Tmdb.py] Filling in dictionary of genres")

                resultado = cls.get_json(url)
                if not isinstance(resultado, dict):
                    resultado = ast.literal_eval(resultado.decode('utf-8'))
                lista_generos = resultado["genres"]

                for i in lista_generos:
                    cls.dic_generos[idioma][tipo][str(i["id"])] = i["name"]
            except:
                logger.error("Error generating dictionaries")
                import traceback
                logger.error(traceback.format_exc())

    def __by_id(self, source='tmdb'):

        if self.busqueda_id:
            if source == "tmdb":
                # http://api.themoviedb.org/3/movie/1924?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es
                #   &append_to_response=images,videos,external_ids,credits&include_image_language=es,null
                # http://api.themoviedb.org/3/tv/1407?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es
                #   &append_to_response=images,videos,external_ids,credits&include_image_language=es,null
                url = ('http://api.themoviedb.org/3/%s/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s'
                       '&append_to_response=images,videos,external_ids,credits&include_image_language=%s,null' %
                       (self.busqueda_tipo, self.busqueda_id, self.busqueda_idioma, self.busqueda_idioma))
                buscando = "id_Tmdb: %s" % self.busqueda_id
            else:
                # http://api.themoviedb.org/3/find/%s?external_source=imdb_id&api_key=a1ab8b8669da03637a4b98fa39c39228
                url = ('http://api.themoviedb.org/3/find/%s?external_source=%s&api_key=a1ab8b8669da03637a4b98fa39c39228'
                       '&language=%s' % (self.busqueda_id, source, self.busqueda_idioma))
                buscando = "%s: %s" % (source.capitalize(), self.busqueda_id)

            logger.info("[Tmdb.py] Searching %s:\n%s" % (buscando, url))
            resultado = self.get_json(url)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            if resultado:
                if source != "tmdb":
                    if self.busqueda_tipo == "movie":
                        resultado = resultado["movie_results"][0]
                    else:
                        resultado = resultado["tv_results"][0]

                self.results = [resultado]
                self.total_results = 1
                self.total_pages = 1
                self.result = ResultDictDefault(resultado)

            else:
                # No hay resultados de la busqueda
                msg = "The search of %s gave no results" % buscando
                logger.debug(msg)

    def __search(self, index_results=0, page=1):
        self.result = ResultDictDefault()
        results = []
        text_simple = self.busqueda_texto.lower()
        text_quote = urllib.quote(text_simple)
        total_results = 0
        total_pages = 0
        buscando = ""

        if self.busqueda_texto:
            # http://api.themoviedb.org/3/search/movie?api_key=a1ab8b8669da03637a4b98fa39c39228&query=superman&language=es
            # &include_adult=false&page=1
            url = ('http://api.themoviedb.org/3/search/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&query=%s&language=%s'
                   '&include_adult=%s&page=%s' % (self.busqueda_tipo, text_quote,
                                                  self.busqueda_idioma, True, page))

            if self.busqueda_year:
                url += '&year=%s' % self.busqueda_year

            buscando = self.busqueda_texto.capitalize()
            logger.info("[Tmdb.py] Searching %s on page %s:\n%s" % (buscando, page, url))
            resultado = self.get_json(url)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            total_results = resultado.get("total_results", 0)
            total_pages = resultado.get("total_pages", 0)

            if total_results > 0:
                results = resultado["results"]

            if self.busqueda_filtro and total_results > 1:
                # TODO documentar esta parte
                for key, value in list(dict(self.busqueda_filtro).items()):
                    for r in results[:]:
                        if not r[key]:
                            r[key] = str(r[key])
                        if key not in r or value not in r[key]:
                            results.remove(r)
                            total_results -= 1

        if results:
            if index_results >= len(results):
                # Se ha solicitado un numero de resultado mayor de los obtenidos
                logger.error(
                    "The search for '%s' gave %s results for the page %s \n It is impossible to show the result number %s"
                    % (buscando, len(results), page, index_results))
                return 0

            # Retornamos el numero de resultados de esta pagina
            self.results = results
            self.total_results = total_results
            self.total_pages = total_pages
            self.result = ResultDictDefault(self.results[index_results])
            return len(self.results)

        else:
            # No hay resultados de la busqueda
            msg = "The search for '%s' gave no results for page %s" % (buscando, page)
            logger.error(msg)
            return 0


    def __discover(self, index_results=0):
        self.result = ResultDictDefault()
        results = []
        total_results = 0
        total_pages = 0

        # Ejemplo self.discover: {'url': 'discover/movie', 'with_cast': '1'}
        # url: Método de la api a ejecutar
        # resto de claves: Parámetros de la búsqueda concatenados a la url
        type_search = self.discover.get('url', '')
        if type_search:
            params = []
            for key, value in list(self.discover.items()):
                if key != "url":
                    params.append(key + "=" + str(value))
            # http://api.themoviedb.org/3/discover/movie?api_key=a1ab8b8669da03637a4b98fa39c39228&query=superman&language=es
            url = ('http://api.themoviedb.org/3/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&%s'
                   % (type_search, "&".join(params)))

            logger.info("[Tmdb.py] Searcing %s:\n%s" % (type_search, url))
            resultado = self.get_json(url)
            if not isinstance(resultado, dict):
                resultado = ast.literal_eval(resultado.decode('utf-8'))

            total_results = resultado.get("total_results", -1)
            total_pages = resultado.get("total_pages", 1)

            if total_results > 0 or self.cast:
                if self.cast:
                    results = resultado[self.cast]
                    total_results = len(results)
                else:
                    results = resultado["results"]
                if self.busqueda_filtro and results:
                    # TODO documentar esta parte
                    for key, value in list(dict(self.busqueda_filtro).items()):
                        for r in results[:]:
                            if key not in r or r[key] != value:
                                results.remove(r)
                                total_results -= 1
            elif total_results == -1:
                results = resultado

            if index_results >= len(results):
                logger.error(
                    "The search for '%s' did not give %s results" % (type_search, index_results))
                return 0

        # Retornamos el numero de resultados de esta pagina
        if results:
            self.results = results
            self.total_results = total_results
            self.total_pages = total_pages
            if total_results > 0:
                self.result = ResultDictDefault(self.results[index_results])

            else:
                self.result = results
            return len(self.results)
        else:
            # No hay resultados de la busqueda
            logger.error("The search for '%s' gave no results" % type_search)
            return 0

    def load_resultado(self, index_results=0, page=1):
        # Si no hay resultados, solo hay uno o
        # si el numero de resultados de esta pagina es menor al indice buscado salir
        self.result = ResultDictDefault()
        num_result_page = len(self.results)

        if page > self.total_pages:
            return False

        if page != self.page:
            num_result_page = self.__search(index_results, page)

        if num_result_page == 0 or num_result_page <= index_results:
            return False

        self.page = page
        self.index_results = index_results
        self.result = ResultDictDefault(self.results[index_results])
        return True

    def get_list_resultados(self, num_result=20):
        # logger.info("self %s" % str(self))
        # TODO documentar
        res = []

        if num_result <= 0:
            num_result = self.total_results
        num_result = min([num_result, self.total_results])

        cr = 0
        for p in range(1, self.total_pages + 1):
            for r in range(0, len(self.results)):
                try:
                    if self.load_resultado(r, p):
                        result = self.result.copy()

                        result['thumbnail'] = self.get_poster(size="w300")
                        result['fanart'] = self.get_backdrop()

                        res.append(result)
                        cr += 1

                        if cr >= num_result:
                            return res
                except:
                    continue

        return res

    def get_generos(self, origen=None):
        """
        :param origen: Diccionario origen de donde se obtiene los infoLabels, por omision self.result
        :type origen: Dict
        :return: Devuelve la lista de generos a los que pertenece la pelicula o serie.
        :rtype: str
        """
        genre_list = []

        if not origen:
            origen = self.result

        if "genre_ids" in origen:
            # Buscar lista de generos por IDs
            for i in origen.get("genre_ids"):
                try:
                    genre_list.append(Tmdb.dic_generos[self.busqueda_idioma][self.busqueda_tipo][str(i)])
                except:
                    pass

        elif "genre" in origen or "genres" in origen:
            # Buscar lista de generos (lista de objetos {id,nombre})
            v = origen["genre"]
            v.extend(origen["genres"])
            for i in v:
                genre_list.append(i['name'])

        return ', '.join(genre_list)

    def search_by_id(self, id, source='tmdb', tipo='movie'):
        self.busqueda_id = id
        self.busqueda_tipo = tipo
        self.__by_id(source=source)

    def get_id(self):
        """

        :return: Devuelve el identificador Tmdb de la pelicula o serie cargada o una cadena vacia en caso de que no
            hubiese nada cargado. Se puede utilizar este metodo para saber si una busqueda ha dado resultado o no.
        :rtype: str
        """
        return str(self.result.get('id', ""))

    def get_sinopsis(self, idioma_alternativo=""):
        """

        :param idioma_alternativo: codigo del idioma, segun ISO 639-1, en el caso de que en el idioma fijado para la
            busqueda no exista sinopsis.
            Por defecto, se utiliza el idioma original. Si se utiliza None como idioma_alternativo, solo se buscara en
            el idioma fijado.
        :type idioma_alternativo: str
        :return: Devuelve la sinopsis de una pelicula o serie
        :rtype: str
        """
        ret = ""

        if 'id' in self.result:
            ret = self.result.get('overview')
            if ret == "" and str(idioma_alternativo).lower() != 'none':
                # Vamos a lanzar una busqueda por id y releer de nuevo la sinopsis
                self.busqueda_id = str(self.result["id"])
                if idioma_alternativo:
                    self.busqueda_idioma = idioma_alternativo
                else:
                    self.busqueda_idioma = self.result['original_language']

                url = ('http://api.themoviedb.org/3/%s/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s' %
                       (self.busqueda_tipo, self.busqueda_id, self.busqueda_idioma))

                resultado = self.get_json(url)
                if not isinstance(resultado, dict):
                    resultado = ast.literal_eval(resultado.decode('utf-8'))

                if 'overview' in resultado:
                    self.result['overview'] = resultado['overview']
                    ret = self.result['overview']

        return ret

    def get_poster(self, tipo_respuesta="str", size="original"):
        """

        @param tipo_respuesta: Tipo de dato devuelto por este metodo. Por defecto "str"
        @type tipo_respuesta: list, str
        @param size: ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280", "original")
            Indica la anchura(w) o altura(h) de la imagen a descargar. Por defecto "original"
        @return: Si el tipo_respuesta es "list" devuelve un listado con todas las urls de las imagenes tipo poster del
            tamaño especificado.
            Si el tipo_respuesta es "str" devuelve la url de la imagen tipo poster, mas valorada, del tamaño
            especificado.
            Si el tamaño especificado no existe se retornan las imagenes al tamaño original.
        @rtype: list, str
        """
        ret = []
        if size not in ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280"):
            size = "original"

        if self.result["poster_path"] is None or self.result["poster_path"] == "":
            poster_path = ""
        else:
            poster_path = 'http://image.tmdb.org/t/p/' + size + self.result["poster_path"]

        if tipo_respuesta == 'str':
            return poster_path
        elif not self.result["id"]:
            return []

        if len(self.result['images_posters']) == 0:
            # Vamos a lanzar una busqueda por id y releer de nuevo
            self.busqueda_id = str(self.result["id"])
            self.__by_id()

        if len(self.result['images_posters']) > 0:
            for i in self.result['images_posters']:
                imagen_path = i['file_path']
                if size != "original":
                    # No podemos pedir tamaños mayores que el original
                    if size[1] == 'w' and int(imagen_path['width']) < int(size[1:]):
                        size = "original"
                    elif size[1] == 'h' and int(imagen_path['height']) < int(size[1:]):
                        size = "original"
                ret.append('http://image.tmdb.org/t/p/' + size + imagen_path)
        else:
            ret.append(poster_path)

        return ret

    def get_backdrop(self, tipo_respuesta="str", size="original"):
        """
        Devuelve las imagenes de tipo backdrop
        @param tipo_respuesta: Tipo de dato devuelto por este metodo. Por defecto "str"
        @type tipo_respuesta: list, str
        @param size: ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280", "original")
            Indica la anchura(w) o altura(h) de la imagen a descargar. Por defecto "original"
        @type size: str
        @return: Si el tipo_respuesta es "list" devuelve un listado con todas las urls de las imagenes tipo backdrop del
            tamaño especificado.
        Si el tipo_respuesta es "str" devuelve la url de la imagen tipo backdrop, mas valorada, del tamaño especificado.
        Si el tamaño especificado no existe se retornan las imagenes al tamaño original.
        @rtype: list, str
        """
        ret = []
        if size not in ("w45", "w92", "w154", "w185", "w300", "w342", "w500", "w600", "h632", "w780", "w1280"):
            size = "original"

        if self.result["backdrop_path"] is None or self.result["backdrop_path"] == "":
            backdrop_path = ""
        else:
            backdrop_path = 'http://image.tmdb.org/t/p/' + size + self.result["backdrop_path"]

        if tipo_respuesta == 'str':
            return backdrop_path
        elif self.result["id"] == "":
            return []

        if len(self.result['images_backdrops']) == 0:
            # Vamos a lanzar una busqueda por id y releer de nuevo todo
            self.busqueda_id = str(self.result["id"])
            self.__by_id()

        if len(self.result['images_backdrops']) > 0:
            for i in self.result['images_backdrops']:
                imagen_path = i['file_path']
                if size != "original":
                    # No podemos pedir tamaños mayores que el original
                    if size[1] == 'w' and int(imagen_path['width']) < int(size[1:]):
                        size = "original"
                    elif size[1] == 'h' and int(imagen_path['height']) < int(size[1:]):
                        size = "original"
                ret.append('http://image.tmdb.org/t/p/' + size + imagen_path)
        else:
            ret.append(backdrop_path)

        return ret

    def get_temporada(self, numtemporada=1):
        # --------------------------------------------------------------------------------------------------------------------------------------------
        #   Parametros:
        #       numtemporada: (int) Numero de temporada. Por defecto 1.
        #   Return: (dic)
        #       Devuelve un dicionario con datos sobre la temporada.
        #       Puede obtener mas informacion sobre los datos devueltos en:
        #           http://docs.themoviedb.apiary.io/#reference/tv-seasons/tvidseasonseasonnumber/get
        #           http://docs.themoviedb.apiary.io/#reference/tv-seasons/tvidseasonseasonnumbercredits/get
        # --------------------------------------------------------------------------------------------------------------------------------------------
        if not self.result["id"] or self.busqueda_tipo != "tv":
            return {}

        numtemporada = int(numtemporada)
        if numtemporada < 0:
            numtemporada = 1

        if not self.temporada.get(numtemporada, {}):
            # Si no hay datos sobre la temporada solicitada, consultar en la web

            # http://api.themoviedb.org/3/tv/1407/season/1?api_key=a1ab8b8669da03637a4b98fa39c39228&language=es&
            # append_to_response=credits
            url = "http://api.themoviedb.org/3/tv/%s/season/%s?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s" \
                  "&append_to_response=credits" % (self.result["id"], numtemporada, self.busqueda_idioma)

            buscando = "id_Tmdb: " + str(self.result["id"]) + " season: " + str(numtemporada) + "\nURL: " + url
            logger.info("[Tmdb.py] Searcing " + buscando)
            try:
                self.temporada[numtemporada] = self.get_json(url)
                if not isinstance(self.temporada[numtemporada], dict):
                    self.temporada[numtemporada] = ast.literal_eval(self.temporada[numtemporada].decode('utf-8'))

            except:
                logger.error("Unable to get the season")
                self.temporada[numtemporada] = {"status_code": 15, "status_message": "Failed"}
                self.temporada[numtemporada] = {"episodes": {}}

            if "status_code" in self.temporada[numtemporada]:
                #Se ha producido un error
                msg = config.get_localized_string(70496) + buscando + config.get_localized_string(70497)
                msg += "\nTmdb error: %s %s" % (
                self.temporada[numtemporada]["status_code"], self.temporada[numtemporada]["status_message"])
                logger.debug(msg)
                self.temporada[numtemporada] = {}

        return self.temporada[numtemporada]

    def get_episodio(self, numtemporada=1, capitulo=1):
        # --------------------------------------------------------------------------------------------------------------------------------------------
        #   Parametros:
        #       numtemporada(opcional): (int) Numero de temporada. Por defecto 1.
        #       capitulo: (int) Numero de capitulo. Por defecto 1.
        #   Return: (dic)
        #       Devuelve un dicionario con los siguientes elementos:
        #           "temporada_nombre", "temporada_sinopsis", "temporada_poster", "temporada_num_episodios"(int),
        #           "temporada_air_date",  "episodio_vote_count", "episodio_vote_average",
        #           "episodio_titulo", "episodio_sinopsis", "episodio_imagen", "episodio_air_date",
        #           "episodio_crew" y "episodio_guest_stars",
        #       Con capitulo == -1 el diccionario solo tendra los elementos referentes a la temporada
        # --------------------------------------------------------------------------------------------------------------------------------------------
        if not self.result["id"] or self.busqueda_tipo != "tv":
            return {}

        try:
            capitulo = int(capitulo)
            numtemporada = int(numtemporada)
        except ValueError:
            logger.debug("The episode or season number is not valid")
            return {}

        temporada = self.get_temporada(numtemporada)
        if not isinstance(temporada, dict):
            temporada = ast.literal_eval(temporada.decode('utf-8'))
        if not temporada:
            # Se ha producido un error
            return {}

        if len(temporada["episodes"]) == 0 or len(temporada["episodes"]) < capitulo:
            # Se ha producido un error
            logger.error("Episode %d of the season %d not found." % (capitulo, numtemporada))
            return {}

        ret_dic = dict()
        # Obtener datos para esta temporada
        ret_dic["temporada_nombre"] = temporada["name"]
        ret_dic["temporada_sinopsis"] = temporada["overview"]
        ret_dic["temporada_num_episodios"] = len(temporada["episodes"])
        if temporada["air_date"]:
            date = temporada["air_date"].split("-")
            ret_dic["temporada_air_date"] = date[2] + "/" + date[1] + "/" + date[0]
        else:
            ret_dic["temporada_air_date"] = ""
        if temporada["poster_path"]:
            ret_dic["temporada_poster"] = 'http://image.tmdb.org/t/p/original' + temporada["poster_path"]
        else:
            ret_dic["temporada_poster"] = ""
        dic_aux = temporada.get('credits', {})
        ret_dic["temporada_cast"] = dic_aux.get('cast', [])
        ret_dic["temporada_crew"] = dic_aux.get('crew', [])
        if capitulo == -1:
            # Si solo buscamos datos de la temporada,
            # incluir el equipo tecnico que ha intervenido en algun capitulo
            dic_aux = dict((i['id'], i) for i in ret_dic["temporada_crew"])
            for e in temporada["episodes"]:
                for crew in e['crew']:
                    if crew['id'] not in list(dic_aux.keys()):
                        dic_aux[crew['id']] = crew
            ret_dic["temporada_crew"] = list(dic_aux.values())

        # Obtener datos del capitulo si procede
        if capitulo != -1:
            episodio = temporada["episodes"][capitulo - 1]
            ret_dic["episodio_titulo"] = episodio["name"]
            ret_dic["episodio_sinopsis"] = episodio["overview"]
            if episodio["air_date"]:
                date = episodio["air_date"].split("-")
                ret_dic["episodio_air_date"] = date[2] + "/" + date[1] + "/" + date[0]
            else:
                ret_dic["episodio_air_date"] = ""
            ret_dic["episodio_crew"] = episodio["crew"]
            ret_dic["episodio_guest_stars"] = episodio["guest_stars"]
            ret_dic["episodio_vote_count"] = episodio["vote_count"]
            ret_dic["episodio_vote_average"] = episodio["vote_average"]
            if episodio["still_path"]:
                ret_dic["episodio_imagen"] = 'http://image.tmdb.org/t/p/original' + episodio["still_path"]
            else:
                ret_dic["episodio_imagen"] = ""

        return ret_dic

    def get_videos(self):
        """
        :return: Devuelve una lista ordenada (idioma/resolucion/tipo) de objetos Dict en la que cada uno de
        sus elementos corresponde con un trailer, teaser o clip de youtube.
        :rtype: list of Dict
        """
        ret = []
        if self.result['id']:
            if self.result['videos']:
                self.result["videos"] = self.result["videos"]['results']
            else:
                # Primera búsqueda de videos en el idioma de busqueda
                url = "http://api.themoviedb.org/3/%s/%s/videos?api_key=a1ab8b8669da03637a4b98fa39c39228&language=%s" \
                      % (self.busqueda_tipo, self.result['id'], self.busqueda_idioma)

                dict_videos = self.get_json(url)
                if not isinstance(dict_videos, dict):
                    dict_videos = ast.literal_eval(dict_videos.decode('utf-8'))

                if dict_videos['results']:
                    dict_videos['results'] = sorted(dict_videos['results'], key=lambda x: (x['type'], x['size']))
                    self.result["videos"] = dict_videos['results']

            # Si el idioma de busqueda no es ingles, hacer una segunda búsqueda de videos en inglés
            if self.busqueda_idioma != 'en':
                url = "http://api.themoviedb.org/3/%s/%s/videos?api_key=a1ab8b8669da03637a4b98fa39c39228" \
                      % (self.busqueda_tipo, self.result['id'])

                dict_videos = self.get_json(url)
                if not isinstance(dict_videos, dict):
                    dict_videos = ast.literal_eval(dict_videos.decode('utf-8'))

                if dict_videos['results']:
                    dict_videos['results'] = sorted(dict_videos['results'], key=lambda x: (x['type'], x['size']))
                    self.result["videos"].extend(dict_videos['results'])

            # Si las busqueda han obtenido resultados devolver un listado de objetos
            for i in self.result['videos']:
                if i['site'] == "YouTube":
                    ret.append({'name': i['name'],
                                'url': "https://www.youtube.com/watch?v=%s" % i['key'],
                                'size': str(i['size']),
                                'type': i['type'],
                                'language': i['iso_639_1']})

        return ret

    def get_infoLabels(self, infoLabels=None, origen=None):
        """
        :param infoLabels: Informacion extra de la pelicula, serie, temporada o capitulo.
        :type infoLabels: Dict
        :param origen: Diccionario origen de donde se obtiene los infoLabels, por omision self.result
        :type origen: Dict
        :return: Devuelve la informacion extra obtenida del objeto actual. Si se paso el parametro infoLables, el valor
        devuelto sera el leido como parametro debidamente actualizado.
        :rtype: Dict
        """

        if infoLabels:
            ret_infoLabels = InfoLabels(infoLabels)
        else:
            ret_infoLabels = InfoLabels()

        # Iniciar listados
        l_country = [i.strip() for i in ret_infoLabels['country'].split(',') if ret_infoLabels['country']]
        l_director = [i.strip() for i in ret_infoLabels['director'].split(',') if ret_infoLabels['director']]
        l_writer = [i.strip() for i in ret_infoLabels['writer'].split(',') if ret_infoLabels['writer']]
        l_castandrole = ret_infoLabels.get('castandrole', [])

        if not origen:
            origen = self.result

        if 'credits' in list(origen.keys()):
            dic_origen_credits = origen['credits']
            origen['credits_cast'] = dic_origen_credits.get('cast', [])
            origen['credits_crew'] = dic_origen_credits.get('crew', [])
            del origen['credits']

        items = list(origen.items())

        # Informacion Temporada/episodio
        if ret_infoLabels['season'] and self.temporada.get(ret_infoLabels['season']):
            # Si hay datos cargados de la temporada indicada
            episodio = -1
            if ret_infoLabels['episode']:
                episodio = ret_infoLabels['episode']

            items.extend(list(self.get_episodio(ret_infoLabels['season'], episodio).items()))

        # logger.info("ret_infoLabels" % ret_infoLabels)

        for k, v in items:
            if not v:
                continue
            elif isinstance(v, str):
                v = re.sub(r"\n|\r|\t", "", v)
                # fix
                if v == "None":
                    continue

            if k == 'overview':
                if origen:
                    ret_infoLabels['plot'] = v
                else:
                    ret_infoLabels['plot'] = self.get_sinopsis()

            elif k == 'runtime':                                #Duration for movies
                ret_infoLabels['duration'] = int(v) * 60

            elif k == 'episode_run_time':                       #Duration for episodes
                try:
                    for v_alt in v:                             #It comes as a list (?!)
                        ret_infoLabels['duration'] = int(v_alt) * 60
                except:
                    pass

            elif k == 'release_date':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['release_date'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]

            elif k == 'first_air_date':
                ret_infoLabels['year'] = int(v[:4])
                ret_infoLabels['aired'] = v.split("-")[2] + "/" + v.split("-")[1] + "/" + v.split("-")[0]
                ret_infoLabels['premiered'] = ret_infoLabels['aired']

            elif k == 'original_title' or k == 'original_name':
                ret_infoLabels['originaltitle'] = v

            elif k == 'vote_average':
                ret_infoLabels['rating'] = float(v)

            elif k == 'vote_count':
                ret_infoLabels['votes'] = v

            elif k == 'poster_path':
                ret_infoLabels['thumbnail'] = 'http://image.tmdb.org/t/p/original' + v

            elif k == 'backdrop_path':
                ret_infoLabels['fanart'] = 'http://image.tmdb.org/t/p/original' + v

            elif k == 'id':
                ret_infoLabels['tmdb_id'] = v

            elif k == 'imdb_id':
                ret_infoLabels['imdb_id'] = v

            elif k == 'external_ids':
                if 'tvdb_id' in v:
                    ret_infoLabels['tvdb_id'] = v['tvdb_id']
                if 'imdb_id' in v:
                    ret_infoLabels['imdb_id'] = v['imdb_id']

            elif k in ['genres', "genre_ids", "genre"]:
                ret_infoLabels['genre'] = self.get_generos(origen)

            elif k == 'name' or k == 'title':
                ret_infoLabels['title'] = v

            elif k == 'production_companies':
                ret_infoLabels['studio'] = ", ".join(i['name'] for i in v)

            elif k == 'credits_cast' or k == 'temporada_cast' or k == 'episodio_guest_stars':
                dic_aux = dict((name, character) for (name, character) in l_castandrole)
                l_castandrole.extend([(p['name'], p['character']) for p in v if p['name'] not in list(dic_aux.keys())])

            elif k == 'videos':
                if not isinstance(v, list):
                    v = v.get('result', [])
                for i in v:
                    if i.get("site", "") == "YouTube":
                        ret_infoLabels['trailer'] = "https://www.youtube.com/watch?v=" + v[0]["key"]
                        break

            elif k == 'production_countries' or k == 'origin_country':
                if isinstance(v, str):
                    l_country = list(set(l_country + v.split(',')))

                elif isinstance(v, list) and len(v) > 0:
                    if isinstance(v[0], str):
                        l_country = list(set(l_country + v))
                    elif isinstance(v[0], dict):
                        # {'iso_3166_1': 'FR', 'name':'France'}
                        for i in v:
                            if 'iso_3166_1' in i:
                                pais = Tmdb.dic_country.get(i['iso_3166_1'], i['iso_3166_1'])
                                l_country = list(set(l_country + [pais]))

            elif k == 'credits_crew' or k == 'episodio_crew' or k == 'temporada_crew':
                for crew in v:
                    if crew['job'].lower() == 'director':
                        l_director = list(set(l_director + [crew['name']]))

                    elif crew['job'].lower() in ('screenplay', 'writer'):
                        l_writer = list(set(l_writer + [crew['name']]))

            elif k == 'created_by':
                for crew in v:
                    l_writer = list(set(l_writer + [crew['name']]))

            elif isinstance(v, str) or isinstance(v, int) or isinstance(v, float):
                ret_infoLabels[k] = v

            else:
                # logger.debug("Atributos no añadidos: " + k +'= '+ str(v))
                pass

        # Ordenar las listas y convertirlas en str si es necesario
        if l_castandrole:
            ret_infoLabels['castandrole'] = sorted(l_castandrole, key=lambda tup: tup[0])
        if l_country:
            ret_infoLabels['country'] = ', '.join(sorted(l_country))
        if l_director:
            ret_infoLabels['director'] = ', '.join(sorted(l_director))
        if l_writer:
            ret_infoLabels['writer'] = ', '.join(sorted(l_writer))

        return ret_infoLabels
