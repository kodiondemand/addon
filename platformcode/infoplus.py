# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# infoplus window with item information
# ------------------------------------------------------------

from typing import List
import xbmc, xbmcgui, sys, requests, re
from core import httptools, support, tmdb, filetools, channeltools, servertools, jsontools
from core.item import Item
from platformcode import config, platformtools, logger, xbmc_videolibrary
from platformcode.logger import log
from core.scrapertools import decodeHtmlentities, htmlclean

from core.support import typo, dbg

PY3 = False
if sys.version_info[0] >= 3: PY3 = True
if PY3: from concurrent import futures
else: from concurrent_py2 import futures

info_list = []
SearchWindows = []
api = 'k_0tdb8a8y'

# Control ID
LIST = 100
CAST = 101
RECOMANDED = 102
TRAILERS = 103
FANARTS = 104


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
    InfoPlus('InfoPlus.xml', config.get_runtime_path(), item=item)

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
        if not self.item.focus: self.item.focus = {}
        platformtools.dialog_busy(True)
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
            platformtools.set_infolabels(self.listitem, self.item)
            
            

            # Add Cast Info
            for cast in self.info.get('castandrole',[]):
                castitem = xbmcgui.ListItem(cast[0], cast[1])
                castitem.setArt({'poster':cast[2]})
                castitem.setProperties({'order':str(cast[3]), 'id':cast[4]})
                self.cast.append(castitem)
            self.cast.sort(key=lambda c: c.getProperty('order'))

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
            self.get_fanarts()

            platformtools.dialog_busy(False)

            self.doModal()

    def onInit(self):
        self.getControl(LIST).addItem(self.listitem)

        self.getControl(CAST).addItems(self.cast)
        if self.item.cast: self.getControl(CAST).selectItem(self.item.cast)

        self.getControl(RECOMANDED).addItems(self.recomanded)
        if self.item.recomanded: self.getControl(RECOMANDED).selectItem(self.item.recomanded)

        self.getControl(TRAILERS).addItems(self.trailers)
        self.getControl(FANARTS).addItems(self.fanarts)

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
        if action in [EXIT]:
            self.close()
        elif action in [BACKSPACE]:
            back(self)
        elif action in [UP, DOWN, LEFT, RIGHT] and focus not in [LIST, CAST, RECOMANDED, TRAILERS, FANARTS, SEARCH, BACK, CLOSE]:
            self.setFocusId(LIST)
        if focus > 0 and focus not in [SEARCH, BACK, CLOSE]:
            self.item.setFocus = focus
            self.item.focus[focus] = self.getControl(focus).getSelectedPosition()


    def onClick(self, control):
        global info_list

        if control in [SEARCH]:
            from specials.globalsearch import new_search
            if self.item.contentType == 'episode':
                self.item.contentType = 'tvshow'
                self.item.text = self.item.contentSerieName
            self.item.mode = 'all'
            self.item.type = self.item.contentType
            new_search(self.item)

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

        elif control in [RECOMANDED]:
            info_list.append(self.item)
            listitem = self.getControl(RECOMANDED).getSelectedItem()
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

    def get_fanarts(self):
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
    CastWindow('CastWindow.xml', config.get_runtime_path(), item=item)
class CastWindow(xbmcgui.WindowXML):
    def __init__(self, *args, **kwargs):
        self.item = kwargs.get('item')
        self.id = self.item.id
        self.item.InfoWindow = 'cast'
        self.host = tmdb.host
        self.api = tmdb.api
        self.movies = []
        self.tvshows = []
        self.movieItems = []
        self.tvshowItems = []
        if not self.item.focus: self.item.focus = {}
        if self.item:
            platformtools.dialog_busy(True)
            self.get_person_info()
            self.get_credits()
            platformtools.dialog_busy(False)
            self.doModal()

    def get_person_info(self):
        # Function for Person Info
        url = '{}/person/{}?api_key={}&language=en'.format(self.host, self.id, self.api)
        translation_url = '{}/person/{}/translations?api_key={}'.format(self.host, self.id, self.api)
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
        self.castitem.setArt({'poster':self.item.poster if self.item.poster else self.item.infoLabels.get('thumbnail', '')})
        self.castitem.setProperties({'birth':birth, 'plot':biography})

    def onInit(self):
        self.getControl(LIST).addItem(self.castitem)
        self.getControl(CAST).addItems(self.movies)
        self.getControl(RECOMANDED).addItems(self.tvshows)

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
        if action in [EXIT]:
            self.close()
        elif action in [BACKSPACE]:
            back(self)
        elif action in [UP, DOWN, LEFT, RIGHT] and focus not in [LIST, CAST, RECOMANDED, TRAILERS, FANARTS, SEARCH, BACK, CLOSE]:
            self.setFocusId(LIST)
        if focus > 0:
            self.item.setFocus = focus
            self.item.focus[focus] = self.getControl(focus).getSelectedPosition()


    def onClick(self, control):
        global info_list

        if control in [CLOSE]:
            self.close()

        elif control in [BACK]:
            back(self)

        elif control in [CAST]:
            info_list.append(self.item)
            self.close()
            start(self.movieItems[self.getControl(CAST).getSelectedPosition()])

        elif control in [RECOMANDED]:
            info_list.append(self.item)
            self.close()
            start(self.tvshowItems[self.getControl(RECOMANDED).getSelectedPosition()])


    def get_credits(self):
        # Function for Credits Info
        url = '{}/person/{}/combined_credits?api_key={}&language=it'.format(self.host, self.id, self.api)
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
            platformtools.set_infolabels(videoitem, item)
            if video.get('media_type') == 'movie':
                self.movies.append(videoitem)
                self.movieItems.append(item)
            else:
                self.tvshows.append(videoitem)
                self.tvshowItems.append(item)


def showImages(images, position):
    xbmc.executebuiltin('Dialog.Close(all)')
    return ImagesWindow('imageWindow.xml', config.get_runtime_path()).start(images=images, position=position)
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