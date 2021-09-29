# -*- coding: utf-8 -*-




import xbmc, xbmcgui, sys, channelselector, time, threading
from core.support import tmdb
from core.item import Item
from core import channeltools, scrapertools, support
from platformcode import platformtools, config, logger
from threading import Thread
from collections import OrderedDict

if sys.version_info[0] >= 3:
    PY3 = True
    from concurrent import futures
else:
    PY3 = False
    from concurrent_py2 import futures

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]
close_action = False
update_lock = threading.Lock()

workers = config.get_setting('thread_number') if config.get_setting('thread_number') > 0 else None


def new_search(*args):
    xbmc.executebuiltin('Dialog.Close(all)')
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
NORESULTS = 3

# Search
MAINTITLE = 100
CHANNELS = 101
RESULTS = 102
EPISODESLIST = 103

PROGRESS = 500
MENU = 502
BACK = 503
CLOSE = 504
TAB = 505
NEXT = 506
PREV = 507
# Servers


class SearchWindow(xbmcgui.WindowXML):
    def start(self, item, moduleDict={}, searchActions=[], thActions=None):
        logger.debug()

        self.exit = False
        self.item = item
        self.channels = OrderedDict({'valid':[]})
        self.persons = []
        self.episodes = []
        self.results = {}
        self.focus = SEARCH
        self.page = 1
        self.moduleDict = moduleDict
        self.searchActions = searchActions
        self.thread = None
        self.selected = False
        self.pos = 0
        self.items = []
        self.search_threads = []
        self.reload = False
        self.nextAction = None
        self.next = None
        self.previous = None
        self.FOCUS = False
        self.mode = self.item.mode.split('_')[-1]

        if not thActions and not self.searchActions:
            self.thActions = Thread(target=self.getActionsThread)
            self.thActions.start()
        else:
            self.thActions = thActions

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

    def getActionsThread(self):
        logger.debug()
        self.channelsList = self.get_channels()

        for channel in self.channelsList:
            logger.debug(channel)
            try:
                module = platformtools.channel_import(channel)
                mainlist = getattr(module, 'mainlist')(Item(channel=channel, global_search=True))
                actions = [elem for elem in mainlist if elem.action == "search" and (self.mode in ['all', 'person'] or elem.contentType in [self.mode, 'undefined'])]
                self.moduleDict[channel] = module
                self.searchActions.append(actions)
            except:
                import traceback
                logger.error('error importing/getting search items of ' + channel)
                logger.error(traceback.format_exc())

    def getActions(self):
        # return immediately all actions that are already loadead
        for action in self.searchActions:
            yield action

        # wait and return as getActionsThread load
        lastLen = len(self.searchActions)
        if self.thActions:
            while self.thActions.is_alive():
                while len(self.searchActions) == lastLen:
                    if not self.thActions.is_alive():
                        return
                    time.sleep(0.1)
                yield self.searchActions[lastLen-1]
                lastLen = len(self.searchActions)

    def select(self):
        logger.debug()
        self.PROGRESS.setVisible(False)
        self.items = []
        if self.mode == 'filmography':
            tmdb_info = tmdb.discovery(self.item, dict_=self.item.discovery)
            results = tmdb_info.results.get('cast',[])
        else:
            tmdb_info = tmdb.Tmdb(searched_text=self.item.text, search_type=self.mode.replace('show', ''))
            results = tmdb_info.results


        def make(n, result):
            result = tmdb_info.get_infoLabels(result, origen=result)
            if self.mode == 'movie':
                title = result['title']
                result['mode'] = 'movie'
            elif self.mode == 'tvshow':
                title = result['name']
                result['mode'] = 'tvshow'
            else:
                title = result.get('title', '')
                result['mode'] = result['media_type'].replace('tv', 'tvshow')

            noThumb = 'Infoplus/' + result['mode'].replace('show','') + '.png'
            rating = result.get('vote_average', 0)

            new_item = Item(channel='globalsearch',
                            action=True,
                            title=title,
                            mode='search',
                            type=result['mode'],
                            contentType=result['mode'],
                            text=title,
                            infoLabels=result)

            if self.mode == 'movie':
                new_item.contentTitle = result['title']
            else:
                new_item.contentSerieName = result['name']
            tmdb.set_infoLabels(new_item)
            tagline = new_item.infoLabels.get('tagline')
            it = xbmcgui.ListItem('[B]{}[/B]'.format(title) + ('\n[I]{}[/I]'.format(tagline if tagline else '')))
            it.setArt({'poster':result.get('thumbnail', noThumb), 'fanart':result.get('fanart', '')})

            platformtools.set_infolabels(it, new_item)

            color = 'FFFFFFFF' if not rating else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'
            it.setProperties({'rating': str(int(rating) * 10) if rating else 100, 'color':color, 'item': new_item.tourl(), 'search': 'search'})
            return n, it

        r_list = []
        with futures.ThreadPoolExecutor() as executor:
            searchList = [executor.submit(make, n, result) for n, result in enumerate(results)]
            for res in futures.as_completed(searchList):
                r_list.append(res.result())
        r_list.sort(key=lambda r: r[0] )
        self.items = [r[1] for r in r_list]

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

            new_item = Item(channel='globalsearch',
                            action=True,
                            title=name,
                            thumbnail=thumb,
                            plot= plot,
                            mode='search_filmography')

            it = xbmcgui.ListItem(name)
            platformtools.set_infolabels(it, new_item)
            it.setArt({'poster':thumb})
            it.setProperties({'search': 'persons', 'item': new_item.tourl()})
            items.append(it)
        if len(results) > 19:
            it = xbmcgui.ListItem(config.get_localized_string(70006))
            it.setArt({'poster':'Infoplus/next_focus.png'})
            it.setProperty('search','next')
            items.append(it)
        if self.page > 1:
            it = xbmcgui.ListItem(config.get_localized_string(70005))
            it.setArt({'poster':'Infoplus/previous_focus.png'})
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
        logger.debug('MODE:', self.mode)
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

            if self.mode in ['all', 'person'] or self.mode in list_cat:
                if config.get_setting("include_in_global_search", channel) and ch_param.get("active", False):
                    channels_list.append(channel)

        logger.debug('search in channels:', channels_list)

        return channels_list

    def timer(self):
        while self.searchActions or (self.thActions and self.thActions.is_alive()):
            if self.exit: return
            try:
                percent = (float(self.count) / len(self.searchActions)) * 100
            except ZeroDivisionError:
                percent = 0
            self.PROGRESS.setPercent(percent)
            self.MAINTITLE.setText('{} | {}/{} [{}"]'.format(self.mainTitle,self.count, len(self.searchActions), int(time.time() - self.time)))

            if percent == 100:
                if len(self.channels['valid']) or len(self.channels) == 2:
                    self.setFocusId(RESULTS)
                elif not len(self.channels['valid']) and not len(self.channels):
                    self.NORESULTS.setVisible(True)
                    self.setFocusId(CLOSE)
                OrderedDict({'valid':[]})
                self.moduleDict = {}
                self.searchActions = []

            time.sleep(1)

    def search(self):
        logger.debug()
        self.count = 0
        Thread(target=self.timer).start()

        try:
            with futures.ThreadPoolExecutor(max_workers=workers) as executor:
                for searchAction in self.getActions():
                    if self.exit: return
                    self.search_threads.append(executor.submit(self.get_channel_results, searchAction))
                for res in futures.as_completed(self.search_threads):
                    if res.result():
                        valid, results = res.result()
                        self.channels['valid'].extend(valid)

                        if results:
                            name = results[0].channel
                            if name not in results: 
                                self.channels[name] = []
                            self.channels[name].extend(results)

                        if valid or results:
                            self.update()

        except:
            import traceback
            logger.error(traceback.format_exc())
        self.count = len(self.searchActions)

    def get_channel_results(self, searchAction):
        def channel_search(text):
            results = []
            valid = []
            other = []

            for a in searchAction:
                logger.debug('Search on channel:', a.channel)
                results.extend(self.moduleDict[a.channel].search(a, text))
            if len(results) == 1:
                if not results[0].action or results[0].nextPage:
                    results = []

            if self.mode != 'all':
                for elem in results:
                    if elem.infoLabels.get('tmdb_id') == self.item.infoLabels.get('tmdb_id'):
                        elem.from_channel = elem.channel
                        elem.verified = 1
                        valid.append(elem)
                    else:
                        other.append(elem)
            return results, valid, other

        logger.debug()
        results = []
        valid = []
        other = []

        if self.exit:
            return [], [], []


        try:
            results, valid, other = channel_search(self.item.text)

            # if we are on movie search but no valid results is found, and there's a lot of results (more pages), try
            # to add year to search text for better filtering
            if self.item.contentType == 'movie' and not valid and other and other[-1].nextPage \
                    and self.item.infoLabels['year']:
                logger.debug('retring adding year on channel ')
                dummy, valid, dummy = channel_search(self.item.text + " " + str(self.item.infoLabels['year']))

            # some channels may use original title
            if self.mode != 'all' and not valid and self.item.infoLabels.get('originaltitle'):
                logger.debug('retring with original title on channel ')
                dummy, valid, dummy = channel_search(self.item.infoLabels.get('originaltitle'))
        except:
            import traceback
            logger.error(traceback.format_exc())

        self.count += 1

        return valid, other if other else results

    def makeItem(self, item):
        if type(item) == str: item = Item().fromurl(item)
        channelParams = channeltools.get_channel_parameters(item.channel)
        info = item.infoLabels

        title = item.title
        tagline = info.get('tagline')
        if tagline == title: tagline = ''
        if item.contentType == 'episode':
            tagline = ''
            title = '{:02d}. {}'.format(item.contentEpisodeNumber, item.contentTitle)
            if item.contentSeason:
                title = '{}x{}'.format(item.contentSeason, title)
            if item.contentLanguage:
                title = '{} [{}]'.format(title, item.contentLanguage)
        if item.quality:
            title = title = '{} [{}]'.format(title, item.quality)
        if tagline:
            title = '[B]{}[/B]'.format(title) + ('\n[I]{}[/I]'.format(tagline))

        thumb = item.thumbnail if item.thumbnail else 'Infoplus/' + item.contentType.replace('show', '') + '.png'

        it = xbmcgui.ListItem(title)
        it.setArt({'poster':thumb, 'fanart':item.fanart, 'thumb':thumb if config.get_setting('episode_info') else ''})
        platformtools.set_infolabels(it, item)
        # logger.debug(item)

        rating = info.get('rating')
        color = 'FFFFFFFF' if not rating else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'

        it.setProperties({'rating': str(int(info.get('rating',10) * 10)), 'color': color,
                          'item': item.tourl(), 'verified': item.verified, 'channel':channelParams['title'], 'channelthumb': channelParams['thumbnail'], 'sub':'true' if 'sub' in item.contentLanguage.lower() else ''})

        return it

    def update(self):
        channels = []
        for name, value in self.channels.items():
            thumb = 'valid.png'
            if name != 'valid':
                thumb = channeltools.get_channel_parameters(name)['thumbnail']
            if value:
                item = xbmcgui.ListItem(name)
                item.setArt({'poster': thumb })
                item.setProperties({'position': '0',
                                    'results': str(len(value))})
                channels.append(item)


        if channels:
            pos = self.CHANNELS.getSelectedPosition()
            if pos < 0: pos = 0
            self.CHANNELS.reset()
            self.CHANNELS.addItems(channels)
            self.CHANNELS.selectItem(pos)

            focus = self.getFocusId()
            items = [self.makeItem(r) for r in self.channels[self.CHANNELS.getSelectedItem().getLabel()]]
            subpos = self.RESULTS.getSelectedPosition()
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)
            if not self.FOCUS:
                if len(self.channels['valid']):
                    self.FOCUS = True
                    self.setFocusId(RESULTS)
                elif focus not in [RESULTS]:
                    self.FOCUS = True
                    self.setFocusId(CHANNELS)

    def onInit(self):
        self.NORESULTS = self.getControl(NORESULTS)
        self.NORESULTS.setVisible(False)

        self.time = time.time()
        self.mainTitle = config.get_localized_string(30993).replace('...', '') % '"%s"' % self.item.text

        # collect controls
        self.NEXT = self.getControl(NEXT)
        self.NEXT.setVisible(False)
        self.PREV = self.getControl(PREV)
        self.PREV.setVisible(False)
        self.CHANNELS = self.getControl(CHANNELS)
        self.RESULTS = self.getControl(RESULTS)
        self.PROGRESS = self.getControl(PROGRESS)
        self.MAINTITLE = self.getControl(MAINTITLE)
        self.MAINTITLE.setText(self.mainTitle)
        self.SEARCH = self.getControl(SEARCH)
        self.EPISODES = self.getControl(EPISODES)
        self.EPISODESLIST = self.getControl(EPISODESLIST)
        self.Focus(self.focus)

        if self.item.mode.split('_')[0] in ['all', 'search']:
            if 'search' in self.item.mode:
                self.item.text = scrapertools.title_unify(self.item.text)
            self.thread = Thread(target=self.search)
            self.thread.start()
        elif self.mode in ['movie', 'tvshow', 'filmography']:
            self.select()
        elif self.mode in ['person']:
            self.actors()

    def Focus(self, focusid):
        if focusid in [SEARCH]:
            self.focus = CHANNELS
            self.SEARCH.setVisible(True)
            self.EPISODES.setVisible(False)
        if focusid in [EPISODES]:
            self.focus = focusid
            self.SEARCH.setVisible(False)
            self.EPISODES.setVisible(True)

    def onAction(self, action):
        global close_action
        action = action.getId()
        focus = self.getFocusId()

        if action in [CONTEXT] and focus in [RESULTS, EPISODESLIST]:
            self.context()

        elif focus in [EPISODESLIST] and action in [LEFT, RIGHT]:
            if action in [LEFT]:
                item = self.previous
            if action in [RIGHT]:
                item = self.next
            if item:
                platformtools.dialog_busy(True)
                self.loadEpisodes(item)
                platformtools.dialog_busy(False)

        elif action in [SWIPEUP] and self.CHANNELS.isVisible():
            self.setFocusId(CHANNELS)
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.selectItem(pos)

        elif action in [LEFT, RIGHT, MOUSEMOVE] and focus in [CHANNELS] and self.CHANNELS.isVisible():
            self.channelItems()

        elif (action in [DOWN] and focus in [BACK, CLOSE, MENU]) or focus not in [BACK, CLOSE, MENU, EPISODESLIST, RESULTS, CHANNELS]:
            if self.EPISODES.isVisible(): self.setFocusId(EPISODESLIST)
            elif self.RESULTS.isVisible() and self.RESULTS.size() > 0: self.setFocusId(RESULTS)
            elif self.CHANNELS.isVisible(): self.setFocusId(CHANNELS)

        elif focus in [RESULTS]:
            pos = self.RESULTS.getSelectedPosition()
            try:
                self.CHANNELS.getSelectedItem().setProperty('position', str(pos))
            except:
                pass

        elif action == ENTER and focus in [CHANNELS]:
            self.setFocusId(RESULTS)

        if action in [BACKSPACE]:
            self.Back()

        elif action in [EXIT]:
            self.Close()
            # reload()
            close_action = True
            xbmc.sleep(500)

    def onClick(self, control_id):
        global close_action

        if self.RESULTS.getSelectedItem(): search = self.RESULTS.getSelectedItem().getProperty('search')
        else: search = None
        if control_id in [CHANNELS, TAB]:
            self.channelItems()

        elif control_id in [BACK]:
            self.Back()

        elif control_id in [CLOSE]:
            self.Close()
            # reload()
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
                new_search(item, self.moduleDict, self.searchActions)
                if close_action:
                    self.close()
            else:
                item = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
                if self.mode == 'movie': item.contentTitle = self.RESULTS.getSelectedItem().getLabel()
                else: item.contentSerieName = self.RESULTS.getSelectedItem().getLabel()

                new_search(item, self.moduleDict, self.searchActions)
                if close_action:
                    self.close()

        elif control_id in [RESULTS, EPISODESLIST]:

            platformtools.dialog_busy(True)
            if control_id in [RESULTS]:
                name = self.CHANNELS.getSelectedItem().getLabel()
                self.pos = self.RESULTS.getSelectedPosition()
                item = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
            else:
                item_url = self.EPISODESLIST.getSelectedItem().getProperty('item')
                if item_url:
                    item = Item().fromurl(item_url)

                else:  # no results  item
                    platformtools.dialog_busy(False)
                    return

                if item.action:
                    item.window = True
                    item.folder = False
                    xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item.tourl() + ")")
                    platformtools.dialog_busy(False)
                    return

            self.loadEpisodes(item)

            platformtools.dialog_busy(False)

    def channelItems(self):
        items = []
        name = self.CHANNELS.getSelectedItem().getLabel()
        subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
        channelResults = self.channels.get(name)
        for result in channelResults:
            if result: items.append(self.makeItem(result))
        self.RESULTS.reset()
        self.RESULTS.addItems(items)
        self.RESULTS.selectItem(subpos)

    def loadEpisodes(self ,item):
        try:
            self.channel = platformtools.channel_import(item.channel)
            self.itemsResult = getattr(self.channel, item.action)(item)
        except:
            import traceback
            logger.error('error importing/getting search items of ' + item.channel)
            logger.error(traceback.format_exc())
            self.itemsResult = []

        self.episodes = self.itemsResult if self.itemsResult else []
        self.itemsResult = []
        ep = []
        isnext = False

        for e in self.episodes:
            if e.action in ['findvideos']:
                ep.append(self.makeItem(e))
            if e.nextSeason and e.action in ['episodios']:
                self.nextAction = e.clone()
                isnext = True

        if self.nextAction:
            self.next = None
            self.previous = None
            if isnext:
                self.next = self.nextAction.clone()
            if self.nextAction.nextSeason > 1 or not self.next:
                self.previous = self.nextAction.clone(nextSeason = self.nextAction.nextSeason - 2 if self.next else 0)

        self.NEXT.setVisible(True if self.next else False)
        self.PREV.setVisible(True if self.previous else False)

        if not ep:
            ep = [xbmcgui.ListItem(config.get_localized_string(60347))]
            ep[0].setArt({'poster', support.thumb('nofolder')})

        self.Focus(EPISODES)
        self.EPISODESLIST.reset()
        self.EPISODESLIST.addItems(ep)
        self.setFocusId(EPISODESLIST)

    def Back(self):
        if self.EPISODES.isVisible():
            self.episodes = []
            self.Focus(SEARCH)
            self.setFocusId(RESULTS)
            self.RESULTS.selectItem(self.pos)
        else:
            self.Close()

    def Close(self):
        self.exit = True
        if self.thread:
            platformtools.dialog_busy(True)
            for th in self.search_threads:
                th.cancel()
            self.thread.join()
            platformtools.dialog_busy(False)
        self.close()

    def context(self):
        focus = self.getFocusId()
        if focus == EPISODESLIST:  # context on episode
            item_url = self.EPISODESLIST.getSelectedItem().getProperty('item')
            parent = Item().fromurl(self.RESULTS.getSelectedItem().getProperty('item'))
        else:
            item_url = self.RESULTS.getSelectedItem().getProperty('item')
            parent = self.item
        item = Item().fromurl(item_url)
        parent.noMainMenu = True
        commands = platformtools.set_context_commands(item, item_url, parent)
        context = [c[0] for c in commands]
        context_commands = [c[1].replace('Container.Refresh', 'RunPlugin').replace('Container.Update', 'RunPlugin').replace(')','&no_reload=True)') for c in commands]
        index = xbmcgui.Dialog().contextmenu(context)
        self.reload = True

        xbmc.executebuiltin(context_commands[index])
        # if index > 0: xbmc.executebuiltin(context_commands[index])

