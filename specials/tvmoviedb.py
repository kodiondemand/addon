# -*- coding: utf-8 -*-
from platformcode.platformtools import calcResolution
from core.item import Item
import re
from core import filetools, jsontools, trakt_tools
from core import support, tmdb
from core.tmdb import Tmdb
from core.scrapertools import htmlclean, decodeHtmlentities
from core.support import thumb, typo, match, dbg
from platformcode import config, logger


langs = Item(tmdb=[tmdb.def_lang, 'de', 'fr', 'pt', 'it', 'es-MX', 'ca', 'en', 'es'],
             imdb=[tmdb.def_lang, 'de-de', 'fr-fr', 'pt-pt', 'it-it', 'es-MX', 'ca-es', 'en', 'es'])
lang = Item(tmdb=langs.tmdb[config.get_setting('tmdb', 'tvmoviedb')],
            tmdbfallback= langs.tmdb[config.get_setting('tmdbfallback', 'tvmoviedb')],
            imdb=langs.imdb[config.get_setting('imdb', 'tvmoviedb')])


mal_adult = config.get_setting('adult_mal', 'tvmoviedb')
mal_key = 'MzE1MDQ2cGQ5N2llYTY4Z2xwbGVzZjFzbTY='
# fanart = filetools.join(config.get_runtime_path(), re 'fanart.jpg')


def mainlist(item):
    logger.debug()
    itemlist = [item.clone(title='TMDB', action='tmdb_menu'),
                item.clone(title='IMDB', action='imdb_menu')]
    # itemlist = [item.clone(title=config.get_localized_string(70021) % (config.get_localized_string(30122), 'TMDB'), action='tmdb_menu', args='movie'),
    #             item.clone(title=config.get_localized_string(70021) % (config.get_localized_string(30123), 'TMDB'), action='tmdb_menu', args='tv'),
    #             item.clone(title=config.get_localized_string(70021) % (config.get_localized_string(30122), 'IMDB'), action='imdb', args='movie', url='&title_type=feature,tv_movie'),
    #             item.clone(title=config.get_localized_string(70021) % (config.get_localized_string(30123), 'IMDB'), action='imdb', args='tv', url='&title_type=tv_series,tv_special,mini_series')]
    support.thumb(itemlist)
    itemlist += [item.clone(title=config.get_localized_string(70415), action='trakt', thumbnail=support.thumb('trakt')),
                 item.clone(title=config.get_localized_string(70026), action='mal', thumbnail=support.thumb('mal')),
                 item.clone(title=typo(config.get_localized_string(70027), 'bold'), action='configuracion', folder=False, thumbnail=support.thumb('setting'))]
    return itemlist



def tmdb_menu(item):
    if not item.args:
        return [item.clone(title=config.get_localized_string(70741) % config.get_localized_string(30122), args='movie'),
                item.clone(title=config.get_localized_string(70741) % config.get_localized_string(30123), args='tv')]

    item.contentType = item.args.replace('tv', 'tvshow')

    itemlist = [item.clone(title=config.get_localized_string(70028), action='peliculas', args=item.args + '/popular'),
                item.clone(title=config.get_localized_string(70029), action='peliculas', args=item.args + '/top_rated'),
                item.clone(title=config.get_localized_string(50001), action='peliculas', args=item.args + '/now_playing' if item.args == 'movie' else '/on_the_air'),
                item.clone(title=config.get_localized_string(70032), action='indices_tmdb'),
                item.clone(title=config.get_localized_string(70042), action='indices_tmdb')]

    if item.args == 'movie':
        itemlist.extend([item.clone(title=config.get_localized_string(70033), action='peliculas', args='person/popular'),
                         item.clone(title=config.get_localized_string(70034), action='list_tmdb', args=item.args + '/upcoming')])


    itemlist.extend([item.clone(title=config.get_localized_string(70035) % config.get_localized_string(60244 if item.args == 'movie' else 60245).lower(), action='search_', search={'url': 'search/%s' % item.args, 'language': lang.tmdb, 'page': 1}),
                     item.clone(title=config.get_localized_string(70036), action='search_', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1})])

    if item.args == 'movie': itemlist.append(item.clone(title=config.get_localized_string(70037), action='search_', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1}, crew=True))

    itemlist.extend([item.clone(title=typo(config.get_localized_string(70038),'bold'), action='filter', ),
                     item.clone(title=typo(config.get_localized_string(70039),'bold'), action='filter', )])

    return thumb(itemlist)

def peliculas(item):
    itemlist = []
    _search = {'url': item.args, 'language': lang.tmdb, 'page': item.page if item.page else 1}
    obj = tmdb.discovery(item, _search)

    for result in obj.results:
        if 'person' in item.args:
            it = item.clone(action='showCast', channel='infoplus', folder=False)
            it.id = result.get('id')
        else:
            it = item.clone(action='start', channel='infoplus', folder=False)
        it.infoLabels = obj.get_infoLabels(it.infoLabels, origen=result)
        for k in ['title', 'thumbnail', 'fanart']:
            it.__setattr__(k, it.infoLabels.get(k))
        itemlist.append(it)
    return itemlist
