# -*- coding: utf-8 -*-
from typing import OrderedDict
from core.item import InfoLabels, Item
import re
from core import httptools, trakt_tools, tmdb, support, jsontools
from platformcode import config, logger, platformtools
from datetime import datetime


langs = Item(tmdb=[tmdb.def_lang, 'de', 'fr', 'pt', 'it', 'es-MX', 'ca', 'en', 'es'],
             imdb=[tmdb.def_lang, 'de-de', 'fr-fr', 'pt-pt', 'it-it', 'es-MX', 'ca-es', 'en', 'es'])
lang = Item(tmdb=langs.tmdb[config.get_setting('tmdb', 'tvmoviedb')],
            tmdbfallback= langs.tmdb[config.get_setting('tmdbfallback', 'tvmoviedb')],
            imdb=langs.imdb[config.get_setting('imdb', 'tvmoviedb')])

imdb_host = 'http://www.imdb.com'
mal_adult = config.get_setting('adult_mal', 'tvmoviedb')
mal_key = 'MzE1MDQ2cGQ5N2llYTY4Z2xwbGVzZjFzbTY='
# fanart = filetools.join(config.get_runtime_path(), re 'fanart.jpg')


def mainlist(item):
    logger.debug()
    itemlist = [item.clone(title='TMDB', action='tmdbMenu', thumbnail=support.thumb('tmdb')),
                item.clone(title='IMDB', action='imdbMenu', thumbnail=support.thumb('imdb'))]
    itemlist += [item.clone(title=config.get_localized_string(70415), action='traktMenu', thumbnail=support.thumb('trakt')),
                 item.clone(title=config.get_localized_string(70026), action='mal', thumbnail=support.thumb('mal')),
                 item.clone(title=support.typo(config.get_localized_string(70027), 'bold'), action='configuracion', folder=False, thumbnail=support.thumb('setting'))]
    return itemlist


def _search(item):
    text = platformtools.dialog_input(heading=item.title)
    if text:
        if item.search:
            item.search['query'] = text
            return tmdbResults(item)
        else:
            item.url = item.url.format(text)
            return imdbResults(item)

########## TMDB ##########

def tmdbMenu(item):
    if not item.args:
        return support.thumb([item.clone(title=config.get_localized_string(30122), args='movie'),
                item.clone(title=config.get_localized_string(30123), args='tv'),
                item.clone(title=config.get_localized_string(70033), action='tmdbResults', args='person/popular'),
                item.clone(title=config.get_localized_string(70036), action='_search', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1}),
                item.clone(title=config.get_localized_string(70037), action='_search', search={'url': 'search/person', 'language': lang.tmdb, 'page': 1}, crew=True)])

    item.contentType = item.args.replace('tv', 'tvshow')

    itemlist = [item.clone(title=config.get_localized_string(70028), action='tmdbResults', args=item.args + '/popular'),
                item.clone(title=config.get_localized_string(70029), action='tmdbResults', args=item.args + '/top_rated'),
                item.clone(title=config.get_localized_string(50001), action='tmdbResults', args=item.args + '/now_playing' if item.args == 'movie' else 'tv/on_the_air'),
                item.clone(title=config.get_localized_string(70032), action='tmdbIndex', mode='genre'),
                item.clone(title=config.get_localized_string(70042), action='tmdbIndex', mode='year')]


    itemlist.extend([item.clone(title=config.get_localized_string(70035) % config.get_localized_string(60244 if item.args == 'movie' else 60245).lower(), action='_search', search={'url': 'search/%s' % item.args, 'language': lang.tmdb, 'page': 1}),
                     item.clone(title=support.typo(config.get_localized_string(70038),'bold'), action='filter', db_type='tmdb' )])


    return support.thumb(itemlist)


def tmdbResults(item):
    itemlist = []
    logger.dbg()
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
        support.nextPage(itemlist, item, 'tmdbResults', page=item.page + 1, total_pages=obj.total_pages)
    return itemlist


