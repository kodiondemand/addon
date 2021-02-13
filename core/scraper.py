# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

#from builtins import str
from core.item import InfoLabels
from platformcode import config, logger
from platformcode import platformtools

# This module is an interface to implement different scrapers, it will contain all the common functions

dict_default = None
scraper = None


def find_and_set_infoLabels(item):
    """
        function called to search and set infolabels
        :param item:
        :return: Boolean indicating if the 'code' could be found
    """
    # from core.support import dbg;dbg()
    global scraper
    scraper = None
    # logger.debug("item:\n" + item.tostring('\n'))

    list_opciones_cuadro = [config.get_localized_string(60223), config.get_localized_string(60224)]
    # If more scrapers are added, they must be declared here-> "modulo_scraper": "Text_in_box"
    scrapers_disponibles = {'tmdb': config.get_localized_string(60225), 'tvdb': config.get_localized_string(60226)}

    # Get the default Scraper of the configuration according to the content type
    if item.contentType == "movie":
        scraper_actual = 'tmdb'
        # scraper_actual = ['tmdb'][config.get_setting("scraper_movies", "videolibrary")]
        tipo_contenido = "movie"
        title = item.contentTitle
        # Complete list of options for this type of content
        list_opciones_cuadro.append(scrapers_disponibles['tmdb'])

    else:
        scraper_actual = 'tmdb'
        # scraper_actual = ['tmdb', 'tvdb'][config.get_setting("scraper_tvshows", "videolibrary")]
        tipo_contenido = "serie"
        title = item.contentSerieName
        # Complete list of options for this type of content
        list_opciones_cuadro.append(scrapers_disponibles['tmdb'])
        # list_opciones_cuadro.append(scrapers_disponibles['tvdb'])

    # We import the scraper
    try:
        scraper = __import__('core.%s' % scraper_actual, fromlist=["core.%s" % scraper_actual])
    except ImportError:
        exec("import core." + scraper_actual + " as scraper")
    except:
        import traceback
        logger.error(traceback.format_exc())

    while scraper:
        # We call the find_and_set_infoLabels function of the selected scraper
        scraper_result = scraper.find_and_set_infoLabels(item)

        # Check if there is a 'code'
        if scraper_result and item.infoLabels['code']:
            # correct code
            logger.debug("Identificador encontrado: %s" % item.infoLabels['code'])
            scraper.completar_codigos(item)
            return True
        elif scraper_result:
            # Content found but no 'code'
            msg = config.get_localized_string(60227) % title
        else:
            # Content not found
            msg = config.get_localized_string(60228) % title

        logger.debug(msg)
        # Show box with other options:
        item = platformtools.dialog_info(item, scraper_actual)
        if item.exit:
            logger.debug("You have clicked 'cancel' in the window '%s'" % msg)
            return False

    logger.error("Error importing the scraper module %s" % scraper_actual)


def cuadro_completar(item):
    logger.debug()

    global dict_default
    dict_default = {}

    COLOR = ["0xFF65B3DA", "0xFFFFFFFF"]
    # We create the list of infoLabel fields
    controls = [("title", "text", config.get_localized_string(60230)),
                ("originaltitle", "text", config.get_localized_string(60231)),
                ("year", "text", config.get_localized_string(60232)),
                ("identificadores", "label", config.get_localized_string(60233)),
                ("tmdb_id", "text", config.get_localized_string(60234)),
                ("url_tmdb", "text", config.get_localized_string(60235), "+!eq(-1,'')"),
                ("tvdb_id", "text", config.get_localized_string(60236), "+eq(-7,'Serie')"),
                ("url_tvdb", "text", config.get_localized_string(60237), "+!eq(-1,'')+eq(-8,'Serie')"),
                ("imdb_id", "text", config.get_localized_string(60238)),
                ("otro_id", "text", config.get_localized_string(60239), "+eq(-1,'')"),
                ("urls", "label", config.get_localized_string(60240)),
                ("fanart", "text", config.get_localized_string(60241)),
                ("thumbnail", "text", config.get_localized_string(60242))]

    if item.infoLabels["mediatype"] == "movie":
        mediatype_default = 0
    else:
        mediatype_default = 1

    listado_controles = [{'id': "mediatype",
                          'type': "list",
                          'label': config.get_localized_string(60243),
                          'color': COLOR[1],
                          'default': mediatype_default,
                          'enabled': True,
                          'visible': True,
                          'lvalues': [config.get_localized_string(60244), config.get_localized_string(70136)]
                          }]

    for i, c in enumerate(controls):
        color = COLOR[0]
        dict_default[c[0]] = item.infoLabels.get(c[0], '')

        enabled = True

        if i > 0 and c[1] != 'label':
            color = COLOR[1]
            enabled = "!eq(-%s,'')" % i
            if len(c) > 3:
                enabled += c[3]

        # default for special cases
        if c[0] == "url_tmdb" and item.infoLabels["tmdb_id"] and 'tmdb' in item.infoLabels["url_scraper"]:
            dict_default[c[0]] = item.infoLabels["url_scraper"]

        elif c[0] == "url_tvdb" and item.infoLabels["tvdb_id"] and 'thetvdb.com' in item.infoLabels["url_scraper"]:
            dict_default[c[0]] = item.infoLabels["url_scraper"]

        if not dict_default[c[0]] or dict_default[c[0]] == 'None' or dict_default[c[0]] == 0:
            dict_default[c[0]] = ''
        elif isinstance(dict_default[c[0]], (int, float)) or (not PY3 and isinstance(dict_default[c[0]], (int, float, long))):
            # If it is numerical we convert it into str
            dict_default[c[0]] = str(dict_default[c[0]])

        listado_controles.append({'id': c[0],
                                  'type': c[1],
                                  'label': c[2],
                                  'color': color,
                                  'default': dict_default[c[0]],
                                  'enabled': enabled,
                                  'visible': True})

    # logger.debug(dict_default)
    if platformtools.show_channel_settings(list_controls=listado_controles, caption=config.get_localized_string(60246), item=item,
                                           callback="core.scraper.callback_cuadro_completar",
                                           custom_button={"visible": False}):
        return True

    else:
        return False


