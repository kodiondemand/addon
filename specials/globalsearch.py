# -*- coding: utf-8 -*-

import xbmc, xbmcgui, sys, channelselector, time, os
from core.support import dbg, tmdb
from core.item import Item
from core import channeltools, servertools, scrapertools
from platformcode import platformtools, config, logger
from platformcode.launcher import run
from threading import Thread

if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]
close_action = False


def busy(state):
    if state: xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    else: xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

def set_workers():
    workers = config.get_setting('thread_number') if config.get_setting('thread_number') > 0 else None
    return workers

def Search(*args):
    w = SearchWindow('GlobalSearch.xml', config.get_runtime_path())
    w.start(*args)
    del w

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
ENTER = 7
EXIT = 10
BACKSPACE = 92
SWIPEUP = 531
CONTEXT = 117
MOUSEMOVE = 107
FULLSCREEN = 18

# Container
SEARCH = 1
EPISODES = 2
SERVERS = 3
NORESULTS = 4
LOADING = 5

# Search
MAINTITLE = 100
CHANNELS = 101
RESULTS = 102

PROGRESS = 500
COUNT = 501
MENU = 502
BACK = 503
CLOSE = 504
QUALITYTAG = 505

# Servers
EPISODESLIST = 200
SERVERLIST = 300

