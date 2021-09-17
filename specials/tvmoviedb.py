# -*- coding: utf-8 -*-
from platformcode.platformtools import calcResolution
from core.item import Item
import re
from core import filetools, jsontools, trakt_tools
from core import support, tmdb
from core.tmdb import Tmdb
from core.scrapertools import htmlclean, decodeHtmlentities
from core.support import nextPage, thumb, typo, match, dbg
from platformcode import config, logger, platformtools


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
    itemlist = [item.clone(title='TMDB', action='tmdbMenu', thumbnail=support.thumb('tmdb')),
                item.clone(title='IMDB', action='imdbMenu', thumbnail=support.thumb('imdb'))]
    itemlist += [item.clone(title=config.get_localized_string(70415), action='trakt', thumbnail=support.thumb('trakt')),
                 item.clone(title=config.get_localized_string(70026), action='mal', thumbnail=support.thumb('mal')),
                 item.clone(title=typo(config.get_localized_string(70027), 'bold'), action='configuracion', folder=False, thumbnail=support.thumb('setting'))]
    return itemlist



def tmdbMenu(item):
    if not item.args:
        return thumb([item.clone(title=config.get_localized_string(70741) % config.get_localized_string(30122), args='movie'),
                item.clone(title=config.get_localized_string(70741) % config.get_localized_string(30123), args='tv')])

    item.contentType = item.args.replace('tv', 'tvshow')

    itemlist = [item.clone(title=config.get_localized_string(70028), action='tmdbResults', args=item.args + '/popular'),
                item.clone(title=config.get_localized_string(70029), action='tmdbResults', args=item.args + '/top_rated'),
                item.clone(title=config.get_localized_string(50001), action='tmdbResults', args=item.args + '/now_playing' if item.args == 'movie' else '/on_the_air'),
                item.clone(title=config.get_localized_string(70032), action='tmdbIndex', mode='genre'),
                item.clone(title=config.get_localized_string(70042), action='tmdbIndex', mode='year')]

    if item.args == 'movie':
        itemlist.extend([item.clone(title=config.get_localized_string(70033), action='tmdbResults', args='person/popular'),
                         item.clone(title=config.get_localized_string(70034), action='tmdbResults', args=item.args + '/upcoming')])


    itemlist.extend([item.clone(title=config.get_localized_string(70035) % config.get_localized_string(60244 if item.args == 'movie' else 60245).lower(), action='_search', search={'url': 'search/%s' % item.args, 'language': lang.tmdb, 'page': 1}),
                     item.clone(title=config.get_localized_string(70036), action='_search', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1})])

    if item.args == 'movie': itemlist.append(item.clone(title=config.get_localized_string(70037), action='_search', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1}, crew=True))

    itemlist.extend([item.clone(title=typo(config.get_localized_string(70038),'bold'), action='filter', ),
                     item.clone(title=typo(config.get_localized_string(70039),'bold'), action='filter', )])

    return thumb(itemlist)


def tmdbResults(item):
    itemlist = []
    if not item.page: item.page = 1
    _search = item.search if item.search else {'url': item.args, 'language': lang.tmdb, 'page': item.page}
    obj = tmdb.discovery(item, _search)

    for result in obj.results:
        if 'person' in _search['url']:
            it = item.clone(action='showCast', channel='infoplus', folder=False)
            it.id = result.get('id')
        else:
            it = item.clone(action='start', channel='infoplus', folder=False)
        it.infoLabels = obj.get_infoLabels(it.infoLabels, origen=result)
        for k in ['title', 'thumbnail', 'fanart']:
            it.__setattr__(k, it.infoLabels.get(k))
        itemlist.append(it)

    if item.page < obj.total_pages:
        support.nextPage(itemlist, item, 'peliculas', page=item.page + 1, total_pages=obj.total_pages)
    return itemlist

def tmdbIndex(item):
    itemlist = []
    from datetime import datetime
    if item.mode == 'genre':
        url = '{}/{}/list?api_key={}&language={}'.format(tmdb.host, item.mode, tmdb.api, lang.tmdb)
        genres = match(url, cookies=False).response.json['genres']

        date = datetime.now().strftime('%Y-%m-%d')
        sort_by = 'release_date.desc'
        param_year = 'release_date.lte'
        if item.contentType == 'tvshow':
            sort_by = 'first_air_date.desc'
            param_year = 'air_date.lte'
        for genre in genres:
            search = {'url': 'discover/{}'.format(item.args), 'with_genres': genre['id'], 'sort_by': sort_by, param_year: date,'language': lang.tmdb, 'page': 1}
            new_item = item.clone(title=genre['name'], action='tmdbResults', search=search, mode='')
            itemlist.append(new_item)

        itemlist.sort(key=lambda item: item.title)
        thumb(itemlist, mode='genre')
    else:
        year = datetime.now().year + 3
        for i in range(year, 1899, -1):
            if item.contentType == 'tvshow':
                param_year = 'first_air_date_year'
            else:
                param_year = 'primary_release_year'
            search = {'url': 'discover/{}'.format(item.args), param_year: i, 'language': lang.tmdb, 'page': 1}
            itemlist.append(item.clone(title=str(i), action='tmdbResults', search=search))

    return itemlist

