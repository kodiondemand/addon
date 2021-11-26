# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# infoplus window with item information
# ------------------------------------------------------------

import xbmc, xbmcgui, sys
from core import httptools,  tmdb
from core.item import Item
from platformcode import config, platformtools, logger

from core.support import match, typo


info_list = []
SearchWindows = []

# Control ID
LIST = 100
CAST = MOVIE = 101
SET = SHOW = 102
RECOMANDED = 103
TRAILERS = 104
FANARTS = 105



SEARCH = 200
BACK = 201
CLOSE = 202

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92


def start(item):
    xbmc.executebuiltin('Dialog.Close(all)')
    InfoPlus('InfoPlus.xml', config.getRuntimePath(), item=item)

class InfoPlus(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.item = kwargs.get('item')
        self.info = self.item.infoLabels
        self.type = 'movie' if self.info.get('mediatype') == 'movie' else 'tv'
        self.items = []
        self.cast = []
        self.actors = []
        self.ids = {}
        self.tmdb = []
        self.recomanded = []
        self.trailers = []
        self.images = []
        self.fanarts = []
        self.collection = []
        if not self.item.focus: self.item.focus = {}
        platformtools.dialogBusy(True)
        if self.item:
            # Find Video Info

            tmdb.set_infoLabels_item(self.item)
            self.info = self.item.infoLabels
            title = typo(self.info.get('title'), 'bold')
            tagline = self.info.get('tagline')
            if tagline: title += '\n' + typo(tagline, 'italic')

            # Set Listitem
            self.listitem = xbmcgui.ListItem(title)
            # Set Image
            if self.info['mediatype'] == 'episode':
                self.listitem.setArt({'poster':self.info['thumbnail'], 'fanart':self.info['poster_path']})
            else:
                self.listitem.setArt({'poster':self.item.thumbnail, 'fanart':self.item.fanart})
            # Set Rating
            if 'trakt_rating' in self.info: self.info['rating'] = self.info['trakt_rating']
            self.listitem.setProperty('rating',str(int(self.info.get('rating',10) * 10)))
            rating = self.info.get('rating', 'N/A')
            color = 'FFFFFFFF' if rating == 'N/A' else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'
            self.listitem.setProperty('color',color)

            info = ''
            if self.info.get('year'): info = str(self.info.get('year'))
            if self.info.get('duration'): info = '{}[B]•[/B]{}'.format(info, self.info.get('duration'))
            if self.info.get('Mpaa'): info = '{}[B]•[/B]{}'.format(info, self.info.get('Mpaa'))
            self.listitem.setProperty('info',info)

            # Set infoLabels
            platformtools.setInfolabels(self.listitem, self.item)

            # Add Cast Info
            for cast in self.info.get('castandrole',[]):
                castitem = xbmcgui.ListItem(cast[0], cast[1])
                castitem.setArt({'poster':cast[2]})
                castitem.setProperties({'order':str(cast[3]), 'id':cast[4]})
                self.cast.append(castitem)
            self.cast.sort(key=lambda c: c.getProperty('order'))

            if self.info.get('setid'):
                url = '{}/collection/{}?api_key={}&language={}'.format(tmdb.host, self.info.get('setid'), tmdb.api, tmdb.def_lang)
                parts = match(url).response.json['parts']
                for part in parts:
                    poster = 'https://image.tmdb.org/t/p/original/' + part.get('poster_path') if part.get('poster_path') else ''
                    setitem = xbmcgui.ListItem(part.get('title'), self.info.get('set'))
                    setitem.setArt({'poster': poster})
                    rating = part.get('vote_average', 'N/A')
                    color = 'FFFFFFFF' if rating == 'N/A' else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'

                    setitem.setProperties({'id':part.get('id'), 'mediatype':'movie', 'color':color})
                    setitem.setInfo("video", {'plot':self.info.get('setoverview'), 'rating':rating})
                    self.collection.append(setitem)


            directors = self.info.get('director')
            if directors:
                for i,  director in enumerate(directors.split(',')):
                    directoritem = xbmcgui.ListItem(director, 'Regista')
                    directoritem.setArt({'poster':self.info.get('director_image')[i]})
                    directoritem .setProperty('id', str(self.info.get('director_id')[i]))
                    self.cast.insert(i, directoritem)

            # Add Recomandations
            self.get_recomendations()

            # Add Trailers
            self.get_trailers()

            # Add Fanart
            self.getFanarts()

            platformtools.dialogBusy(False)

            self.doModal()

    def onInit(self):
        self.getControl(LIST).addItem(self.listitem)

        self.getControl(CAST).addItems(self.cast)
        if self.item.cast: self.getControl(CAST).selectItem(self.item.cast)

        self.getControl(RECOMANDED).addItems(self.recomanded)
        if self.item.recomanded: self.getControl(RECOMANDED).selectItem(self.item.recomanded)

        self.getControl(TRAILERS).addItems(self.trailers)
        self.getControl(FANARTS).addItems(self.fanarts)

        if self.collection:
            self.getControl(SET).addItems(self.collection)

        # Set Focus
        if self.item.focus:
            for k, v in self.item.focus.items():
                self.getControl(k).selectItem(v)
            xbmc.sleep(200)
            self.setFocusId(self.item.setFocus)
        else: self.setFocusId(LIST)


    def onAction(self, action):
        action = action.getId()
        focus = self.getFocusId()
        infoList = [LIST, CAST, SET, RECOMANDED, TRAILERS, FANARTS]
        actionList = [SEARCH, BACK, CLOSE]
        if action in [EXIT]:
            self.close()
        elif action in [BACKSPACE]:
            back(self)
        elif action in [UP, DOWN]:
            A = 1 if action == DOWN else -1
            if focus not in infoList or focus in actionList:
                self.setFocusId(infoList[0])
            elif focus + A in infoList and not focus in actionList:
                while focus in infoList:
                    focus += A
                    if self.getControl(focus).isVisible():
                        self.setFocusId(focus)
                        break
            else:
                self.setFocusId(SEARCH)

        if focus > 0 and focus not in actionList:
            self.item.setFocus = focus
            self.item.focus[focus] = self.getControl(focus).getSelectedPosition()


    def onClick(self, control):
        global info_list

        if control in [SEARCH]:
            selection = 0
            original = self.item.infoLabels.get('originaltitle')

            if self.item.contentType == 'episode':
                self.item.contentType = 'tvshow'
                self.item.text = self.item.contentSerieName
            else:
                self.item.text = self.item.contentTitle
            titles = [self.item.text] + [original] if original else []
            if original and original != self.item.text:
                selection = platformtools.dialogSelect(config.getLocalizedString(90010), titles)
            if selection > -1:
                self.item.text = titles[selection]
                self.item.mode = 'search/' + self.item.contentType
                item = self.item.clone(channel='globalsearch', action='new_search')
                xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?" + item.tourl() + ")")
                # new_search(self.item.clone())

        elif control in [CLOSE]:
            self.close()

        elif control in [BACK]:
            back(self)

        elif control in [CAST]:
            info_list.append(self.item)
            listitem = self.getControl(CAST).getSelectedItem()
            it = Item(id=listitem.getProperty('id'), poster=listitem.getArt('poster'))
            self.close()
            showCast(it)

        elif control in [RECOMANDED, SET]:
            info_list.append(self.item)
            listitem = self.getControl(control).getSelectedItem()
            it = Item(title=listitem.getLabel(), infoLabels={'tmdb_id':listitem.getProperty('id'), 'mediatype':listitem.getProperty('mediatype')})
            self.close()
            start(it)

        elif control in [TRAILERS]:
            listitem = self.getControl(TRAILERS).getSelectedItem()
            xbmc.executebuiltin('RunPlugin({})'.format(listitem.getPath()))

        elif control in [FANARTS]:
            position = showImages(self.images, self.getControl(FANARTS).getSelectedPosition())
            self.getControl(FANARTS).selectItem(position)


    def get_recomendations(self):
        # Function for recomanded
        search = {'url': '{}/{}/recommendations'.format(self.type, self.info.get('tmdb_id')), 'language': 'it', 'page': 1}
        tmdb_res = tmdb.Tmdb(discover=search, search_type=self.type, language_search='it').results
        search = {'url': '{}/{}/recommendations'.format(self.type, self.info.get('tmdb_id')), 'language': 'it', 'page': 2}
        tmdb_res += tmdb.Tmdb(discover=search, search_type=self.type, language_search='it').results[1:]
        for result in tmdb_res:
            title = result.get("title", result.get("name", ''))
            original_title = result.get("original_title", result.get("original_name", ''))
            thumbnail ='https://image.tmdb.org/t/p/w342' + result.get("poster_path", "") if result.get("poster_path", "") else ''
            recomandationsitem = xbmcgui.ListItem(title, original_title)
            recomandationsitem.setArt({'poster':thumbnail})
            recomandationsitem.setInfo("video",{'plot':result.get('overview', ''), 'rating':result.get('vote_average', 0)})
            rating = result.get('vote_average', 'N/A')
            color = 'FFFFFFFF' if rating == 'N/A' else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'
            recomandationsitem.setProperties({'id': result.get('id', 0), 'mediatype': self.info.get('mediatype'), 'rating':str(int(result.get('vote_average',10) * 10)), 'color':color})

            self.recomanded.append(recomandationsitem)

    def get_trailers(self):
        trailers = tmdb.Tmdb(id_Tmdb=self.info.get('tmdb_id'), search_type=self.type).get_videos()
        if trailers:
            for trailer in trailers:
                traileitem = xbmcgui.ListItem(trailer['name'], path=trailer['url'])
                traileitem.setArt({'thumb':'http://img.youtube.com/vi/' + trailer['url'].split('=')[-1] + '/0.jpg'})
                self.trailers.append(traileitem)

    def getFanarts(self):
        _id = self.info.get('tmdb_id')
        res = {}
        fanarts = self.info.get('fanarts',[])
        if _id:
            _type = self.item.contentType.replace('show','').replace('movie','movies')
            host = 'http://webservice.fanart.tv/v3/{}/{}?api_key=cab16e262d72fea6a6843d679aa10300'
            res = httptools.downloadpage(host.format(_type, _id)).json

        if res: fanarts += [k.get('url') for k in res.get('moviebackground', [])] if _type == 'movies' else [k.get('url') for k in res.get('showbackground', [])]

        if fanarts:
            for i, fanart in enumerate(fanarts):
                fanartitem = xbmcgui.ListItem(str(i))
                fanartitem.setArt({'fanart':fanart})
                self.images.append(fanart)
                self.fanarts.append(fanartitem)