def tmdbIndex(item):
    itemlist = []

    if item.mode == 'genre':
        url = '{}/{}/list?api_key={}&language={}'.format(tmdb.host, item.mode, tmdb.api, lang.tmdb)
        genres = support.match(url, cookies=False).response.json['genres']

        date = datetime.now().strftime('%Y-%m-%d')
        sort_by = 'first_air_date.desc' if item.contentType == 'tvshow' else 'release_date.desc'
        param_year = 'air_date.lte' if item.contentType == 'tvshow' else 'release_date.lte'
        for genre in genres:
            search = {'url': 'discover/{}'.format(item.args), 'with_genres': genre['id'], 'sort_by': sort_by, param_year: date,'language': lang.tmdb, 'page': 1}
            new_item = item.clone(title=genre['name'], action='tmdbResults', search=search, mode='')
            itemlist.append(new_item)

        itemlist.sort(key=lambda item: item.title)
        support.thumb(itemlist, mode='genre')
    else:
        year = datetime.now().year + 3
        for i in range(year, 1899, -1):
            param_year = 'first_air_date_year' if item.contentType == 'tvshow' else 'primary_release_year'
            search = {'url': 'discover/{}'.format(item.args), param_year: i, 'language': lang.tmdb, 'page': 1}
            itemlist.append(item.clone(title=str(i), action='tmdbResults', search=search))

    return itemlist


########## IMDB ##########

def imdbMenu(item):
    itemlist = []
    if not item.args:
        itemlist.extend([item.clone(title=config.get_localized_string(30122), args='movie'),
                         item.clone(title=config.get_localized_string(30123), args='tvshow'),
                         item.clone(title=config.get_localized_string(70033), action='imdbResults', args=['actors']),
                         item.clone(title=config.get_localized_string(70036), action='_search', url='/search/name?name={}', args=['actors']),
                         item.clone(title=config.get_localized_string(30980), action='_search', url= '/search/title?title={}')])
    else:
        item.contentType = item.args

        itemlist.append(item.clone(title=config.get_localized_string(70028), action='imdbResults', args=[item.contentType]))
        itemlist.append(item.clone(title=config.get_localized_string(70029), action='imdbResults', args=[item.contentType,'top']))
        if item.contentType == 'movie':
            itemlist.extend([item.clone(title=config.get_localized_string(70030), action='imdbResults', args=['cinema']),
                            item.clone(title=config.get_localized_string(70034), action='imdbResults', args=['soon'])])

        itemlist.extend([item.clone(title=config.get_localized_string(70032), action='imdbIndex', args='genre'),
                         item.clone(title=config.get_localized_string(70042), action='imdbIndex', args='year'),
                         item.clone(title=support.typo(config.get_localized_string(70038),'color kod'), action='filter', db_type='imdb')])

    return support.thumb(itemlist)


def imdbResults(item):
    itemlist = []

    params = {'movie':'/search/title?&title_type=feature,tv_movie',
              'tvshow':'/search/title?&title_type=tv_series,tv_special,mini_series',
              'top':'&num_votes=25000,&sort=user_rating,desc',
              'cinema':'/showtimes/location?ref_=inth_ov_sh_sm',
              'actors': '/search/name?gender=male,female&ref_=nv_cel_m_3',
              'soon': '/movies-coming-soon/?ref_=shlc_cs'}

    if item.search: item.url = imdb_host + params[item.contentType] + '&' + support.urlencode(item.search)
    elif not item.url: item.url = imdb_host + ''.join(params[a] for a in item.args)
    else: item.url = imdb_host + item.url
    if item.prevthumb: item.thumbnail = item.prevthumb
    if 'actors' in item.args:
        data = support.match(item.url, patron=r'nm\d+[^>]*>\s*<img alt="([^"]+)" height="\d+" src="([^"]+)')
        for title, thumb in data.matches:
            item.thumbnail = thumb.split('._V1_')[0] + '._V1_UX482.jpg' if thumb else thumb
            itemlist.append(item.clone(title=title, action='showCast', channel='infoplus', text=title, folder=False))
    else:
        data = support.match(item.url, patron=r'"(?:image|lister-item-image)[^>]+>\s*<a href="/[^/]+/(tt\d+)/[^>]+>.*?<img.*?alt="([^"]+)" (?:class|title)="[^"]+" (?:loadlate|src)="([^"]+)', debug=True)

        for imdb_id, title, thumb in data.matches:
            item.infoLabels['imdb_id'] = imdb_id
            item.thumbnail = thumb.split('@')[0] + '@._UX482.jpg' if thumb else thumb
            itemlist.append(item.clone(title=title.split('(')[0], action='start', channel='infoplus', folder=False))
        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.nextPage(itemlist, item,  data=data.data, patron=r'<a href="([^"]+)"[^>]*>Next')
    return itemlist


