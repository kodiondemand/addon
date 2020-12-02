# -*- coding: utf-8 -*-

import xbmc, xbmcgui, sys, channelselector, time
from core.support import dbg, typo, tmdb
from core.item import Item
from core import channeltools, servertools, scrapertools
from platformcode import platformtools, config, logger
from platformcode.launcher import run
from threading import Thread

if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]


def busy(state):
    if state: xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    else: xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

def set_workers():
    workers = config.get_setting('thread_number') if config.get_setting('thread_number') > 0 else None
    return workers

def Search(item):
    xbmc.executebuiltin('Dialog.Close(all,true)')
    SearchWindow('GlobalSearch.xml', config.get_runtime_path()).start(item)
    xbmc.sleep(600)

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92
SWIPEUP = 531
CONTEXT = 117

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
    def start(self, item):
        logger.debug()
        self.exit = False
        self.item = item
        self.lastSearch()
        if not self.item.text: return
        self.type = self.item.mode
        self.channels = []
        self.find = []
        self.persons = []
        self.episodes = []
        self.servers = []
        self.results = {}
        self.channelsList =  self.get_channels()
        self.focus = SEARCH
        self.process = True
        self.page = 1
        self.moduleDict = {}
        self.searchActions = []
        self.thread = None
        self.doModal()

    def lastSearch(self):
        logger.debug()
        if not self.item.text:
            if config.get_setting('last_search'): last_search = channeltools.get_channel_setting('Last_searched', 'search', '')
            else: last_search = ''
            if not self.item.text: self.item.text = platformtools.dialog_input(default=last_search, heading='')
            if self.item.text: channeltools.set_channel_setting('Last_searched', self.item.text, 'search')

    def select(self):
        logger.debug()
        self.PROGRESS.setVisible(False)
        items = []
        if self.persons:
            tmdb_info = tmdb.discovery(self.item, dict_=self.item.discovery)
            results = tmdb_info.results.get('cast',[])
        else:
            tmdb_info = tmdb.Tmdb(texto_buscado=self.item.text, tipo=self.item.mode.replace('show', ''))
            results = tmdb_info.results

        for result in results:
            logger.info(result)
            result = tmdb_info.get_infoLabels(result, origen=result)
            movie = result.get('title','')
            tvshow = result.get('name','')
            title = tvshow if tvshow else movie
            result['mode'] = 'tvshow' if tvshow else 'movie'
            self.find.append(result)
            thumb = 'Infoplus/' + result['mode'].replace('show','') + '.png'
            it = xbmcgui.ListItem(title)
            it.setProperty('thumb', result.get('thumbnail', thumb))
            it.setProperty('fanart', result.get('fanart',''))
            it.setProperty('plot', result.get('overview', ''))
            it.setProperty('search','search')
            year = result.get('release_date','')
            if year: it.setProperty('year','[' + year.split('/')[-1] + ']')
            else:
                year = result.get('first_air_date','')
                if year: it.setProperty('year','[' + year.split('-')[0] + ']')
            items.append(it)

        if items:
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.setFocusId(RESULTS)
        else:
            self.NORESULTS.setVisible(True)

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
            it = xbmcgui.ListItem(name)
            it.setProperty('thumb', thumb)
            it.setProperty('plot', plot)
            it.setProperty('search','persons')
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
            self.NORESULTS.setVisible(True)

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

            if self.item.mode == 'all' or self.item.type in list_cat:
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
            return module, action
        except:
            import traceback
            logger.error('error importing/getting search items of ' + channel)
            logger.error(traceback.format_exc())
            return None, None

    def search(self):
        count = 0
        self.count = 0
        self.LOADING.setVisible(True)
        with futures.ThreadPoolExecutor() as executor:
            for channel in self.channelsList:
                if self.exit: break
                module, action = executor.submit(self.getModule, channel).result()
                if module and action:
                    self.moduleDict[channel] = module
                    self.searchActions += action
                count += 1
                percent = (float(count) / len(self.channelsList)) * 100
                self.PROGRESS.setPercent(percent)
                self.COUNT.setText('%s/%s' % (count, len(self.channelsList)))
            self.channelsList = []

        with futures.ThreadPoolExecutor(max_workers=set_workers()) as executor:
            for searchAction in self.searchActions:
                if self.exit: break
                executor.submit(self.get_channel_results, self.item, self.moduleDict, searchAction)
        self.moduleDict = {}
        self.searchActions = []

    def get_channel_results(self, item, module_dict, search_action):
        logger.debug()
        channel = search_action.channel
        results = []
        valid = []
        other = []
        module = module_dict[channel]
        searched_id = item.infoLabels['tmdb_id']

        try:
            results.extend(module.search(search_action, item.text))
            if len(results) == 1:
                if not results[0].action or config.get_localized_string(70006).lower() in results[0].title.lower():
                    results = []

            if self.item.mode != 'all':
                for elem in results:
                    if not elem.infoLabels.get('year', ""):
                        elem.infoLabels['year'] = '-'
                    tmdb.set_infoLabels_item(elem)
                    if elem.infoLabels['tmdb_id'] == searched_id:
                        elem.from_channel = channel
                        elem.verified ='ok.png'
                        valid.append(elem)
                    else:
                        other.append(elem)
        except:
            pass

        self.count += 1
        if self.item.mode == 'all': self.update(channel, results)
        else: self.update(channel, valid + other)

    def makeItem(self, item):
        logger.debug()
        thumb = item.thumbnail if item.thumbnail else 'Infoplus/' + item.contentType.replace('show','') + 'png'
        logger.info('THUMB', thumb)
        it = xbmcgui.ListItem(item.title)
        it.setProperty('year', '[' + str(item.year if item.year else item.infoLabels.get('year','')) + ']')
        it.setProperty('thumb', thumb)
        it.setProperty('fanart', item.fanart)
        it.setProperty('plot', item.plot)
        it.setProperty('verified', item.verified)
        if item.server:
            color = scrapertools.find_single_match(item.alive, r'(FF[^\]]+)')
            it.setProperty('channel', channeltools.get_channel_parameters(item.channel).get('title',''))
            it.setProperty('thumb', "https://raw.githubusercontent.com/kodiondemand/media/master/resources/servers/%s.png" % item.server.lower())
            it.setProperty('servername', servertools.get_server_parameters(item.server.lower()).get('name',item.server))
            it.setProperty('color', color if color else 'FF0082C2')
        return it

    def update(self, channel, results):
        logger.debug('Search on channel', channel)
        if results:
            channelParams = channeltools.get_channel_parameters(channel)
            name = channelParams['title']
            if name not in self.results:
                self.results[name] = [results, len(self.channels)]
                item = xbmcgui.ListItem(name)
                item.setProperty('thumb', channelParams['thumbnail'])
                item.setProperty('position', '0')
                item.setProperty('results', str(len(results)))
                item.setProperty('verified', results[0].verified)
                self.channels.append(item)
            else:
                self.results[name].append([results, len(self.channels)])
                self.channels[int(self.results[name][1])].setProperty('results', str(len(results)))
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.reset()
            self.CHANNELS.addItems(self.channels)
            self.CHANNELS.selectItem(pos)
            if len(self.channels) == 1:
                self.setFocusId(CHANNELS)
                items = []
                for result in self.results[name][0]:
                    items.append(self.makeItem(result))
                self.RESULTS.reset()
                self.RESULTS.addItems(items)
        percent = (float(self.count) / len(self.searchActions)) * 100
        self.LOADING.setVisible(False)
        self.PROGRESS.setPercent(percent)
        self.COUNT.setText('%s/%s [%s"]' % (self.count, len(self.searchActions), int(time.time() - self.time) ))
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
        self.MAINTITLE.setText(typo(config.get_localized_string(30993).replace('...','') % '"%s"' % self.item.text, 'bold'))
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
            elif self.item.mode in ['movie', 'tvshow']:
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
        action = action.getId()
        focus = self.getFocusId()
        if action in [CONTEXT] and focus in [RESULTS, EPISODESLIST, SERVERLIST]:
            self.context()

        elif action in [SWIPEUP] and self.CHANNELS.isVisible() :
            self.setFocusId(CHANNELS)
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.selectItem(pos)

        elif action in [LEFT, RIGHT] and focus in [CHANNELS] and self.CHANNELS.isVisible():
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            for result in self.results[name][0]:
                items.append(self.makeItem(result))
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)

        elif action in [DOWN] and focus in [BACK, CLOSE, MENU]:
            if self.SERVERS.isVisible(): self.setFocusId(SERVERLIST)
            elif self.EPISODES.isVisible(): self.setFocusId(EPISODESLIST)
            else: self.setFocusId(RESULTS)

        elif focus in [RESULTS] and self.item.mode == 'all':
            pos = self.RESULTS.getSelectedPosition()
            self.CHANNELS.getSelectedItem().setProperty('position', str(pos))

        if action in [BACKSPACE]:
            self.Back()

        elif action in [EXIT]:
            self.Close()

    def onClick(self, control_id):
        if self.RESULTS.getSelectedItem(): search = self.RESULTS.getSelectedItem().getProperty('search')
        else: search = None
        if control_id in [CHANNELS]:
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            for result in self.results[name][0]:
                items.append(self.makeItem(result))
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)
            self.CHANNELS.getSelectedItem().setProperty('position', str(subpos))
            # self.setFocusId(RESULTS)

        elif control_id in [BACK]:
            self.Back()

        elif control_id in [CLOSE]:
            self.Close()

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
                self.item.discovery = self.persons[pos]
                self.select()
            else:
                result = self.find[pos]
                name = self.RESULTS.getSelectedItem().getLabel()
                item = Item(mode='search', type=result['mode'], contentType=result['mode'], infoLabels=result, selected = True, text=name)
                if self.item.mode == 'movie': item.contentTitle = self.RESULTS.getSelectedItem().getLabel()
                else: item.contentSerieName = self.RESULTS.getSelectedItem().getLabel()
                return Search(item)

        elif control_id in [RESULTS, EPISODESLIST]:
            busy(True)
            if control_id in [RESULTS]:
                name = self.CHANNELS.getSelectedItem().getLabel()
                self.pos = self.RESULTS.getSelectedPosition()
                item = self.results[name][0][self.pos]
            else:
                self.pos = self.EPISODESLIST.getSelectedPosition()
                item = self.episodes[self.pos]
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
                self.servers = self.itemsResult
                self.itemsResult = []
                uhd = []
                fhd = []
                hd = []
                sd = []
                unknown = []
                for i, item in enumerate(self.servers):
                    if item.server:
                        it = self.makeItem(item)
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


                uhd.sort(key=lambda it: it.getProperty('index'))
                fhd.sort(key=lambda it: it.getProperty('index'))
                hd.sort(key=lambda it: it.getProperty('index'))
                sd.sort(key=lambda it: it.getProperty('index'))
                unknown.sort(key=lambda it: it.getProperty('index'))

                serverlist = uhd + fhd + hd + sd + unknown

                self.Focus(SERVERS)
                self.SERVERLIST.reset()
                self.SERVERLIST.addItems(serverlist)
                self.setFocusId(SERVERLIST)

            else:
                self.episodes = self.itemsResult
                self.itemsResult = []
                episodes = []
                for item in self.episodes:
                    if item.action == 'findvideos':
                        it = xbmcgui.ListItem(item.title)
                        episodes.append(it)

                self.Focus(EPISODES)
                self.EPISODESLIST.reset()
                self.EPISODESLIST.addItems(episodes)
                self.setFocusId(EPISODESLIST)

            busy(False)

        elif control_id in [SERVERLIST]:
            index = int(self.getControl(control_id).getSelectedItem().getProperty('index'))
            server = self.servers[index]
            server.player_mode = 0
            run(server)

    def Back(self):
        self.getControl(QUALITYTAG).setText('')
        if self.SERVERS.isVisible():
            if self.episodes:
                self.Focus(EPISODES)
                self.setFocusId(EPISODESLIST)
            else:
                self.Focus(SEARCH)
                self.setFocusId(RESULTS)
                self.RESULTS.selectItem(self.pos)
        elif self.EPISODES.isVisible():
            self.episodes = []
            self.Focus(SEARCH)
            self.setFocusId(RESULTS)
            self.RESULTS.selectItem(self.pos)
        elif self.item.mode in ['person'] and self.find:
            self.find = []
            self.actors()
        else:
            self.Close()

    def Close(self):
        self.exit = True
        if self.thread:
            busy(True)
            while self.thread.is_alive(): xbmc.sleep(200)
            busy(False)
        self.close()

    def context(self):
        pos = self.RESULTS.getSelectedPosition()
        name = self.CHANNELS.getSelectedItem().getLabel()
        item = self.results[name][0][pos]
        context = [config.get_localized_string(70739), config.get_localized_string(70557), config.get_localized_string(30155), config.get_localized_string(60359)]
        context_commands = ["RunPlugin(%s?%s)" % (sys.argv[0], 'action=open_browser&url=' + item.url),
                            "RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=kodfavorites&action=addFavourite&from_channel=' + item.channel + '&from_action=' + item.action),
                            "RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=favorites&action=addFavourite&from_channel=' + item.channel + '&from_action=' + item.action),
                            "RunPlugin(%s?%s)" % (sys.argv[0], 'channel=trailertools&action=buscartrailer&contextual=True&search_title=' + item.contentTitle if item.contentTitle else item.fulltitle)]
        if item.contentType == 'movie':
            context += [config.get_localized_string(60353), config.get_localized_string(60354)]
            context_commands += ["RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'action=add_pelicula_to_library&from_action=' + item.action),
                                 "RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' +item.action)]

        else:
            context += [config.get_localized_string(60352), config.get_localized_string(60355), config.get_localized_string(60357)]
            context_commands += ["RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'action=add_serie_to_library&from_action=' + item.action),
                                 "RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action),
                                 "RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel +'&from_action=' + item.action)]

            if self.EPISODES.isVisible() or self.SERVERS.isVisible():
                pos = self.EPISODESLIST.getSelectedPosition()
                item = self.episodes[pos]
                context += [config.get_localized_string(60356)]
                context_commands += ["RunPlugin(%s?%s&%s)" % (sys.argv[0], item.tourl(), 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' +item.action)]

        index = xbmcgui.Dialog().contextmenu(context)
        if index > 0: xbmc.executebuiltin(context_commands[index])