def showCast(item):
    xbmc.executebuiltin('Dialog.Close(all)')
    CastWindow('CastWindow.xml', config.getRuntimePath(), item=item)
class CastWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.item = kwargs.get('item')
        self.id = self.item.id
        self.item.InfoWindow = 'cast'
        self.movies = []
        self.tvshows = []
        self.movieItems = []
        self.tvshowItems = []
        if not self.item.focus: self.item.focus = {}
        if self.item:
            platformtools.dialogBusy(True)
            self.get_person_info()
            self.get_credits()
            platformtools.dialogBusy(False)
            self.doModal()

    def get_person_info(self):
        # Function for Person Info
        if not self.id and self.item.text:
            res = httptools.downloadpage('{}/search/person?api_key={}&language={}&query={}'.format(tmdb.host, tmdb.api, tmdb.def_lang, self.item.text)).json.get('results',[])
            if res: self.id = res[0]['id']
            else: self.close()

        url = '{}/person/{}?api_key={}&language={}'.format(tmdb.host, self.id, tmdb.api, tmdb.def_lang)
        translation_url = '{}/person/{}/translations?api_key={}'.format(tmdb.host, self.id, tmdb.api)
        info = httptools.downloadpage(url).json


        biography = info.get('biography', '')
        if not biography:
            translation = httptools.downloadpage(translation_url).json
            if translation:
                for t in translation['translations']:
                    if t['iso_639_1'] == 'en':
                        biography = t['data']['biography']
                        break

        born = info.get('birthday').split('-')[0] if info.get('birthday') else ''
        dead = info.get('deathday').split('-')[0] if info.get('deathday') else ''
        place = info.get('place_of_birth')
        self.castitem = xbmcgui.ListItem(info.get('name'))
        birth = born + (' - ' + dead if dead else '') + ('   [B]•[/B]   ' + place if place else '')
        self.castitem.setArt({'poster':self.item.poster if self.item.poster else self.item.infoLabels.get('thumbnail', self.item.thumbnail)})
        self.castitem.setProperties({'birth':birth, 'plot':biography})

    def onInit(self):
        self.getControl(LIST).addItem(self.castitem)
        self.getControl(MOVIE).addItems(self.movies)
        self.getControl(SHOW).addItems(self.tvshows)

        # Set Focus
        xbmc.sleep(200)
        if self.item.focus:
            for k, v in self.item.focus.items():
                self.getControl(k).selectItem(v)
            self.setFocusId(self.item.setFocus)
        else: self.setFocusId(LIST)

    def onAction(self, action):
        action = action.getId()
        focus = self.getFocusId()
        infoList = [LIST, MOVIE, SHOW]
        actionList = [BACK, CLOSE]
        if action in [EXIT]:
            self.close()
        elif action in [BACKSPACE]:
            back(self)
        elif action in [UP, DOWN] and focus in infoList + actionList:
            A = 1 if action == DOWN else -1
            if focus not in infoList or focus in actionList:
                self.setFocusId(infoList[0])
            elif focus + A in infoList and not focus in actionList:
                while focus in infoList:
                    focus += A
                    if self.getControl(focus).isVisible():
                        self.setFocusId(focus)
                        break
            else:
                self.setFocusId(BACK)

        if focus > 0 and focus not in actionList:
            self.item.setFocus = focus
            self.item.focus[focus] = self.getControl(focus).getSelectedPosition()

    def onClick(self, control):
        global info_list

        if control in [CLOSE]:
            self.close()

        elif control in [BACK]:
            back(self)

        elif control in [MOVIE]:
            info_list.append(self.item)
            self.close()
            start(self.movieItems[self.getControl(MOVIE).getSelectedPosition()])

        elif control in [SHOW]:
            info_list.append(self.item)
            self.close()
            start(self.tvshowItems[self.getControl(SHOW).getSelectedPosition()])


    def get_credits(self):
        # Function for Credits Info
        url = '{}/person/{}/combined_credits?api_key={}&language='.format(tmdb.host, self.id, tmdb.api, tmdb.def_lang)
        info = httptools.downloadpage(url).json

        for video in info.get('cast',[]) + info.get('crew',[]):
            year = video.get('release_date', video.get('first_air_date'))
            poster = 'https://image.tmdb.org/t/p/original/' + video.get('poster_path') if video.get('poster_path') else ''
            infoLabels = {
                'rating':video.get('vote_average', 0),
                'plot':video.get('overview',''),
                'mediatype':video.get('media_type','').replace('tv','tvshow'),
                'thumbnail': poster,
                'tmdb_id':video.get('id'),
                'title':video.get('title',video.get('name','')),
                'year':year.split('-')[0] if year else ''
            }
            item = Item(infoLabels=infoLabels)
            videoitem = xbmcgui.ListItem(video.get('title',video.get('name','')), video.get('character', video.get('job')))
            videoitem.setArt({'poster':infoLabels['thumbnail']})
            rating = video.get('vote_average', 'N/A')
            color = 'FFFFFFFF' if rating == 'N/A' else 'FFDB2360' if rating < 4 else 'FFD2D531' if rating < 7 else 'FF21D07A'
            videoitem.setProperties({'rating':str(int(video.get('vote_average',10) * 10)), 'color':color})
            platformtools.setInfolabels(videoitem, item)
            if video.get('media_type') == 'movie':
                self.movies.append(videoitem)
                self.movieItems.append(item)
            else:
                self.tvshows.append(videoitem)
                self.tvshowItems.append(item)


def showImages(images, position):
    xbmc.executebuiltin('Dialog.Close(all)')
    return ImagesWindow('imageWindow.xml', config.getRuntimePath()).start(images=images, position=position)
class ImagesWindow(xbmcgui.WindowXMLDialog):
    def start(self, *args, **kwargs):
        self.images = []
        self.position = kwargs.get('position')
        for i, image in enumerate(kwargs.get('images', [])):
            listitem = xbmcgui.ListItem(str(i+1), str(len(kwargs.get('images', []))))
            listitem.setArt({'fanart':image})
            self.images.append(listitem)
        self.doModal()
        return self.position

    def onInit(self):
        self.getControl(LIST).addItems(self.images)
        self.setFocusId(LIST)
        self.getControl(LIST).selectItem(self.position)

    def onAction(self, action):
        action = action.getId()
        self.position = self.getControl(LIST).getSelectedPosition()
        if action in [BACKSPACE, EXIT]:
            self.close()



def back(self):
    global info_list
    if info_list:
        self.close()
        it = info_list[-1]
        info_list = info_list[:-1]
        if it.InfoWindow == 'cast':
            showCast(it)
        else:
            start(it)
    else:
        self.close()