def imdbIndex(item):
    itemlist = []
    params = {'movie':'&title_type=feature,tv_movie',
              'tvshow':'&title_type=tv_series,tv_special,mini_series',}
    item.action = 'imdbResults'
    url = '/search/title'
    if item.args == 'genre':
        matches = support.match(imdb_host + url, patronBlock=r'<h3>Genres</h3>(.*?)</table>', patron=r' value="([^"]+)"\s*>\s*<label.*?>([^<]+)<').matches
        if matches:
            itemlist = [item.clone(title=title, url='{}?genres={}{}'.format(url, value, params[item.contentType]))for value, title in matches]
        support.thumb(itemlist, mode='genre')
    elif item.args == 'year':
        year = datetime.now().year + 3
        for i in range(year, 1899, -1):
            itemlist.append(item.clone(title=str(i), url='{}?release_date={}{}'.format(url, i, params[item.contentType])))
    return itemlist


########## TRAKT ##########

def traktMenu(item):
    itemlist = []
    token_auth = config.get_setting("token_trakt", "trakt")
    if not item.args:
        itemlist.extend([item.clone(title=config.get_localized_string(30122), args='movies'),
                         item.clone(title=config.get_localized_string(30123), args='shows')])
        if token_auth: itemlist.append(item.clone(title=support.typo(config.get_localized_string(70057), 'bold'), action="traktResults", url="/users/me/lists"))
        else: itemlist.append(item.clone(title=support.typo(config.get_localized_string(70054), 'bold'), action="traktAuth", folder=False))
    else:
        item.contentType = item.args.replace('shows', 'tvshow').replace('movies', 'movie')
        item.title = config.get_localized_string(30122 if item.contentType == 'movie' else 30123)
        itemlist.extend([item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70049)), action='traktResults', url= item.args + '/popular'),
                        item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70050)), action='traktResults', url= item.args + '/trending'),
                        item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70053)), action='traktResults', url= item.args + '/watched/all'),
                        item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70051)), action='traktResults', url= item.args + '/anticipated')])
        if token_auth:
            itemlist.extend([item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70052)), action='traktResults', url='/recommendations/' + item.args),
                             item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70055)), action='traktResults', url='/users/me/watchlist/' + item.args),
                             item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70056)), action='traktResults', url='/users/me/watched/' + item.args),
                             item.clone(title='{} [{}]'.format(item.title, config.get_localized_string(70068)), action='traktResults', url='/users/me/collection/' + item.args)])
    return itemlist


