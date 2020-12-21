# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# autorenumber - Rinumera Automaticamente gli Episodi
# --------------------------------------------------------------------------------


import xbmc, xbmcgui, re, base64, inspect, sys
from core import jsontools, tvdb, scrapertools, filetools
from core.item import Item
from core.support import typo, match, dbg, Item
from platformcode import config, platformtools, logger
PY3 = True if sys.version_info[0] >= 3 else False

# Json Var
TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
ID = "ID"
SEASON = "Season"
EPISODE = "Episode"
SPECIAL = "Special"
MODE = "Mode"
EPLIST = "EpList"
CHECK = "ReCheck"
SPLIST = "SpList"
TYPE = "Type"

# helper Functions
def check(item):
    logger.debug()
    dict_series = load(item)
    title = item.fulltitle.rstrip()
    if title in dict_series: title = dict_series[title]
    return True if ID in title and EPISODE in title else False

def filename(item):
    logger.debug()
    name_file = item.channel + "_data.json"
    path = filetools.join(config.get_data_path(), "settings_channels")
    fname = filetools.join(path, name_file)
    return fname


def load(item):
    logger.debug()
    try:
        json_file = open(filename(item), "r").read()
        json = jsontools.load(json_file)[TVSHOW_RENUMERATE]

    except:
        json = {}

    return json


def write(item, json):
    logger.debug()
    json_file = open(filename(item), "r").read()
    js = jsontools.load(json_file)
    js[TVSHOW_RENUMERATE] = json
    with open(filename(item), "w") as file:
        file.write(jsontools.dump(js))
        file.close()

def b64(json, mode = 'encode'):
    if PY3: json = bytes(json, 'ascii')
    if mode == 'encode':
        ret = base64.b64encode(json)
        if PY3: ret = ret.decode()
    else:
        ret = jsontools.load(base64.b64decode(json))
    return ret

def RepresentsInt(s):
    # Controllo Numro Stagione
    logger.debug()
    try:
        int(s)
        return True
    except ValueError:
        return False

def find_episodes(item):
    logger.debug()
    ch = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
    itemlist = ch.episodios(item)
    return itemlist

def busy(state):
    if state: xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    else: xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

# Main
def start(itemlist, item=None):
    if not itemlist: return
    if type(itemlist) == Item:
        item = itemlist
        if item.channel in ['autorenumber']:
            item.channel = item.from_channel
            item.action = item.from_action
            item.renumber = True
        busy(True)
        itemlist = find_episodes(item)
        busy(False)
    return autorenumber(itemlist, item)

