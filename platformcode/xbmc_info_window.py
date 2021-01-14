# -*- coding: utf-8 -*-

import xbmcgui, sys

from core.tmdb import Tmdb
from platformcode import config, logger
from core import filetools
if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures

BACKGROUND = 30000
LOADING = 30001
SELECT = 30002
CLOSE = 30003
EXIT = 10
BACKSPACE = 92

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
        logger.debug('RESPONSE',self.response)
        return self.response

    def make_items(self, i, result):
        infoLabels = self.scraper().get_infoLabels(origen=result)
        it = xbmcgui.ListItem(infoLabels['title'])
        it.setProperty('fanart', infoLabels.get('fanart', ''))
        it.setProperty('thumbnail', infoLabels.get('thumbnail', imagepath('movie' if infoLabels['mediatype'] == 'movie' else 'tv')))
        it.setProperty('genre', infoLabels.get('genre', 'N/A'))
        it.setProperty('rating', str(infoLabels.get('rating', 'N/A')))
        it.setProperty('plot', str(infoLabels.get('plot', '')))
        it.setProperty('year', str(infoLabels.get('year', '')))
        it.setProperty('position', str(i))
        return it

    def onInit(self):
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)
        results = []
        with futures.ThreadPoolExecutor() as executor:
            for i, result in enumerate(self.results):
                if ('seriesName' in result and result['seriesName']) or ('name' in result and result['name']) or ('title' in result and result['title']):
                    results.append(executor.submit(self.make_items, i, result))
            for res in futures.as_completed(results):
                self.items.append(res.result())
        self.items.sort(key=lambda it: int(it.getProperty('position')))

        self.getControl(SELECT).addItems(self.items)
        self.getControl(BACKGROUND).setImage(self.items[0].getProperty('fanart'))
        self.getControl(LOADING).setVisible(False)
        self.setFocusId(SELECT)

    def onClick(self, control_id):
        if control_id == SELECT:
            self.response = self.results[int(self.getControl(SELECT).getSelectedItem().getProperty('position'))]
            self.close()
        elif control_id == CLOSE:
            self.close()

    def onAction(self, action):
        if self.getFocusId() in [SELECT]:
            fanart = self.getControl(self.getFocusId()).getSelectedItem().getProperty('fanart')
            self.getControl(BACKGROUND).setImage(fanart)
        if action in [BACKSPACE]:
            self.close()
        elif action in [EXIT]:
            self.close()