def traktResults(item):
    prepage = config.get_setting('pagination', default=20)
    if not item.page: item.page = 1
    if item.itemlist:
        itemlist = support.pagination(support.itemlistdb(), item, 'traktResults')
        tmdb.set_infoLabels_itemlist(itemlist, True)
        return itemlist

    if item.prevthumb: item.thumbnail = item.prevthumb
    token_auth = config.get_setting('token_trakt', 'trakt')
    itemlist = []
    client_id = trakt_tools.client_id
    headers = [['Content-Type', 'application/json'], ['trakt-api-key', client_id], ['trakt-api-version', '2']]
    if token_auth: headers.append(['Authorization', 'Bearer {}'.format(token_auth)])

    post = None
    if item.post: post = jsontools.dump(item.post)

    url = '{}{}?page={}&limit=20&extended=full'.format(trakt_tools.host, item.url, item.page) 

    data = httptools.downloadpage(url, post=post, headers=headers)
    if data.code == '401':
        trakt_tools.token_trakt(item.clone(args='renew'))
        token_auth = config.get_setting('token_trakt', 'trakt')
        headers[3][1] = 'Bearer {}'.format(token_auth)
        data = httptools.downloadpage(url, post=post, headers=headers)


    data = data.json

    if data and 'recommendations' in item.url:
        ratings = []

        for i, entry in enumerate(data):
            new_item = item.clone(action='start',
                                  channel='infoplus',
                                  folder=False,
                                  title = entry['title'])
            new_item.infoLabels['tmdb_id'] = entry['ids']['tmdb']
            try: ratings.append(entry['rating'])
            except: ratings.append(0.0)
            itemlist.append(new_item)


        tmdb.set_infoLabels_itemlist(itemlist, True)
        for i, new_item in enumerate(itemlist):
            if new_item.infoLabels['title']: new_item.title = new_item.infoLabels['title']
        if len(itemlist) == prepage:
            support.nextPage(itemlist, item, 'traktResults', page=item.page + 1)


    elif data and not item.url.endswith('lists'):
        ratings = []
        try:
            for entry in data:
                logger.debug(jsontools.dump(entry))
                new_item = item.clone(action='start', channel='infoplus', folder=False)
                if 'show' in entry:
                    entry = entry['show']
                    new_item.contentType = 'tvshow'
                elif 'movie' in entry:
                    entry = entry['movie']
                    new_item.contentType = 'movie'

                new_item.title = entry['title']
                new_item.infoLabels['tmdb_id'] = entry['ids']['tmdb']
                try: ratings.append(entry['rating'])
                except: ratings.append('')
                itemlist.append(new_item)

            if len(itemlist) > prepage:
                itemlist= support.pagination(itemlist, item, 'traktResults')
            elif len(itemlist) == prepage:
                support.nextPage(itemlist, item, 'traktResults', page=item.page + 1, total_pages=item.total_pages)

            tmdb.set_infoLabels_itemlist(itemlist, True)
            for i, new_item in enumerate(itemlist):
                if new_item.infoLabels['title']: new_item.title = new_item.infoLabels['title']
                new_item.infoLabels['trakt_rating'] = ratings[i]


        except:
            import traceback
            logger.error(traceback.format_exc())

    else:
        for entry in data:
            new_item = item.clone()
            new_item.title = entry['name'] + support.typo(str(entry['item_count']),'color kod _ []')
            new_item.infoLabels['plot'] = entry.get('description')
            new_item.url = 'users/me/lists/{}/items/'.format(entry['ids']['trakt'])
            new_item.order = entry.get('sort_by')
            new_item.how = entry.get('sort_how')
            new_item.total_pages = int(entry['item_count'] / prepage)
            itemlist.append(new_item)

    return itemlist


def traktAuth(item):
    return trakt_tools.auth_trakt()