def callback_cuadro_completar(item, dict_values):
    # logger.debug(dict_values)
    global dict_default

    if dict_values.get("title", None):
        # Adapt dict_values ​​to valid infoLabels
        dict_values['mediatype'] = ['movie', 'tvshow'][dict_values['mediatype']]
        for k, v in list(dict_values.items()):
            if k in dict_default and dict_default[k] == dict_values[k]:
                del dict_values[k]

        if isinstance(item.infoLabels, InfoLabels):
            infoLabels = item.infoLabels
        else:
            infoLabels = InfoLabels()

        infoLabels.update(dict_values)
        item.infoLabels = infoLabels

        if item.infoLabels['code']:
            return True

    return False


def get_nfo(item, search_groups=False):
    """
    Returns the information necessary for the result to be scraped into the kodi video library,

    @param item: element that contains the data necessary to generate the info
    @type item: Item
    @rtype: str
    @return:
    """
    logger.debug()
    if "infoLabels" in item and "noscrap_id" in item.infoLabels:
        # Create the xml file with the data obtained from the item since there is no active scraper
        info_nfo = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'

        if "season" in item.infoLabels and "episode" in item.infoLabels:
            info_nfo += '<episodedetails><title>%s</title>' % item.infoLabels['title']
            info_nfo += '<showtitle>%s</showtitle>' % item.infoLabels['tvshowtitle']
            info_nfo += '<thumb>%s</thumb>' % item.thumbnail

            info_nfo += '</episodedetails>\n'

        elif item.infoLabels["mediatype"] == "tvshow":
            info_nfo += '<tvshow><title>%s</title>' % item.infoLabels['title']
            info_nfo += '<thumb aspect="poster">%s</thumb>' % item.thumbnail
            info_nfo += '<fanart><thumb>%s</thumb></fanart>' % item.fanart

            info_nfo += '</tvshow>\n'

        else:
            info_nfo += '<movie><title>%s</title>' % item.infoLabels['title']
            info_nfo += '<thumb aspect="poster">%s</thumb>' % item.thumbnail
            info_nfo += '<fanart><thumb>%s</thumb></fanart>' % item.fanart

            info_nfo += '</movie>\n'

        return info_nfo
    else:
        try: return scraper.get_nfo(item)
        except:
            if item.contentType == "movie": scraper_actual = ['tmdb'][config.get_setting("scraper_movies", "videolibrary")]
            else: scraper_actual = ['tmdb', 'tvdb'][config.get_setting("scraper_tvshows", "videolibrary")]
            scraper = __import__('core.%s' % scraper_actual, fromlist=["core.%s" % scraper_actual])
            return scraper.get_nfo(item, search_groups)


def sort_episode_list(episodelist):
    scraper_actual = ['tmdb', 'tvdb'][config.get_setting("scraper_tvshows", "videolibrary")]

    if scraper_actual == "tmdb":
        episodelist.sort(key=lambda e: (int(e.contentSeason), int(e.contentEpisodeNumber)))

    elif scraper_actual == "tvdb":
        episodelist.sort(key=lambda e: (int(e.contentEpisodeNumber), int(e.contentSeason)))

    return episodelist
