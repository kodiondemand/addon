# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# infoplus window with item information
# ------------------------------------------------------------
import xbmc, xbmcgui, sys, requests, re
from core import support, tmdb, filetools, channeltools, servertools
from core.item import Item
from platformcode import config, platformtools
from platformcode.logger import log
from core.scrapertools import decodeHtmlentities, htmlclean

PY3 = False
if sys.version_info[0] >= 3: PY3 = True
if PY3: from concurrent import futures
else: from concurrent_py2 import futures

info_list = []
SearchWindows = []
api = 'k_0tdb8a8y'

# Control ID
FANART = 30000
NUMBER = 30001
TITLE = 30002
TAGLINE = 30003
PLOT = 30004
RATING_ICON = 30005
RATING = 30006
TRAILER = 30007
SEARCH = 30008
NEXT = 30009
PREVIOUS = 30010
LOADING = 30011
COMMANDS = 30012
IMAGES = 30013
RECOMANDED = TRAILERS = 30500
ACTORS = 30501
CAST = 30502

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92



def Main(item):
    if type(item) == Item:
        item.channel = item.from_channel
        global ITEM
        ITEM = item
        Info = xbmcgui.ListItem(item.infoLabels['title'])
        for key, value in item.infoLabels.items():
            Info.setProperty(key, str(value))
    else:
        Info = item

    main = MainWindow('InfoPlus.xml', config.get_runtime_path())
    add({'class':main, 'info':Info, 'id':RECOMANDED, RECOMANDED:0, ACTORS:0})
    modal()

class MainWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []
        self.cast = []
        self.actors = []
        self.ids = {}
        self.tmdb = []

    def onInit(self):
        #### Compatibility with Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        if Info.getProperty('id'):self.items = get_movies(Info)
        else: self.items = get_recomendations(Info)
        self.cast, self.actors = get_cast(Info)
        self.getControl(LOADING).setVisible(False)
        self.getControl(RECOMANDED).addItems(self.items)
        self.getControl(FANART).setImage(Info.getProperty('fanart'))
        self.getControl(ACTORS).addItems(self.actors)
        if self.cast:
            self.getControl(CAST).setVisible(True)
            self.getControl(CAST).addItems(self.cast)
        else:
            self.getControl(CAST).setVisible(False)
        if Info.getProperty('rating'): rating = str(Info.getProperty('rating'))
        else: rating = 'N/A'
        self.getControl(RATING).setText(rating)
        getFocus(self)

    def onClick(self, control_id):
        setFocus(self)
        title = self.getControl(RECOMANDED).getSelectedItem().getProperty('title')
        mode = self.getControl(RECOMANDED).getSelectedItem().getProperty('mediatype')
        if control_id in [SEARCH]:
            self.close()
            if self.getControl(RECOMANDED).getSelectedPosition() > 0:
                Search(ITEM.clone(action='search', search_text=title))
            else:
                Search(ITEM.clone(channel='search', action='new_search', search_text=title, mode=mode))
        elif control_id in [TRAILER]:
            info = self.getControl(RECOMANDED).getSelectedItem()
            self.close()
            Trailer(info)
        elif control_id in [IMAGES]:
            info = self.getControl(RECOMANDED).getSelectedItem()
            images = tmdb.Tmdb(id_Tmdb=info.getProperty('tmdb_id'), search_type='movie' if mode == 'movie' else 'tv').result.get("images", {})
            for key, value in list(images.items()):
                if not value: images.pop(key)
            ImagesWindow(tmdb = images).doModal()
        elif control_id in [ACTORS, CAST]:
            self.close()
            Main(self.getControl(self.getFocusId()).getSelectedItem())
        elif control_id in [RECOMANDED] and self.getControl(RECOMANDED).getSelectedPosition() > 0:
            self.close()
            Main(self.getControl(RECOMANDED).getSelectedItem())

    def onAction(self, action):
        if self.getFocusId() in [ACTORS, RECOMANDED]:
            self.ids[self.getFocusId()] = self.getControl(self.getFocusId()).getSelectedPosition()
        if self.getFocusId() in [ACTORS, CAST] and action not in [BACKSPACE, EXIT]:
            actors_more_info(self.getControl(self.getFocusId()).getSelectedItem())
        if self.getFocusId() in [RECOMANDED]:
            fanart = self.getControl(self.getFocusId()).getSelectedItem().getProperty('fanart')
            rating = self.getControl(self.getFocusId()).getSelectedItem().getProperty('rating')
            if not rating: rating = 'N/A'
            self.getControl(FANART).setImage(fanart)
            self.getControl(RATING).setText(rating)
            cast, actors = get_cast(self.getControl(self.getFocusId()).getSelectedItem())
            self.getControl(ACTORS).reset()
            self.getControl(ACTORS).addItems(actors)
            self.getControl(CAST).reset()
            self.getControl(CAST).addItems(cast)
        action = action.getId()
        if action in [BACKSPACE]:
            self.close()
            remove()
            modal()
        elif action in [EXIT]:
            self.close()