class autorenumber():
    def __init__(self, itemlist, item=None):
        self.item = item
        self.itemlist = itemlist
        self.auto = False
        self.dictSeries = load(self.itemlist[0]) if self.itemlist else load(item) if item else {}
        self.Episodes = {}
        self.sp = False
        if self.item:
            self.auto = config.get_setting('autorenumber', item.channel)
            self.title = self.item.fulltitle.strip()
            if match(self.itemlist[0].title, patron=r'[Ss]?(\d+)(?:x|_|\s+)[Ee]?[Pp]?(\d+)').match:
                item.exit = True
                return 
            elif self.item.channel in self.item.channel_prefs and TVSHOW_RENUMERATE in self.item.channel_prefs[item.channel] and self.title not in self.dictSeries:
                from core.videolibrarytools import check_renumber_options
                from specials.videolibrary import update_videolibrary
                check_renumber_options(self.item)
                update_videolibrary(self.item)
            if self.title in self.dictSeries and ID in self.dictSeries[self.title] and self.dictSeries[self.title][ID] != '0':
                self.id = self.dictSeries[self.title][ID]
                self.Episodes = b64(self.dictSeries[self.title][EPISODE], 'decode') if EPISODE in self.dictSeries[self.title] else {}
                self.Season = self.dictSeries[self.title][SEASON]
                self.Mode = self.dictSeries[self.title].get(MODE, False)
                self.Type = self.dictSeries[self.title].get(TYPE, False)
                if self.item.renumber:
                    self.config()
                else:
                    self.renumber()
            elif self.auto or self.item.renumber:
                self.Episodes = {}
                self.config()

        else:
            for item in self.itemlist:
                item.context = [{"title": typo(config.get_localized_string(70585), 'bold'),
                                "action": "start",
                                "channel": "autorenumber",
                                "from_channel": item.channel,
                                "from_action": item.action}]

    def config(self):
        self.id = ''
        if self.title in self.dictSeries:
            self.id = self.dictSeries[self.title].get(ID,'')

        # Pulizia del Titolo
        if any( word in self.title.lower() for word in ['specials', 'speciali']):
            self.title = re.sub(r'\s*specials|\s*speciali', '', self.title.lower())
        elif not self.item.infoLabels['tvdb_id']:
            self.item.contentSerieName = self.title.rstrip('123456789 ')

        while not self.item.exit:
            tvdb.find_and_set_infoLabels(self.item)
            if self.item.infoLabels['tvdb_id']: self.item.exit = True
            else: self.item = platformtools.dialog_info(self.item, 'tvdb')

        # Rinumerazione Automatica
        if (not self.id and self.auto) or self.item.renumber:
            self.id = self.item.infoLabels['tvdb_id'] if 'tvdb_id' in self.item.infoLabels else ''
            if self.id:
                self.dictRenumber = {ID: self.id}
                self.dictSeries[self.title] = self.dictRenumber
                if any(word in self.title.lower() for word in ['specials', 'speciali']): season = '0'
                elif RepresentsInt(self.title.split()[-1]): season = self.title.split()[-1]
                else: season = '1'
                self.Season = self.dictRenumber[SEASON] = season
                self.renumber()

    def renumber(self):
        if not self.item.renumber and self.itemlist:
            if '|' in self.Season:
                season = int(self.Season.split('|')[0])
                addNumber = int(self.Season.split('|')[-1]) - 1
            else:
                season = int(self.Season)
                addNumber = 0
            for item in self.itemlist:
                if not match(item.title, patron=r'[Ss]?(\d+)(?:x|_|\s+)[Ee]?[Pp]?(\d+)').match:
                    number = match(item.title, patron=r'(\d+)').match.lstrip('0')
                    if number:
                        if number in self.Episodes:
                            if season > 0: item.title = typo(self.Episodes[number] + ' - ', 'bold') + item.title
                            else: item.title = typo('0x%s - ' % str(int(number) + addNumber), 'bold') + item.title
                        else:
                            self.makelist()
                            if season > 0: item.title = typo(self.Episodes[number] + ' - ', 'bold') + item.title
                            else: item.title = typo('0x%s - ' % str(int(number) + addNumber), 'bold') + item.title
        else:
            self.makelist()


    def makelist(self):
        FirstOfSeason= 0
        self.EpList = b64(self.dictSeries[self.title][EPLIST], 'decode') if EPLIST in self.dictSeries[self.title] else []
        self.Pages = self.dictSeries[self.title].get(CHECK, [1])
        self.Mode = self.dictSeries[self.title].get(MODE, False)
        self.Type = self.dictSeries[self.title].get(TYPE, False)
        Specials = {}
        Seasons = {}

        if '|' in self.Season:
            ep = int(self.Season.split('|')[-1])
            season = int(self.Season.split('|')[0])
        else:
            season = int(self.Season)
            ep = 1

        busy(True)
        itemlist = find_episodes(self.item)
        busy(False)

        if self.item.renumber:
            self.s = season
            self.e = 1
            Season, Episode, self.Mode, Specials, Seasons, Exit = SelectreNumeration(self, itemlist)
            if Exit: return
            if ep != 1: self.Season = '%s|%s' % (Season, Episode)
            else: self.Season = str(Season)

        elif self.Episodes and not self.Mode:
            self.s = season
            self.e = ep
            self.sp = True
            Season, Episode, self.Mode, Specials, Seasons, Exit = SelectreNumeration(self, itemlist)

        if self.Mode:
            if not Seasons:
                self.s = 1
                self.e = 1
                Season, Episode, self.Mode, Specials, Seasons, Exit = SelectreNumeration(self, itemlist, True)
            self.Episodes = Seasons

        else:
            # Ricava Informazioni da TVDB
            checkpages = []
            exist = True
            Page = self.Pages[-1]
            Episode = ep

            while exist:
                data = tvdb.Tvdb(tvdb_id=self.id).get_list_episodes(self.id, Page)
                if data:
                    for episode in data['data']:
                        if episode['firstAired'] and [episode['firstAired'], episode['airedSeason'], episode['airedEpisodeNumber']] not in self.EpList:
                            self.EpList.append([episode['firstAired'], episode['airedSeason'], episode['airedEpisodeNumber']])
                    Page += 1
                else:
                    if Page not in checkpages:
                        checkpages.append(Page -1)
                    exist = False
            self.Pages = [checkpages[-1]]
            self.EpList.sort()

            # Crea Dizionari per la Rinumerazione
            if self.EpList:
                self.specials = []
                self.regular = {}
                self.complete = {}
                allep = 1
                specialep = 0

                for episode in self.EpList:
                    self.complete[allep] = [str(episode[1]) + 'x' + str(episode[2]), episode[0]]
                    if episode[1] == 0:
                        self.specials.append(allep)
                        specialep = specialep + 1
                    else:
                        self.regular[ep] = [str(episode[1]) + 'x' + str(episode[2]), str(episode[0]), allep - 1]
                        ep = ep + 1
                    allep = allep + 1

            if season > 1:
                for numbers, data in self.regular.items():
                    if data[0] == str(season) + 'x1':
                        FirstOfSeason = numbers - 1
            else: FirstOfSeason = Episode - 1

            addiction = 0
            for item in itemlist:
                if not match(re.sub(r'\[[^\]]+\]','',item.title), patron=r'[Ss]?(\d+)(?:x|_|\s+)[Ee]?[Pp]?(\d+)').match:
                    # Otiene Numerazione Episodi
                    scraped_ep = match(re.sub(r'\[[^\]]+\]','',item.title), patron=r'(\d+)').match
                    if scraped_ep:
                        episode = int(scraped_ep)
                        number = episode + FirstOfSeason - addiction
                        if episode == 0:
                            self.Episodes[str(episode)] = str(self.complete[self.regular[FirstOfSeason+1][2]][0])
                        elif episode in Specials:
                                self.Episodes[str(episode)] = Specials[episode]
                                addiction +=  1
                        elif number <= len(self.regular) and number in self.regular:
                            self.Episodes[str(episode)] = str(self.regular[number][0])
                        else:
                            try: Episodes[str(episode)] = str(self.complete[self.regular[number+2][2]][0])
                            except: self.Episodes[str(episode)] = '0x0'

        if self.Episodes: self.dictSeries[self.title][EPISODE] = b64(jsontools.dump(self.Episodes))
        self.dictSeries[self.title][EPLIST] = b64(jsontools.dump(self.EpList))
        self.dictSeries[self.title][MODE] = self.Mode
        self.dictSeries[self.title][SEASON] = self.Season
        self.dictSeries[self.title][CHECK] = self.Pages
        write(self.item, self.dictSeries)

        if self.auto: self.renumber()