def _search(item):
    text = platformtools.dialog_input(heading=item.title)
    if text:
        item.search['query'] = text
        return tmdbResults(item)



############################################################

def filter(item):
    logger.debug()

    from datetime import datetime
    list_controls = []
    valores = {}

    dict_values = None

    list_controls.append({'id': 'years', 'label': config.get_localized_string(60232), 'enabled': True, 'type': 'list', 'default': -1, 'visible': True})
    list_controls[0]['lvalues'] = []
    valores['years'] = []
    year = datetime.now().year + 1
    for i in range(1900, year + 1):
        list_controls[0]['lvalues'].append(str(i))
        valores['years'].append(str(i))
    list_controls[0]['lvalues'].append(config.get_localized_string(70450))
    valores['years'].append('')

    if config.get_localized_string(70038) in item.title:
        # Se utilizan los valores por defecto/guardados
        saved_values = config.get_setting("default_filter_" + item.args, item.channel)
        if saved_values:
            dict_values = saved_values
        # dbg()
        url = '{}/genre/{}/list?api_key={}&language={}'.format(tmdb.host, item.args, tmdb.api, lang.tmdb)
        # try:
        lista = support.match(url, cookies=False).response.json["genres"]
        if lista:
            list_controls.append({'id': 'labelgenre', 'enabled': True, 'type': 'label', 'default': None, 'label': config.get_localized_string(70451), 'visible': True})
            for l in lista:
                list_controls.append({'id': 'genre' + str(l["id"]), 'label': l["name"], 'enabled': True, 'type': 'bool', 'default': False, 'visible': True})
        # except:
        #     pass

        list_controls.append({'id': 'orden', 'label': config.get_localized_string(70455), 'enabled': True, 'type': 'list', 'default': -1, 'visible': True})
        orden = [config.get_localized_string(70456), config.get_localized_string(70457), config.get_localized_string(70458), config.get_localized_string(70459), config.get_localized_string(70460), config.get_localized_string(70461)]
        if item.args == "movie":
            orden.extend([config.get_localized_string(70462), config.get_localized_string(70463)])
        orden_tmdb = ['popularity.desc', 'popularity.asc', 'release_date.desc', 'release_date.asc', 'vote_average.desc', 'vote_average.asc', 'original_title.asc', 'original_title.desc']
        valores['orden'] = []
        list_controls[-1]['lvalues'] = []
        for i, tipo_orden in enumerate(orden):
            list_controls[-1]['lvalues'].insert(0, tipo_orden)
            valores['orden'].insert(0, orden_tmdb[i])

        list_controls.append({'id': 'espacio', 'label': '', 'enabled': False, 'type': 'label', 'default': None, 'visible': True})
        list_controls.append({'id': 'save', 'label': config.get_localized_string(70464), 'enabled': True, 'type': 'bool', 'default': False, 'visible': True})
    else:
        list_controls.append({'id': 'keyword', 'label': config.get_localized_string(70465), 'enabled': True, 'type': 'text', 'default': '', 'visible': True})

    item.valores = valores
    return platformtools.show_channel_settings(list_controls=list_controls, dict_values=dict_values, caption=config.get_localized_string(70320), item=item, callback='filtered')

def filtered(item, values):
    values_copy = values.copy()
    # Save the filter to be the one loaded by default
    if "save" in values and values["save"]:
        values_copy.pop("save")
        config.set_setting("default_filter_" + item.args, values_copy, item.channel)

    year = item.valores["years"][values["years"]]
    if config.get_localized_string(70038) in item.title:
        orden = item.valores["orden"][values["orden"]]
        if item.args == "tv": orden = orden.replace('release_date', 'first_air_date')

        genre_ids = []
        for v in values:
            if "genre" in v:
                if values[v]: genre_ids.append(v.replace('genre', ''))
        genre_ids = ",".join(genre_ids)

    if config.get_localized_string(70465).lower() in item.title.lower(): item.search = {'url': 'search/%s' % item.args, 'year': year, 'query': values["keyword"], 'language': lang.tmdb, 'page': 1}
    elif item.args == "movie": item.search = {'url': 'discover/%s' % item.args, 'sort_by': orden, 'primary_release_year': year, 'with_genres': genre_ids, 'vote_count.gte': '10', 'language': lang.tmdb, 'page': 1}
    else: item.search = {'url': 'discover/%s' % item.args, 'sort_by': orden, 'first_air_date_year': year, 'with_genres': genre_ids, 'vote_count.gte': '10', 'language': lang.tmdb, 'page': 1}

    item.action = "list_tmdb"
    return tmdbResults(item)