def Search(item):
    if item.action == 'findvideos': XML = 'ServersWindow.xml'
    else: XML = 'SearchWindow.xml'
    global Info
    Info = item
    main = SearchWindow(XML, config.get_runtime_path())
    add({'class':main, 'info':item, 'id':RECOMANDED})
    modal()

class SearchWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []
        self.itemlist = []
        self.commands = []
        self.ids = {}
        self.channel = None

    def onInit(self):
        #### Compatibility with Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        if len(self.items) == 0:
            if Info.action == 'new_search' and Info.mode:
                from specials.search import new_search
                itemlist = new_search(Info)
            elif Info.action == 'channel_search':
                from specials.search import channel_search
                itemlist = channel_search(Info)
            else:
                self.channel = __import__('channels.%s' % Info.channel, fromlist=["channels.%s" % Info.channel])
                if Info.action == 'search': itemlist = getattr(self.channel, 'search')(Info, Info.search_text)
                else: itemlist = getattr(self.channel, Info.action)(Info)
            if not itemlist:
                if platformtools.dialog_yesno(config.get_localized_string(60473), config.get_localized_string(70820) % Info.channel):
                    remove()
                    self.close()
                    return Search(Info.clone(mode=Info.infoLabels['mediatype']))
                else:
                    remove()
                    self.close()
                    modal()
            for item in itemlist:
                if item.action not in ['save_download', 'add_pelicula_to_library', 'add_serie_to_library', ''] and item.infoLabels['title']:
                    if item.action == 'findvideos' and item.contentType in ['episode', 'tvshow']:
                        it = xbmcgui.ListItem(re.sub(r'\[[^\]]+\]', '', item.title))
                        self.getControl(NUMBER).setText(support.typo(config.get_localized_string(70362),'uppercase bold'))
                    else:
                        it = xbmcgui.ListItem(item.infoLabels['title'])
                    it.setProperty('channelname', channeltools.get_channel_parameters(item.channel).get('title',''))
                    it.setProperty('channel', item.channel)
                    it.setProperty('action', item.action)
                    it.setProperty('server', servertools.get_server_parameters(item.server.lower()).get('name',item.server))
                    it.setProperty('url', item.url)
                    for key, value in item.infoLabels.items():
                        it.setProperty(key, str(value))
                    if item.action == 'play':
                        it.setProperty('thumbnail', "https://raw.githubusercontent.com/kodiondemand/media/master/resources/servers/%s.png" % item.server.lower())
                    self.items.append(it)
                    self.itemlist.append(item)
            if itemlist[0].contentType == 'movie':
                if not itemlist[0].server:
                    self.commands.append(itemlist[0].clone(action='add_pelicula_to_library',  thumbnail=support.thumb('add_to_videolibrary')))
                    self.commands.append(itemlist[0].clone(channel='downloads', action='save_download', from_channel=itemlist[0].channel, from_action=itemlist[0].action, thumbnail=support.thumb('downloads')))
                else:
                    self.commands.append(Info.clone(channel='downloads', action='save_download', from_channel=Info.channel, from_action=Info.action, thumbnail=support.thumb('downloads')))
            if itemlist[0].contentType in ['tvshow', 'episode']:
                if not itemlist[0].server:
                    self.commands.append(itemlist[0].clone(action='add_serie_to_library',  thumbnail=support.thumb('add_to_videolibrary')))
                    self.commands.append(itemlist[0].clone(channel='downloads', action='save_download', from_channel=itemlist[0].channel, from_action=itemlist[0].action, thumbnail=support.thumb('downloads')))
                else:
                    self.commands.append(Info.clone(channel='downloads', action='save_download', from_channel=Info.channel, from_action=Info.action, thumbnail=support.thumb('downloads')))
            if self.commands:
                commands = []
                for command in self.commands:
                    it = xbmcgui.ListItem(command.title)
                    path = filetools.join(config.get_runtime_path(),'resources','skins','Default','media','Infoplus',command.thumbnail.split('/')[-1].replace('thumb_',''))
                    it.setProperty('thumbnail',path)
                    commands.append(it)
                self.getControl(COMMANDS).addItems(commands)
            if self.items:
                self.getControl(FANART).setImage(self.items[0].getProperty('fanart'))

            self.getControl(RECOMANDED).addItems(self.items)
            self.getControl(LOADING).setVisible(False)
            getFocus(self)

    def onClick(self, control_id):
        setFocus(self)
        if control_id == COMMANDS:
            from platformcode.launcher import run
            pos = self.getControl(COMMANDS).getSelectedPosition()
            if self.commands[pos].action =='save_download' and self.commands[pos].contentType == 'tvshow':
                actions = [self.commands[-1].clone(), self.commands[-1].clone(download='season')]
                options = [config.get_localized_string(60355),config.get_localized_string(60357)]
                run(actions[platformtools.dialog_select(config.get_localized_string(60498),options)])
            else:
                run(self.commands[pos])
        else:
            action = self.getControl(RECOMANDED).getSelectedItem().getProperty('action')
            channel = self.getControl(RECOMANDED).getSelectedItem().getProperty('channel')
            url = self.getControl(RECOMANDED).getSelectedItem().getProperty('url')
            item = Item(channel=channel, action=action, url=url)
            if action == 'play':
                item.server = self.getControl(RECOMANDED).getSelectedItem().getProperty('server')
                self.close()
                from platformcode.launcher import run
                run(item)
                xbmc.sleep(500)
                while xbmc.Player().isPlaying():
                    xbmc.sleep(500)
                modal()
            elif config.get_setting('autoplay'):
                item.quality = self.getControl(RECOMANDED).getSelectedItem().getProperty('quality')
                getattr(self.channel, item.action)(item)
                self.close()
                xbmc.sleep(500)
                while xbmc.Player().isPlaying():
                    xbmc.sleep(500)
                modal()
            else:
                pos = self.getControl(RECOMANDED).getSelectedPosition()
                self.close()
                if self.itemlist[pos].mode: remove()
                Search(self.itemlist[pos])

    def onAction(self, action):
        if self.getFocusId() in [RECOMANDED]:
            fanart = self.getControl(self.getFocusId()).getSelectedItem().getProperty('fanart')
            self.getControl(FANART).setImage(fanart)
        action = action.getId()
        if action in [BACKSPACE]:
            self.close()
            remove()
            modal()
        elif action in [EXIT]:
            self.close()