class SearchWindow(xbmcgui.WindowXML):
    def start(self, item, moduleDict={}, searchActions=[]):
        logger.debug()
        self.exit = False
        self.item = item
        self.type = self.item.mode
        self.channels = []
        self.persons = []
        self.episodes = []
        self.servers = []
        self.results = {}
        self.focus = SEARCH
        self.process = True
        self.page = 1
        self.moduleDict = moduleDict
        self.searchActions = searchActions
        self.thread = None
        self.selected = False
        self.pos = 0
        selfeppos = 0
        self.items = []

        if not searchActions:
            self.thActions = Thread(target=self.getActions)
            self.thActions.start()
        else:
            self.thActions = None

        self.lastSearch()
        if not self.item.text: return

        self.doModal()

    def lastSearch(self):
        logger.debug()
        if not self.item.text:
            if self.item.contentTitle:
                self.item.text = self.item.contentTitle
            elif self.item.contentSerieName:
                self.item.text = self.item.contentSerieName

            if not self.item.text:
                if config.get_setting('last_search'): last_search = channeltools.get_channel_setting('Last_searched', 'search', '')
                else: last_search = ''
                if not self.item.text: self.item.text = platformtools.dialog_input(default=last_search, heading='')
                if self.item.text:
                    channeltools.set_channel_setting('Last_searched', self.item.text, 'search')
                    from specials.search import save_search
                    save_search(self.item.text)

    def getActions(self):
        logger.debug()
        count = 0
        self.channelsList = self.get_channels()
        for channel in self.channelsList:
            self.getModule(channel)
            count += 1
            percent = (float(count) / len(self.channelsList)) * 100
            if self.thread or self.selected:  # window started
                self.PROGRESS.setPercent(percent)
                self.COUNT.setText('%s/%s' % (count, len(self.channelsList)))

    def select(self):
        logger.debug()
        self.PROGRESS.setVisible(False)
        self.items = []
        if self.item.mode == 'person_':
            tmdb_info = tmdb.discovery(self.item, dict_=self.item.discovery)
            results = tmdb_info.results.get('cast',[])
        else:
            tmdb_info = tmdb.Tmdb(texto_buscado=self.item.text, tipo=self.item.mode.replace('show', ''))
            results = tmdb_info.results

        for result in results:
            result = tmdb_info.get_infoLabels(result, origen=result)
            if self.item.mode == 'movie':
                title = result['title']
                result['mode'] = 'movie'
            else:
                title = result['name']
                result['mode'] = 'tvshow'

            thumbnail = result.get('thumbnail', '')
            noThumb = 'Infoplus/' + result['mode'].replace('show','') + '.png'
            fanart = result.get('fanart', '')
            year = result.get('release_date', '')
            rating = str(result.get('vote_average', ''))

            new_item = Item(channel='globalsearch',
                            action=True,
                            title=title,
                            thumbnail=thumbnail,
                            fanart=fanart,
                            mode='search',
                            type=result['mode'],
                            contentType=result['mode'],
                            text=title,
                            infoLabels=result)

            if self.item.mode == 'movie':
                new_item.contentTitle = result['title']
            else:
                new_item.contentSerieName = result['name']

            it = xbmcgui.ListItem(title)
            it.setProperties({'thumb': result.get('thumbnail', noThumb), 'fanart': result.get('fanart', ''), 'rating': '    [' + rating + ']' if rating else '',
                              'plot': result.get('overview', ''), 'search': 'search', 'release_date': '', 'item': new_item.tourl(),
                              'year': '   [' + year.split('/')[-1] + ']' if year else '    [' + result.get('first_air_date','').split('-')[0] + ']'})
            self.items.append(it)

        if self.items:
            self.RESULTS.reset()
            self.RESULTS.addItems(self.items)
            self.setFocusId(RESULTS)
        else:
            self.RESULTS.setVisible(False)
            self.NORESULTS.setVisible(True)
            self.setFocusId(CLOSE)

    def actors(self):
        logger.debug()
        self.PROGRESS.setVisible(False)
        items = []

        dict_ = {'url': 'search/person', 'language': def_lang, 'query': self.item.text, 'page':self.page}
        prof = {'Acting': 'Actor', 'Directing': 'Director', 'Production': 'Productor'}
        plot = ''
        self.item.search_type = 'person'
        tmdb_inf = tmdb.discovery(self.item, dict_=dict_)
        results = tmdb_inf.results

        for elem in results:
            name = elem.get('name', '')
            if not name: continue
            rol = elem.get('known_for_department', '')
            rol = prof.get(rol, rol)
            know_for = elem.get('known_for', '')
            cast_id = elem.get('id', '')
            if know_for:
                t_k = know_for[0].get('title', '')
                if t_k: plot = '%s in %s' % (rol, t_k)

            t = elem.get('profile_path', '')
            if t: thumb = 'https://image.tmdb.org/t/p/original' + t
            else : thumb = 'Infoplus/no_photo.png'

            discovery = {'url': 'person/%s/combined_credits' % cast_id, 'page': '1', 'sort_by': 'primary_release_date.desc', 'language': def_lang}
            self.persons.append(discovery)

            new_item = Item(channel='search',
                            action=True,
                            title=name,
                            thumbnail=thumb,
                            mode='search')

            it = xbmcgui.ListItem(name)
            it.setProperties({'thumb': thumb, 'plot': plot, 'search': 'persons', 'item': new_item.tourl()})
            items.append(it)
        if len(results) > 19:
            it = xbmcgui.ListItem(config.get_localized_string(70006))
            it.setProperty('thumb', 'Infoplus/next_focus.png')
            it.setProperty('search','next')
            items.append(it)
        if self.page > 1:
            it = xbmcgui.ListItem(config.get_localized_string(70005))
            it.setProperty('thumb', 'Infoplus/previous_focus.png')
            it.setProperty('search','previous')
            items.insert(0, it)

        if items:
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.setFocusId(RESULTS)
        else:
            self.RESULTS.setVisible(False)
            self.NORESULTS.setVisible(True)
            self.setFocusId(CLOSE)

    def get_channels(self):
        logger.debug()
        channels_list = []
        all_channels = channelselector.filterchannels('all')

        for ch in all_channels:
            channel = ch.channel
            ch_param = channeltools.get_channel_parameters(channel)
            if not ch_param.get("active", False):
                continue
            list_cat = ch_param.get("categories", [])

            if not ch_param.get("include_in_global_search", False):
                continue

            if 'anime' in list_cat:
                n = list_cat.index('anime')
                list_cat[n] = 'tvshow'

            if self.item.mode == 'all' or self.item.mode in list_cat or self.item.type in list_cat:
                if config.get_setting("include_in_global_search", channel) and ch_param.get("active", False):
                    channels_list.append(channel)

        logger.debug('search in channels:',channels_list)

        return channels_list

    def getModule(self, channel):
        logger.debug()
        try:
            module = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
            mainlist = getattr(module, 'mainlist')(Item(channel=channel, global_search=True))
            action = [elem for elem in mainlist if elem.action == "search" and (self.item.mode == 'all' or elem.contentType in [self.item.mode, 'undefined'])]
            self.moduleDict[channel] = module
            self.searchActions += action
        except:
            import traceback
            logger.error('error importing/getting search items of ' + channel)
            logger.error(traceback.format_exc())

    def timer(self):
        while self.searchActions:
            self.COUNT.setText('%s/%s [%s"]' % (self.count, len(self.searchActions), int(time.time() - self.time) ))
            time.sleep(1)

    def search(self):
        logger.debug()
        self.count = 0
        self.LOADING.setVisible(True)
        if self.thActions:
            self.thActions.join()
        Thread(target=self.timer).start()

        with futures.ThreadPoolExecutor(max_workers=set_workers()) as executor:
            for searchAction in self.searchActions:
                if self.exit: return
                executor.submit(self.get_channel_results, searchAction)
                logger.debug('end search for:', searchAction.channel)

    def get_channel_results(self, searchAction):
        logger.debug()
        channel = searchAction.channel
        results = []
        valid = []
        other = []

        try:
            results = self.moduleDict[channel].search(searchAction, self.item.text)
            if len(results) == 1:
                if not results[0].action or config.get_localized_string(70006).lower() in results[0].title.lower():
                    results = []

            if self.item.mode != 'all':
                for elem in results:
                    if elem.infoLabels['tmdb_id'] == self.item.infoLabels['tmdb_id']:
                        elem.from_channel = channel
                        elem.verified = 1
                        valid.append(elem)
                    else:
                        other.append(elem)
        except:
            pass

        self.count += 1
        return self.update(channel, valid, other if other else results)

    def makeItem(self, url):
        item = Item().fromurl(url)
        channelParams = channeltools.get_channel_parameters(item.channel)
        thumb = item.thumbnail if item.thumbnail else 'Infoplus/' + item.contentType.replace('show', '') + '.png'
        logger.info('THUMB', thumb)
        it = xbmcgui.ListItem(item.title)
        year = str(item.year if item.year else item.infoLabels.get('year', ''))
        rating = str(item.infoLabels.get('rating', ''))
        it.setProperties({'thumb': thumb, 'fanart': item.fanart, 'plot': item.plot,
                          'year': '    [' + year + ']' if year else '', 'rating':'    [' + rating + ']' if rating else '',
                          'item': url, 'verified': item.verified, 'channel':channelParams['title'], 'channelthumb': channelParams['thumbnail'] if item.verified else ''})
        if item.server:
            color = scrapertools.find_single_match(item.alive, r'(FF[^\]]+)')
            it.setProperties({'channel': channeltools.get_channel_parameters(item.channel).get('title', ''),
                              'thumb': "https://raw.githubusercontent.com/kodiondemand/media/master/resources/servers/%s.png" % item.server.lower(),
                              'servername': servertools.get_server_parameters(item.server.lower()).get('name', item.server),
                              'color': color if color else 'FF0082C2'})

        return it

    def update(self, channel, valid, results):
        if self.exit:
            return
        logger.debug('Search on channel', channel)
        if self.item.mode != 'all' and 'valid' not in self.results:
            self.results['valid'] = 0
            item = xbmcgui.ListItem('valid')
            item.setProperties({'thumb': 'valid.png',
                                'position': '0',
                                'results': '0'})
            self.channels.append(item)
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.addItems(self.channels)
            self.CHANNELS.selectItem(pos)
            self.setFocusId(CHANNELS)
        if valid:
            item = self.CHANNELS.getListItem(0)
            resultsList = item.getProperty('items')
            for result in valid:
                resultsList += result.tourl() + '|'
            item.setProperty('items', resultsList)
            self.channels[0].setProperty('results', str(len(resultsList.split('|'))))
            if self.CHANNELS.getSelectedPosition() == 0:
                items = []
                for result in valid:
                    if result: items.append(self.makeItem(result.tourl()))
                pos = self.RESULTS.getSelectedPosition()
                self.RESULTS.addItems(items)
                self.RESULTS.selectItem(pos)
        if results:
            resultsList = ''
            channelParams = channeltools.get_channel_parameters(channel)
            name = channelParams['title']
            if name not in self.results:
                item = xbmcgui.ListItem(name)
                item.setProperties({'thumb': channelParams['thumbnail'],
                                    'position': '0',
                                    'results': str(len(results))
                                    })
                for result in results:
                    resultsList += result.tourl() + '|'
                item.setProperty('items',resultsList)
                self.results[name] = len(self.results)
                self.channels.append(item)
            else:
                item = self.CHANNELS.getListItem(self.results[name])
                resultsList = item.getProperty('items')
                for result in results:
                    resultsList += result.tourl() + '|'
                item.setProperty('items',resultsList)
                logger.log(self.channels[int(self.results[name])])
                self.channels[int(self.results[name])].setProperty('results', str(len(resultsList.split('|')) - 1))
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.reset()
            self.CHANNELS.addItems(self.channels)
            self.CHANNELS.selectItem(pos)

            if len(self.channels) == 1:
                self.setFocusId(CHANNELS)
                channelResults = self.CHANNELS.getListItem(self.results[name]).getProperty('items').split('|')
                items = []
                for result in channelResults:
                    if result: items.append(self.makeItem(result))
                self.RESULTS.reset()
                self.RESULTS.addItems(items)

        percent = (float(self.count) / len(self.searchActions)) * 100
        self.LOADING.setVisible(False)
        self.PROGRESS.setPercent(percent)
        self.COUNT.setText('%s/%s [%s"]' % (self.count, len(self.searchActions), int(time.time() - self.time) ))
        if percent == 100:
            self.channels = []
            self.moduleDict = {}
            self.searchActions = []
        if percent == 100 and not self.results:
            self.PROGRESS.setVisible(False)
            self.NORESULTS.setVisible(True)

    def onInit(self):
        self.time = time.time()

        # collect controls
        self.CHANNELS = self.getControl(CHANNELS)
        self.RESULTS = self.getControl(RESULTS)
        self.PROGRESS = self.getControl(PROGRESS)
        self.COUNT = self.getControl(COUNT)
        self.MAINTITLE = self.getControl(MAINTITLE)
        self.MAINTITLE.setText(config.get_localized_string(30993).replace('...', '') % '"%s"' % self.item.text)
        self.SEARCH = self.getControl(SEARCH)
        self.EPISODES = self.getControl(EPISODES)
        self.EPISODESLIST = self.getControl(EPISODESLIST)
        self.SERVERS = self.getControl(SERVERS)
        self.SERVERLIST = self.getControl(SERVERLIST)
        self.NORESULTS = self.getControl(NORESULTS)
        self.NORESULTS.setVisible(False)
        self.LOADING = self.getControl(LOADING)
        self.LOADING.setVisible(False)

        self.Focus(self.focus)

        if self.type:
            self.type = None
            if self.item.mode in ['all', 'search']:
                if self.item.type: self.item.mode = self.item.type
                self.thread = Thread(target=self.search)
                self.thread.start()
            elif self.item.mode in ['movie', 'tvshow', 'person_']:
                self.select()
            elif self.item.mode in ['person']:
                self.actors()

    def Focus(self, focusid):
        if focusid in [SEARCH]:
            self.focus = CHANNELS
            self.SEARCH.setVisible(True)
            self.EPISODES.setVisible(False)
            self.SERVERS.setVisible(False)
        if focusid in [EPISODES]:
            self.focus = focusid
            self.SEARCH.setVisible(False)
            self.EPISODES.setVisible(True)
            self.SERVERS.setVisible(False)
        if focusid in [SERVERS]:
            self.focus = SERVERLIST
            self.SEARCH.setVisible(False)
            self.EPISODES.setVisible(False)
            self.SERVERS.setVisible(True)

    def onAction(self, action):
        global close_action
        action = action.getId()
        focus = self.getFocusId()

        if action in [CONTEXT] and focus in [RESULTS, EPISODESLIST, SERVERLIST]:
            self.context()

        elif action in [SWIPEUP] and self.CHANNELS.isVisible():
            self.setFocusId(CHANNELS)
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.selectItem(pos)

        elif action in [LEFT, RIGHT, MOUSEMOVE] and focus in [CHANNELS] and self.CHANNELS.isVisible():
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            channelResults = self.CHANNELS.getListItem(self.results[name]).getProperty('items').split('|')
            for result in channelResults:
                if result: items.append(self.makeItem(result))
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)

        elif (action in [DOWN] and focus in [BACK, CLOSE, MENU]) or focus not in [BACK, CLOSE, MENU, SERVERLIST, EPISODESLIST, RESULTS, CHANNELS]:
            if self.SERVERS.isVisible(): self.setFocusId(SERVERLIST)
            elif self.EPISODES.isVisible(): self.setFocusId(EPISODESLIST)
            elif self.RESULTS.isVisible(): self.setFocusId(RESULTS)

        elif focus in [RESULTS] and self.item.mode == 'all':
            pos = self.RESULTS.getSelectedPosition()
            self.CHANNELS.getSelectedItem().setProperty('position', str(pos))

        elif action == ENTER and focus in [CHANNELS]:
            self.setFocusId(RESULTS)

        if action in [BACKSPACE]:
            self.Back()

        elif action in [EXIT]:
            self.Close()
            close_action = True

    def onClick(self, control_id):
        global close_action

        if self.RESULTS.getSelectedItem(): search = self.RESULTS.getSelectedItem().getProperty('search')
        else: search = None
        if control_id in [CHANNELS]:
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            channelResults = self.CHANNELS.getListItem(self.results[name]).getProperty('items').split('|')
            for result in channelResults:
                if result: items.append(self.makeItem(result))
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)
            self.CHANNELS.getSelectedItem().setProperty('position', str(subpos))

        elif control_id in [BACK]:
            self.Back()

        elif control_id in [CLOSE]:
            self.Close()
            close_action = True

        elif control_id in [MENU]:
            self.context()

        elif search:
            pos = self.RESULTS.getSelectedPosition()
            if search == 'next':
                self.page += 1
                self.actors()
            elif search == 'previous':
                self.page -= 1
                self.actors()
            elif search == 'persons':
                item = self.item.clone(mode='person_', discovery=self.persons[pos])
                # self.close()
                Search(item, self.moduleDict, self.searchActions)
                if close_action:
                    self.close
            else:
                item = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
                if self.item.mode == 'movie': item.contentTitle = self.RESULTS.getSelectedItem().getLabel()
                else: item.contentSerieName = self.RESULTS.getSelectedItem().getLabel()

                self.RESULTS.reset()
                self.RESULTS.setVisible(False)
                self.PROGRESS.setVisible(True)
                self.selected = True
                self.thActions.join()
                self.RESULTS.addItems(self.items)
                self.RESULTS.setVisible(True)
                self.PROGRESS.setVisible(False)

                # self.close()
                Search(item, self.moduleDict, self.searchActions)
                if close_action:
                    self.close()

        elif control_id in [RESULTS, EPISODESLIST]:
            busy(True)
            if control_id in [RESULTS]:
                name = self.CHANNELS.getSelectedItem().getLabel()
                self.pos = self.RESULTS.getSelectedPosition()
                item = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
            else:
                self.eppos = self.EPISODESLIST.getSelectedPosition()
                item_url = self.EPISODESLIST.getSelectedItem().getProperty('item')
                if item_url:
                    item = Item().fromurl(item_url)
                else:  # no results  item
                    busy(False)
                    return

                if item.action in ['add_pelicula_to_library', 'add_serie_to_library','save_download']:  # special items (add to videolibrary, download ecc.)
                    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item_url + ")")
                    busy(False)
                    return

            try:
                self.channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
                self.itemsResult = getattr(self.channel, item.action)(item)
            except:
                import traceback
                logger.error('error importing/getting search items of ' + item.channel)
                logger.error(traceback.format_exc())
                self.itemsResult = []

            if self.itemsResult and self.itemsResult[0].action in ['play', '']:

                if config.get_setting('checklinks') and not config.get_setting('autoplay'):
                    self.itemsResult = servertools.check_list_links(self.itemsResult, config.get_setting('checklinks_number'))
                servers = self.itemsResult if self.itemsResult else []
                self.itemsResult = []
                uhd = []
                fhd = []
                hd = []
                sd = []
                unknown = []
                other = []
                for i, item in enumerate(servers):
                    if item.server:
                        it = self.makeItem(item.tourl())
                        it.setProperty('index', str(i))
                        if item.quality in ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k']:
                            it.setProperty('quality', 'uhd.png')
                            uhd.append(it)
                        elif item.quality in ['fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p']:
                            it.setProperty('quality', 'Fhd.png')
                            fhd.append(it)
                        elif item.quality in ['hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv']:
                            it.setProperty('quality', 'hd.png')
                            hd.append(it)
                        elif item.quality in ['sd', '480p', '480', '360p', '360', '240p', '240']:
                            it.setProperty('quality', 'sd.png')
                            sd.append(it)
                        else:
                            it.setProperty('quality', '')
                            unknown.append(it)
                    elif not item.action:
                        self.getControl(QUALITYTAG).setText(item.fulltitle)
                    else:
                        it = self.makeItem(item.tourl())
                        other.append(it)

                uhd.sort(key=lambda it: it.getProperty('index'))
                fhd.sort(key=lambda it: it.getProperty('index'))
                hd.sort(key=lambda it: it.getProperty('index'))
                sd.sort(key=lambda it: it.getProperty('index'))
                unknown.sort(key=lambda it: it.getProperty('index'))

                serverlist = uhd + fhd + hd + sd + unknown + other
                if not serverlist:
                    serverlist = [xbmcgui.ListItem(config.get_localized_string(60347))]
                    serverlist[0].setProperty('thumb', channelselector.get_thumb('nofolder.png'))

                self.Focus(SERVERS)
                self.SERVERLIST.reset()
                self.SERVERLIST.addItems(serverlist)
                self.setFocusId(SERVERLIST)

                if config.get_setting('autoplay'):
                    busy(False)

            else:
                self.episodes = self.itemsResult if self.itemsResult else []
                self.itemsResult = []
                ep = []
                for item in self.episodes:
                    it = xbmcgui.ListItem(item.title)
                    it.setProperty('item', item.tourl())
                    ep.append(it)

                if not ep:
                    ep = [xbmcgui.ListItem(config.get_localized_string(60347))]
                    ep[0].setProperty('thumb', channelselector.get_thumb('nofolder.png'))

                self.Focus(EPISODES)
                self.EPISODESLIST.reset()
                self.EPISODESLIST.addItems(ep)
                self.setFocusId(EPISODESLIST)

            busy(False)

        elif control_id in [SERVERLIST]:
            server = Item().fromurl(self.getControl(control_id).getSelectedItem().getProperty('item'))
            return self.play(server)

    def Back(self):
        self.getControl(QUALITYTAG).setText('')
        if self.SERVERS.isVisible():
            if self.episodes:
                self.Focus(EPISODES)
                self.setFocusId(EPISODESLIST)
            else:
                self.Focus(SEARCH)
                self.setFocusId(RESULTS)
                self.RESULTS.selectItem(self.eppos)
        elif self.EPISODES.isVisible():
            self.episodes = []
            self.Focus(SEARCH)
            self.setFocusId(RESULTS)
            self.RESULTS.selectItem(self.pos)
        elif self.item.mode in ['person']:
            self.actors()
        else:
            self.Close()

    def Close(self):
        self.exit = True
        if self.thread:
            busy(True)
            self.thread.join()
            busy(False)
        self.close()

    def context(self):
        focus = self.getFocusId()
        if focus == EPISODESLIST:  # context on episode
            item_url = self.EPISODESLIST.getSelectedItem().getProperty('item')
            parent = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
        elif focus == SERVERLIST:
            item_url = self.SERVERLIST.getSelectedItem().getProperty('item')
            parent = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
        else:
            item_url = self.RESULTS.getSelectedItem().getProperty('item')
            parent = self.item
        item = Item().fromurl(item_url)
        parent.noMainMenu = True
        commands = platformtools.set_context_commands(item, item_url, parent)
        context = [c[0] for c in commands]
        context_commands = [c[1].replace('Container.Refresh', 'RunPlugin').replace('Container.Update', 'RunPlugin') for c in commands]
        index = xbmcgui.Dialog().contextmenu(context)
        if index > 0: xbmc.executebuiltin(context_commands[index])


    def play(self, server=None):
        platformtools.prevent_busy(server)
        server.window = True
        server.globalsearch = True
        return run(server)

