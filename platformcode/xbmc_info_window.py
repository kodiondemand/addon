# -*- coding: utf-8 -*-

import xbmcgui

from core.tmdb import Tmdb
from platformcode import config, logger
from core import filetools

BACKGROUND = 30000
LOADING = 30001
SELECT = 30002

def imagepath(image):
    if len(image.split('.')) == 1: image += '.png'
    path = filetools.join(config.get_runtime_path(), 'resources', 'skins' , 'Default', 'media', 'Infoplus', image)
    return path

class InfoWindow(xbmcgui.WindowXMLDialog):

    def start(self, results, caption="", item=None, scraper=Tmdb):
        self.items = []
        self.response = None
        self.results = results
        self.item = item
        self.scraper = scraper

        self.doModal()
        logger.info('RESPONSE',self.response)
        return self.response

    def onInit(self):
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)

        for result in self.results:
            infoLabels = self.scraper().get_infoLabels(origen=result)
            it = xbmcgui.ListItem(infoLabels['title'])
            it.setProperty('fanart', infoLabels.get('fanart', ''))
            it.setProperty('thumbnail', infoLabels.get('thumbnail', imagepath('movie' if infoLabels['mediatype'] == 'movie' else 'tv')))
            it.setProperty('genre', infoLabels.get('genre', 'N/A'))
            it.setProperty('rating', str(infoLabels.get('rating', 'N/A')))
            it.setProperty('plot', str(infoLabels.get('plot', '')))
            it.setProperty('year', str(infoLabels.get('year', '')))
            self.items.append(it)

        self.getControl(SELECT).addItems(self.items)
        self.getControl(BACKGROUND).setImage(self.items[0].getProperty('fanart'))
        self.getControl(LOADING).setVisible(False)
        self.setFocusId(SELECT)

    def onClick(self, control_id):
        if control_id == SELECT:
            self.response = self.results[self.getControl(SELECT).getSelectedPosition()]
        self.close()