def Trailer(info):
    global info_list, trailers
    trailers = []
    trailers_list = []
    Type = info.getProperty('mediatype')
    if Type != "movie": Type = "tv"
    trailers_list = tmdb.Tmdb(id_Tmdb=info.getProperty('tmdb_id'), search_type=Type).get_videos()
    if trailers_list:
        for i, trailer in enumerate(trailers_list):
            item = xbmcgui.ListItem(trailer['name'])
            item.setProperties({'tile':trailer['name'],
                                'url': trailer['url'],
                                'thumbnail': 'http://img.youtube.com/vi/' + trailer['url'].split('=')[-1] + '/0.jpg',
                                'fanart':info.getProperty('fanart'), 
                                'position':'%s/%s' % (i + 1, len(trailers_list))})
            trailers.append(item)
    else: # TRY youtube search
        patron  = r'thumbnails":\[\{"url":"(https://i.ytimg.com/vi[^"]+).*?'
        patron += r'text":"([^"]+).*?'
        patron += r'simpleText":"[^"]+.*?simpleText":"([^"]+).*?'
        patron += r'url":"([^"]+)'
        matches = support.match('https://www.youtube.com/results?search_query=' + info.getProperty('title').replace(' ','+') + '+trailer+ita', patron = patron).matches
        i = 0
        for thumb, title, text, url in matches:
            i += 1
            item = xbmcgui.ListItem(title + ' - '+ text)
            item.setProperties({'tile':title + ' - '+ text, 'url': url, 'thumbnail': thumb, 'fanart':info.getProperty('fanart'), 'position':'%s/%s' % (i, len(matches))})
            trailers.append(item)
    main = TrailerWindow('TrailerWindow.xml', config.get_runtime_path())
    add({'class':main, 'info':trailers, 'id':RECOMANDED, TRAILERS:0})
    modal()

class TrailerWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.ids = {}

    def onInit(self):
        #### Compatibility with Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        self.getControl(FANART).setImage(trailers[0].getProperty('fanart'))
        self.getControl(NUMBER).setText(trailers[0].getProperty('position'))
        self.getControl(TRAILERS).addItems(trailers)
        self.setFocusId(TRAILERS)
        getFocus(self)

    def onClick(self, control_id):
        setFocus(self)
        if control_id in [TRAILERS]:
            selected = self.getControl(TRAILERS).getSelectedItem()
            platformtools.play_video(Item(title=selected.getProperty('title'), action='play', url=selected.getProperty('url'), server='youtube'))
            while not xbmc.Player().isPlaying():
                xbmc.sleep(100)
            self.close()
            while xbmc.Player().isPlaying():
                xbmc.sleep(100)
            modal()

    def onAction(self, action):
        if self.getFocusId() in [TRAILERS]:
            self.ids[self.getFocusId()] = self.getControl(self.getFocusId()).getSelectedPosition()
            fanart = self.getControl(TRAILERS).getSelectedItem().getProperty('fanart')
            position = self.getControl(TRAILERS).getSelectedItem().getProperty('position')
            self.getControl(FANART).setImage(fanart)
            self.getControl(NUMBER).setText(position)
        action = action.getId()
        global info_list
        if action in [BACKSPACE]:
            self.close()
            remove()
            modal()
        elif action in [EXIT]:
            self.close()