def filter(item):
    import xbmcgui
    orderTitle = [config.get_localized_string(70456), config.get_localized_string(70457), config.get_localized_string(70458), config.get_localized_string(70459), config.get_localized_string(70460), config.get_localized_string(70461), config.get_localized_string(70462), config.get_localized_string(70462)]
    tmdbOrder = ['popularity.desc', 'popularity.asc', 'release_date.desc', 'release_date.asc', 'vote_average.desc', 'vote_average.asc', 'title.asc', 'title.desc']
    imdbOrder = ['moviemeter,asc', 'moviemeter,desc', 'release_date,asc', 'release_date,desc', 'user_rating,asc', 'user_rating,desc', 'alpha,asc', 'alpha,desc']
    defControls = {'year':{'title': config.get_localized_string(60232), 'values': '', 'order':0},
                           'genre':{'title': config.get_localized_string(70032), 'values': '', 'order':1},
                           'rating':{'title': config.get_localized_string(70473), 'values': '', 'order':2},
                           'order': {'title': config.get_localized_string(70455), 'values': orderTitle[0], 'order':3}}

    controls = dict(sorted(config.get_setting('controls', item.channel, default=defControls).items(), key=lambda k: k[1]['order']))
    class Filter(xbmcgui.WindowXMLDialog):
        def start(self, item):
            self.item = item
            self.controls = controls
            self.order = tmdbOrder if item.db_type == 'tmdb' else imdbOrder
            self.doModal()
            if self.controls and self.controls['order']['values'] == orderTitle[0]: self.controls['order']['values'] = self.order[0]
            return self.controls

        def onInit(self):
            for n, v in enumerate(self.controls.values()):
                title = v['title']
                value = v['values']
                self.getControl(n + 100).setLabel('{}: {}'.format(title, value))

        def onClick(self, control):
            logger.debug('CONTROL', control)
            if control in [100]: # Year
                years = [str(i) for i in range(datetime.now().year + 3, 1899, -1)]
                selection = platformtools.dialog_select('', years)
                self.controls['year']['values'] = years[selection] if selection > -1 else ''
                self.getControl(100).setLabel('{}: {}'.format(self.controls['year']['title'], self.controls['year']['values']))
            elif control in [101]: # Genre
                genresIds = []
                genresNames = []
                # logger.dbg()
                if self.item.db_type == 'tmdb':
                    url = ('{}/genre/{}/list?api_key={}&language={}'.format(tmdb.host, item.args, tmdb.api, langs.tmdb))
                    genres = httptools.downloadpage(url).json['genres']
                    for genre in genres:
                        genresNames.append(genre['name'])
                        genresIds.append(str(genre['id']))
                else:
                    genres = support.match(imdb_host + '/search/title', patronBlock=r'<h3>Genres</h3>(.*?)</table>', patron=r' value="([^"]+)"\s*>\s*<label.*?>([^<]+)<').matches
                    for value, genre in genres:
                        genresNames.append(genre)
                        genresIds.append(value)
                selected = [genresIds.index(i.strip()) for i in self.controls['genre']['values'].split(',') if i]
                selections = platformtools.dialog_multiselect('', genresNames, preselect=selected)
                self.controls['genre']['values'] = ','.join(genresIds[g] for g in selections)
                names= ', '.join(genresNames[g] for g in selections)
                self.getControl(101).setLabel('{}: {}'.format(self.controls['genre']['title'], names))
            elif control in [102]:
                rating = [str(i) for i in range(1, 11)]
                selection = platformtools.dialog_select('', rating, preselect=rating.index(self.controls['rating']['values']) if self.controls['rating']['values'] else 0)
                self.controls['rating']['values'] = rating[selection]
                self.getControl(102).setLabel('{}: {}'.format(self.controls['rating']['title'], self.controls['rating']['values']))
            elif control in [103]:
                selection = platformtools.dialog_select('', orderTitle)
                if selection > -1:
                    self.controls['order']['values'] = self.order[selection]
                    self.getControl(103).setLabel('{}: {}'.format(self.controls['order']['title'], orderTitle[selection]))

            elif control in [200]:
                self.close()

            elif control in [201]:
                config.set_setting('controls', self.controls, self.item.channel)
                platformtools.dialog_notification('TMDB', 'Filtro salvato', time=1000, sound=False)

            elif control in [202]:
                config.set_setting('controls', defControls, self.item.channel)
                platformtools.dialog_notification('TMDB', 'Filtro eliminato', time=1000, sound=False)
                self.controls = None
                self.close()
                return filter(self.item)

            elif control in [203]:
                self.controls = None
                self.close()

        def onAction(self, action):
            action = action.getId()
            if action in [10,92]:
                self.controls = None
                self.close()


    controls = Filter('Filter.xml', config.get_runtime_path()).start(item)
    if controls:
        item.search = {'url': 'discover/' + item.args, 'vote_count.gte': 10} if item.db_type == 'tmdb' else {}

        params ={'year':{'tmdb':'first_air_date_year', 'imdb':'year'},
                 'genre':{'tmdb':'with_genres', 'imdb':'genres'},
                 'rating': {'tmdb':'vote_average.gte', 'imdb':'user_rating'},
                 'order': {'tmdb':'sort_by', 'imdb':'sort'}}

        for k, v in controls.items():
            k = params[k][item.db_type]
            v = v['values']
            if v:
                item.search[k] = v
        logger.debug(item.search)
        return tmdbResults(item) if item.db_type == tmdb else imdbResults(item)