def SelectreNumeration(opt, itemlist, manual=False):
    class SelectreNumerationWindow(xbmcgui.WindowXMLDialog):
        def start(self, opt):
            self.episodes = opt.Episodes if opt.Episodes else {}
            self.dictSeries = opt.dictSeries
            self.item = opt.item
            self.title = opt.title
            self.season = opt.s
            self.episode = opt.e
            self.mode = opt.Mode
            self.sp = opt.sp
            self.manual = opt.manual
            self.offset = 0
            self.Exit = False

            self.itemlist = opt.itemlist
            self.count = 1
            self.specials = {}
            self.items = []
            self.selected = []
            self.seasons = {}

            self.doModal()
            return self.season, self.episode, self.mode, self.specials, self.seasons, self.Exit

        def onInit(self):
            # Compatibility with Kodi 18
            if config.get_platform(True)['num_version'] < 18: self.setCoordinateResolution(2)
            fanart = self.item.fanart
            thumb = self.item.thumbnail
            self.getControl(SELECT).setVisible(False)
            self.getControl(SPECIALS).setVisible(False)
            self.getControl(MANUAL).setVisible(False)
            # MANUAL
            if self.manual:
                self.getControl(MANUAL).setVisible(True)
                self.getControl(MPOSTER).setImage(thumb)
                if fanart: self.getControl(MBACKGROUND).setImage(fanart)
                self.getControl(INFO).setLabel(typo(config.get_localized_string(70822) + self.title, 'bold'))

                self.mode = True

                se = '1'
                ep = '1'
                position = 0
                for i, item in enumerate(self.itemlist):
                    title = match(item.title, patron=r'(\d+)').match.lstrip('0')
                    it = xbmcgui.ListItem(title)
                    if int(title) <= len(self.episodes):
                        se, ep = self.episodes[title].split('x')
                    else:
                        if position == 0: position = i
                        ep = str(int(ep) + 1)
                    it.setProperties({'season': se, "episode": ep})
                    self.items.append(it)
                self.makerenumber()
                self.addseasons()
                season = self.getControl(MSEASONS).getSelectedItem().getLabel()
                self.getControl(MSEP).reset()
                self.getControl(MSEP).addItems(self.episodes[season])
                self.getControl(MLIST).addItems(self.items)
                self.setFocusId(MLIST)
                self.getControl(MLIST).selectItem(position)
            # MAIN / SPECIALS
            else:
                for item in self.itemlist:
                    if not match(item.title, patron=r'[Ss]?(\d+)(?:x|_|\s+)[Ee]?[Pp]?(\d+)').match:
                        title = match(item.title, patron=r'(\d+)').match.lstrip('0')
                        it = xbmcgui.ListItem(title)
                        self.items.append(it)

                self.getControl(POSTER).setImage(thumb)
                self.getControl(MPOSTER).setImage(thumb)
                if fanart:
                    self.getControl(BACKGROUND).setImage(fanart)
                    self.getControl(MBACKGROUND).setImage(fanart)
                self.getControl(INFO).setLabel(typo(config.get_localized_string(70824) + self.title, 'bold'))
                self.getControl(LIST).addItems(self.items)

                if self.sp:
                    self.getControl(SPECIALS).setVisible(True)
                    self.setFocusId(OK)
                else:
                    self.getControl(SELECT).setVisible(True)

                    self.getControl(S).setLabel(str(self.season))
                    self.getControl(E).setLabel(str(self.episode))

                    self.setFocusId(O)

        def onFocus(self, focus):
            if focus in [S]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70825), 'bold'))
            elif focus in [E]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70826), 'bold'))
            elif focus in [O]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70001), 'bold'))
            elif focus in [SS]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70827), 'bold'))
            elif focus in [M]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70828), 'bold'))
            elif focus in [D]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70829) + self.title, 'bold'))
            elif focus in [C]:
                self.getControl(108).setLabel(typo(config.get_localized_string(70002), 'bold'))

        def onAction(self, action):
            action = action.getId()
            focus = self.getFocusId()
            # SEASON SELECT
            if 100 < focus < 200:
                s = int(self.getControl(S).getLabel())
                e = int(self.getControl(E).getLabel())
                if action in [RIGHT]:
                    if focus in [C]:
                        self.setFocusId(S)
                    else:
                        self.setFocusId(focus + 1)
                elif action in [LEFT]:
                    if focus in [S]:
                        self.setFocusId(C)
                    else:
                        self.setFocusId(focus - 1)
                elif action in [UP]:
                    if focus in [S]:
                        s += 1
                        self.getControl(S).setLabel(str(s))
                    elif focus in [E]:
                        e += 1
                        self.getControl(E).setLabel(str(e))
                elif action in [DOWN]:
                    if focus in [S]:
                        if s > 0: s -= 1
                        self.getControl(S).setLabel(str(s))
                    elif focus in [E]:
                        if e > 0: e -= 1
                        self.getControl(E).setLabel(str(e))
            # MANUAL
            if focus in [MS, ME]:
                s = int(self.getControl(MLIST).getSelectedItem().getProperty('season'))
                e = int(self.getControl(MLIST).getSelectedItem().getProperty('episode'))
                pos = self.getControl(MLIST).getSelectedPosition()
                # Set Season
                if focus in [MS] and action in [UP]:
                    s += 1
                elif focus in [MS] and action in [DOWN] and s > 0:
                    s -= 1
                # Set Episode
                if focus in [ME] and action in [UP]:
                    e += 1
                elif focus in [ME] and action in [DOWN] and e > 0:
                    e -= 1
                if action in [UP, DOWN]:
                    if s != self.season: e = 1
                    self.season = s
                    self.episode = e
                    self.makerenumber(pos)
                    self.addseasons()
                    season = self.getControl(MSEASONS).getSelectedItem().getLabel()
                    self.getControl(MSEP).reset()
                    self.getControl(MSEP).addItems(self.episodes[season])
                    self.getControl(MLIST).reset()
                    self.getControl(MLIST).addItems(self.items)
                    self.getControl(MLIST).selectItem(pos)
            if focus in [MSEASONS]:
                season = self.getControl(MSEASONS).getSelectedItem().getLabel()
                self.getControl(MSEP).reset()
                self.getControl(MSEP).addItems(self.episodes[season])

            # EXIT
            if action in [EXIT, BACKSPACE]:
                self.Exit = True
                self.close()

        def onClick(self, control_id):
            ## FIRST SECTION
            if control_id in [S]:
                selected = platformtools.dialog_numeric(0, config.get_localized_string(70825),
                                                        self.getControl(S).getLabel())
                if selected: s = self.getControl(S).setLabel(selected)
            elif control_id in [E]:
                selected = platformtools.dialog_numeric(0, config.get_localized_string(70826),
                                                        self.getControl(E).getLabel())
                if selected: e = self.getControl(E).setLabel(selected)
            # OPEN SPECIALS OR OK
            if control_id in [O, SS]:
                s = self.getControl(S).getLabel()
                e = self.getControl(E).getLabel()
                self.season = int(s)
                self.episode = int(e)
                if control_id in [O]:
                    self.close()
                elif control_id in [SS]:
                    self.getControl(SELECT).setVisible(False)
                    self.getControl(SPECIALS).setVisible(True)
                    self.setFocusId(OK)
            # OPEN MANUAL
            elif control_id in [M]:
                self.getControl(INFO).setLabel(typo(config.get_localized_string(70823) + self.title, 'bold'))
                self.mode = True
                if self.episodes:
                    items = []
                    se = '1'
                    ep = '1'
                    for item in self.items:
                        if int(item.getLabel()) <= len(self.episodes) - 1:
                            se, ep = self.episodes[item.getLabel()].split('x')
                        else:
                            ep = str(int(ep) + 1)
                        item.setProperties({'season': se, "episode": ep})
                        items.append(item)
                        self.seasons[item.getLabel()] = '%sx%s' % (se, ep)
                    self.items = items
                else:
                    self.makerenumber()
                self.addseasons()
                season = self.getControl(MSEASONS).getSelectedItem().getLabel()
                self.getControl(MSEP).reset()
                self.getControl(MSEP).addItems(self.episodes[season])
                self.getControl(MLIST).addItems(self.items)
                self.getControl(SELECT).setVisible(False)
                self.getControl(MANUAL).setVisible(True)
                self.setFocusId(OK)
            # CLOSE
            elif control_id in [C]:
                self.Exit = True
                self.close()
            # DELETE
            if control_id in [D]:
                self.Exit = True
                self.dictSeries.pop(self.title)
                write(self.item, self.dictSeries)
                self.close()

            ## SPECIAL SECTION
            # ADD TO SPECIALS
            p1 = self.getControl(SELECTED).getSelectedPosition()
            if control_id in [LIST]:
                item = self.getControl(LIST).getSelectedItem()
                it = xbmcgui.ListItem(str(len(self.selected) + 1))
                it.setProperty('title', item.getLabel())
                self.selected.append(it)
                index = self.getControl(SELECTED).getSelectedPosition()
                self.getControl(SELECTED).reset()
                self.getControl(SELECTED).addItems(self.selected)
                self.getControl(SELECTED).selectItem(index)

                index = self.getControl(LIST).getSelectedPosition()
                self.items.pop(index)
                self.getControl(LIST).reset()
                self.getControl(LIST).addItems(self.items)
                if index == len(self.items): index -= 1
                self.getControl(LIST).selectItem(index)
            # MOVE SPECIALS
            elif control_id in [SU]:
                p2 = p1 - 1
                if p2 > -1:
                    self.selected[p1], self.selected[p2] = self.selected[p2], self.selected[p1]
                    for i, it in enumerate(self.selected):
                        it.setLabel(str(i + 1))
                        break
                    self.getControl(SELECTED).reset()
                    self.getControl(SELECTED).addItems(self.selected)
                    self.getControl(SELECTED).selectItem(p2)

            elif control_id in [SD]:
                p2 = p1 + 1
                if p2 < len(self.selected):
                    self.selected[p1], self.selected[p2] = self.selected[p2], self.selected[p1]
                    for i, it in enumerate(self.selected):
                        it.setLabel(str(i + 1))
                        break
                    self.getControl(SELECTED).reset()
                    self.getControl(SELECTED).addItems(self.selected)
                    self.getControl(SELECTED).selectItem(p2)
            # REMOVE FROM SPECIALS
            elif control_id in [SR]:
                item = self.getControl(SELECTED).getSelectedItem()
                it = xbmcgui.ListItem(item.getProperty('title'))
                if int(item.getProperty('title')) < int(self.items[-1].getLabel()):
                    for i, itm in enumerate(self.items):
                        if int(itm.getLabel()) > int(item.getProperty('title')):
                            self.items.insert(i, it)
                            break
                else:
                    self.items.append(it)
                self.getControl(LIST).reset()
                self.getControl(LIST).addItems(self.items)
                index = self.getControl(SELECTED).getSelectedPosition()
                self.selected.pop(index)
                self.getControl(SELECTED).reset()
                self.getControl(SELECTED).addItems(self.selected)

                if index == len(self.selected): index -= 1
                self.getControl(SELECTED).selectItem(index)
            # RELOAD SPECIALS
            if control_id in [SELECTED]:
                epnumber = platformtools.dialog_numeric(0, config.get_localized_string(60386))
                it = self.getControl(SELECTED).getSelectedItem()
                it.setLabel(str(epnumber))
                self.selected.sort(key=lambda it: int(it.getLabel()))
                for i, it in enumerate(self.selected):
                    if it.getLabel() == epnumber: pos = i
                    self.selected.sort(key=lambda it: int(it.getLabel()))
                    self.getControl(SELECTED).reset()
                    self.getControl(SELECTED).addItems(self.selected)
                    self.getControl(SELECTED).selectItem(pos)
                    break
            if len(self.selected) > 0:
                self.getControl(SPECIALCOMMANDS).setVisible(True)
            else:
                self.getControl(SPECIALCOMMANDS).setVisible(False)

            ## MANUAL SECTION
            # SELECT SEASON EPISODE (MANUAL)
            if control_id in [MS, ME]:
                s = int(self.getControl(MLIST).getSelectedItem().getProperty('season'))
                e = int(self.getControl(MLIST).getSelectedItem().getProperty('episode'))
                pos = self.getControl(MLIST).getSelectedPosition()
                if control_id in [MS]:
                    selected = platformtools.dialog_numeric(0, config.get_localized_string(70825), str(s))
                    if selected: s = int(selected)
                elif control_id in [ME]:
                    selected = platformtools.dialog_numeric(0, config.get_localized_string(70826), str(e))
                    if selected: e = int(selected)
                if s != self.season or e != self.episode:
                    self.season = s
                    self.episode = 1 if s != self.season else e
                    self.makerenumber(pos)
                    self.addseasons()
                    season = self.getControl(MSEASONS).getSelectedItem().getLabel()
                    self.getControl(MSEP).reset()
                    self.getControl(MSEP).addItems(self.episodes[season])
                    self.getControl(MLIST).reset()
                    self.getControl(MLIST).addItems(self.items)
                    self.getControl(MLIST).selectItem(pos)
            # OK
            if control_id in [OK]:
                for it in self.selected:
                    self.specials[int(it.getProperty('title'))] = '0x' + it.getLabel()
                self.close()
            # CLOSE
            elif control_id in [CLOSE]:
                self.Exit = True
                self.close()

        def makerenumber(self, pos=0):
            items = []
            currentSeason = self.items[pos].getProperty('season')
            previousSeason = self.items[pos - 1 if pos > 0 else 0].getProperty('season')
            prevEpisode = self.items[pos - 1 if pos > 0 else 0].getProperty('episode')
            if currentSeason != str(self.season):
                if str(self.season) == previousSeason:
                    prevEpisode = int(prevEpisode) + 1
                else:
                    prevEpisode = 1
            else:
                prevEpisode = self.episode

            for i, item in enumerate(self.items):
                if (i >= pos and item.getProperty('season') == currentSeason) or not item.getProperty('season'):
                    if i > pos: prevEpisode += 1
                    item.setProperties({'season': self.season, 'episode': prevEpisode})
                items.append(item)
                self.seasons[item.getLabel()] = '%sx%s' % (item.getProperty('season'), item.getProperty('episode'))
            self.items = items
            logger.debug('SELF', self.seasons)

        def addseasons(self):
            seasonlist = []
            seasons = []
            self.episodes = {}
            for ep, value in self.seasons.items():
                season = value.split('x')[0]
                if season not in seasonlist:
                    item = xbmcgui.ListItem(season)
                    seasonlist.append(season)
                    seasons.append(item)
                if season in seasonlist:
                    if season not in self.episodes:
                        self.episodes[season] = []
                    item = xbmcgui.ListItem('%s - Ep. %s' % (value, ep))
                    item.setProperty('episode', ep)
                    self.episodes[season].append(item)
                    logger.log('EPISODES', self.episodes[season])
                self.episodes[season].sort(key=lambda it: int(it.getProperty('episode')))

            seasons.sort(key=lambda it: int(it.getLabel()))
            self.getControl(MSEASONS).reset()
            self.getControl(MSEASONS).addItems(seasons)

    opt.itemlist = itemlist
    opt.manual = manual
    return SelectreNumerationWindow('Renumber.xml', path).start(opt)

# Select Season
SELECT = 100
S = 101
E = 102
O = 103
SS = 104
M = 105
D = 106
C = 107

# Main
MAIN = 10000
INFO = 10001
OK=10002
CLOSE = 10003

# Select Specials
SPECIALS = 200
POSTER= 201
LIST = 202
SELECTED = 203
BACKGROUND = 208

SPECIALCOMMANDS = 204
SU = 205
SD = 206
SR = 207

# Select Manual
MANUAL = 300
MPOSTER= 301
MLIST = 302
MSEASONS = 303
MSEP = 304
MBACKGROUND = 310

MANUALEP = 305
MS = 306
ME = 307
MSS = 308
MC = 309

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92

path = config.get_runtime_path()