class ImagesWindow(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.tmdb = kwargs.get("tmdb", {})
        self.imdb = kwargs.get("imdb", {})
        self.mal = kwargs.get("mal", {})
        self.fanartv = kwargs.get("fanartv", {})

        self.image_list = []

        for key, value in self.tmdb.items():
            for detail in value: self.image_list.append('https://image.tmdb.org/t/p/original' + detail["file_path"])
        for image in self.imdb: self.image_list.append(image["src"])
        for image, title in self.mal: self.image_list.append(image)
        for key, value in self.fanartv.items():
            for image in value: self.image_list.append(image["url"])

        #### Kodi 18 Compatibility ####
        if config.get_platform(True)['num_version'] < 18: self.setCoordinateResolution(2)
        log
        self.background = xbmcgui.ControlImage(0, 0, 1280, 720, imagepath('white'), colorDiffuse='FF232323')
        self.addControl(self.background)
        main_image = self.image_list[0] if self.image_list else ''
        self.main_image = xbmcgui.ControlImage(0, 0, 1280, 720, main_image, 2)
        self.addControl(self.main_image)

        if self.image_list:
            self.counter = xbmcgui.ControlTextBox(1180, 640, 60, 40, 'font13')
            self.addControl(self.counter)
            self.counter.setText('%s/%s' % (1,len(self.image_list)))
        else:
            self.text = xbmcgui.ControlLabel(0, 0, 1280, 720, 'NESSUNA IMMAGINE', 'font13', alignment=2|4)
            self.addControl(self.text)

        self.close_btn = xbmcgui.ControlButton(0, 0, 1280, 720, '' ,'', '')
        self.addControl(self.close_btn)

        if len(self.image_list) > 1:
            # BUTTON LEFT
            self.btn_left = xbmcgui.ControlButton(0, 330, 60, 60, '', imagepath('previous_focus'), imagepath('previous_nofocus'))
            self.addControl(self.btn_left)
            self.btn_left.setAnimations([('WindowOpen', 'effect=slide start=-60,0 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=-60,0 delay=100 time=200')])

            # BUTTON RIGHT
            self.btn_right = xbmcgui.ControlButton(1220, 330, 60, 60, '', imagepath('next_focus'), imagepath('next_nofocus'))
            self.addControl(self.btn_right)
            self.btn_right.setAnimations([('WindowOpen', 'effect=slide start=60,0 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=60,0 delay=100 time=200')])

            self.count = 0

    def onAction(self, action):
        if action in [BACKSPACE, EXIT]:
            self.close()
        if len(self.image_list) > 1:
            if action in [RIGHT, DOWN]:
                self.count += 1
                if self.count > len(self.image_list) -1: self.count = 0
                self.main_image.setImage(self.image_list[self.count])
                self.counter.setText('%s/%s' % (self.count,len(self.image_list)))

            if action in [LEFT, UP]:
                self.count -= 1
                if self.count < 0: self.count = len(self.image_list) -1
                self.main_image.setImage(self.image_list[self.count])
                self.counter.setText('%s/%s' % (self.count,len(self.image_list)))


    def onControl(self, control):
        if len(self.image_list) > 1:
            if control.getId() == self.btn_right.getId():
                self.count += 1
                if self.count > len(self.image_list) -1: self.count = 0
                self.main_image.setImage(self.image_list[self.count])

            elif control.getId()  == self.btn_left.getId():
                self.count -= 1
                if self.count < 0: self.count = len(self.image_list) -1
                self.main_image.setImage(self.image_list[self.count])

            else:
                self.close()
        else:
            self.close()


def get_recomendations(info):
    recommendations = [info]
    Type = info.getProperty('mediatype')
    if Type != "movie": Type = "tv"
    search = {'url': '%s/%s/recommendations' % (Type, info.getProperty('tmdb_id')), 'language': 'it', 'page': 1}
    tmdb_res = tmdb.Tmdb(discover=search, search_type=Type, idioma_Search='it').results
    for result in tmdb_res:
        if Type == 'movie':
            title = result.get("title", '')
            original_title = result.get("original_title", "")
        else:
            title = result.get("name", '')
            original_title  = result.get("original_name", '')
        thumbnail ='https://image.tmdb.org/t/p/w342' + result.get("poster_path", "") if result.get("poster_path", "") else ''
        fanart = 'https://image.tmdb.org/t/p/original' + result.get("backdrop_path", "") if result.get("backdrop_path", "") else ''
        item = xbmcgui.ListItem(title)
        item.setProperties({'title': title,
                            'original_title': original_title,
                            'mediatype': info.getProperty('mediatype'),
                            'tmdb_id': result.get('id', 0),
                            'imdb_id': info.getProperty('imdb_id'),
                            'rating': result.get('vote_average', 0),
                            'plot': result.get('overview', ''),
                            'year': result.get('release_date', '').split('-')[0],
                            'thumbnail': thumbnail,
                            'fanart': fanart})
        recommendations.append(item)
    return recommendations


def get_cast(info):
    cast_list = []
    actors_list = []
    Type = "movie" if info.getProperty('mediatype') == 'movie' else 'tv'
    otmdb = tmdb.Tmdb(id_Tmdb=info.getProperty('tmdb_id'), search_type=Type)
    actors = otmdb.result.get("credits", {}).get("cast", [])
    cast = otmdb.result.get("credits", {}).get("crew", []) if Type == 'movie' else otmdb.result.get("created_by", [])
    for i, crew in enumerate(cast):
        if crew.get('job', '') == 'Director' or Type!= "movie":
            actors.insert(0, crew)
        else:
            res = xbmcgui.ListItem(crew.get('name', ''))
            res.setProperties({'title': crew.get('name', ''),
                               'job': crew.get('job', '') if crew.get('job', '') else crew.get('character',''),
                               'thumbnail': "https://image.tmdb.org/t/p/w342" + crew.get('profile_path', '') if crew.get('profile_path', '')  else '',
                               'department': crew.get('department', ''),
                               'type': Type,
                               'id': crew.get('id', ''),
                               'mediatype': info.getProperty('mediatype')})
            cast_list.append(res)
    for actor in actors:
        res = xbmcgui.ListItem(actor.get('name', ''))
        res.setProperties({'title': actor.get('name', ''),
                           'job': actor.get('job', '') if actor.get('job', '') else actor.get('character',''),
                           'thumbnail': "https://image.tmdb.org/t/p/w342" + actor.get('profile_path', '') if actor.get('profile_path', '')  else imagepath('no_photo'),
                           'type': Type,
                           'id': actor.get('id', ''),
                           'mediatype': info.getProperty('mediatype')})
        actors_list.append(res)
    return cast_list, actors_list

def imagepath(image):
    if len(image.split('.')) == 1: image += '.png'
    path = filetools.join(config.get_runtime_path(), 'resources', 'skins' , 'Default', 'media', 'Infoplus', image)
    return path

def actors_more_info(ListItem):
    Type = ListItem.getProperty('type')
    actor_id = ListItem.getProperty('id')
    more = tmdb.Tmdb(discover={'url': 'person/' + str(actor_id), 'language': 'en'}).results
    if more['biography']: ListItem.setProperty('bio', more['biography'])

def get_movies(info):
    Type = info.getProperty('mediatype') if info.getProperty('mediatype') == 'movie' else 'tv'
    more = tmdb.Tmdb(discover={'url': 'person/' + str(info.getProperty('id')), 'language': 'it', 'append_to_response': Type + '_credits'}).results
    movies = []
    for movie in more.get(Type + '_credits', {}).get('cast',[]) + more.get(Type + '_credits', {}).get('crew',[]):
        ret = {}
        ret['mediatype'] = info.getProperty('mediatype')
        thumbnail = movie.get('poster_path','')
        ret['thumbnail'] = "https://image.tmdb.org/t/p/w342" + thumbnail if thumbnail else imagepath(Type)
        ret['title'] = movie.get('title','') if Type == 'movie' else movie.get('name','')
        ret['original_title'] = movie.get('original_title','') if Type == 'movie' else movie.get("original_name", '')
        ret['tmdb_id'] = movie.get('id',0)
        if ret not in movies: movies.append(ret)
    itemlist = []
    with futures.ThreadPoolExecutor() as executor:
        List = [executor.submit(add_infoLabels, movie) for movie in movies]
        for res in futures.as_completed(List):
            if res.result():
                itemlist.append(res.result())
        itemlist = sorted(itemlist, key=lambda it: (it.getProperty('year'),it.getProperty('title')))
    return itemlist

def add_infoLabels(movie):
    it = Item(title=movie['title'], infoLabels=movie, contentType=movie['mediatype'])
    tmdb.set_infoLabels_item(it, True)
    movie=it.infoLabels
    item = xbmcgui.ListItem(movie['title'])
    for key, value in movie.items():
        item.setProperty(key, str(value))
    return item


def add(Dict):
    global info_list
    info_list.append(Dict)

def remove():
    global info_list
    info_list = info_list[:-1]

def modal():
    global Info
    global info_list
    if info_list:
        Info = info_list[-1]['info']
        info_list[-1]['class'].doModal()

def getFocus(self):
    global info_list
    for key, value in info_list[-1].items():
        if key not in ['class', 'info', 'id']:
            self.getControl(int(key)).selectItem(value)
    self.setFocusId(info_list[-1]['id'])

def setFocus(self):
    global info_list
    info_list[-1]['id'] = self.getFocusId()
    for key, values in self.ids.items():
        info_list[-1][key] = values