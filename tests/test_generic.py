# -*- coding: utf-8 -*-
# use export PYTHONPATH=addon source code
# and inside .kodi to run tests locally
# you can pass specific channel name using KOD_TST_CH environment var

# export PYTHONPATH=/home/user/.kodi/addons/plugin.video.kod
# export KOD_TST_CH=channel
# python tests/test_generic.py

import os
import sys
import unittest

import xbmc

if 'KOD_TST_CH' not in os.environ:
    # custom paths
    def add_on_info(*args, **kwargs):
        return xbmc.AddonData(
            kodi_home_path=os.path.join(os.getcwd(), 'tests', 'home'),
            add_on_id='plugin.video.kod',
            add_on_path=os.getcwd(),
            kodi_profile_path=os.path.join(os.getcwd(), 'tests', 'home', 'userdata')
        )


    # override
    xbmc.get_add_on_info_from_calling_script = add_on_info


import HtmlTestRunner
import parameterized

from platformcode import config, logger

config.set_setting('tmdb_active', False)

librerias = os.path.join(config.get_runtime_path(), 'lib')
sys.path.insert(0, librerias)
from core.support import typo
from core.item import Item
from core.httptools import downloadpage
from core import servertools
import channelselector
import re

validUrlRegex = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

chBlackList = ['url']
chNumRis = {
    'altadefinizione01': {
        'Film': 20
    },
    'altadefinizione01_link': {
        'Film': 16,
        'Serie TV': 16,
    },
    'altadefinizioneclick': {
        'Film': 36,
        'Serie TV': 12,
    },
    'casacinema': {
        'Film': 10,
        'Serie TV': 10,
    },
    'cineblog01': {
        'Film': 12,
        'Serie TV': 13
    },
    'cinemalibero': {
        'Film': 20,
        'Serie TV': 20,
    },
    'cinetecadibologna': {
        'Film': 10
    },
    'eurostreaming': {
        'Serie TV': 18
    },
    'Filmpertutti': {
        'Film': 24,
        'Serie TV': 24,
    },
    'hd4me': {
        'Film': 10
    },
    'ilgeniodellostreaming': {
        'Film': 30,
        'Serie TV': 30
    },
    'italiaserie': {
        'Serie TV': 20
    },
    'casacinemaInfo': {
        'Film': 150
    },
    'netfreex': {
        'Film': 30,
        'Serie TV': 30
    },
    'piratestreaming': {
        'Film': 24,
        'Serie TV': 24
    },
    'polpotv': {
        'Film': 12,
        'Serie TV': 12
    },
    'streamingaltadefinizione': {
        'Film': 30,
        'Serie TV': 30
    },
    'seriehd': {
        'Serie TV': 12
    },
    'serietvonline': {
        'Film': 35,
        'Serie TV': 35
    },
    'tantifilm': {
        'Film': 20,
        'Serie TV': 20
    },
}

servers = []
channels = []

channel_list = channelselector.filterchannels("all") if 'KOD_TST_CH' not in os.environ else [Item(channel=os.environ['KOD_TST_CH'], action="mainlist")]
ret = []
for chItem in channel_list:
    try:
        ch = chItem.channel
        if ch not in chBlackList:
            module = __import__('channels.%s' % ch, fromlist=["channels.%s" % ch])
            hasChannelConfig = False
            mainlist = module.mainlist(Item())
            menuItemlist = {}
            serversFound = {}

            for it in mainlist:
                print 'preparing ' + ch + ' -> ' + it.title

                if it.action == 'channel_config':
                    hasChannelConfig = True
                    continue
                if it.action == 'search':  # channel-specific
                    continue
                itemlist = getattr(module, it.action)(it)
                menuItemlist[it.title] = itemlist

                # some sites might have no link inside, but if all results are without servers, there's something wrong
                for resIt in itemlist:
                    if resIt.action == 'findvideos':
                        if hasattr(module, resIt.action):
                            serversFound[it.title] = getattr(module, resIt.action)(resIt)
                        else:
                            serversFound[it.title] = [resIt]

                        if serversFound[it.title]:
                            servers.extend(
                                {'name': srv.server.lower(), 'server': srv} for srv in serversFound[it.title] if srv.server)
                            break

            channels.append(
                {'ch': ch, 'hasChannelConfig': hasChannelConfig, 'mainlist': mainlist, 'menuItemlist': menuItemlist,
                 'serversFound': serversFound, 'module': module})
    except:
        import traceback
        logger.error(traceback.format_exc())

from specials import news
dictNewsChannels, any_active = news.get_channels_list()
print channels
# only 1 server item for single server
serverNames = []
serversFinal = []
for s in servers:
    if not s['name'] in serverNames:
        serverNames.append(s['name'])
        serversFinal.append(s)


@parameterized.parameterized_class(channels)
class GenericChannelTest(unittest.TestCase):
    def test_mainlist(self):
        self.assertTrue(self.mainlist, 'channel ' + self.ch + ' has no mainlist')
        self.assertTrue(self.hasChannelConfig, 'channel ' + self.ch + ' has no channel config')

    def test_newest(self):
        for cat in dictNewsChannels:
            for ch in dictNewsChannels[cat]:
                if self.ch == ch[0]:
                    itemlist = self.module.newest(cat)
                    self.assertTrue(itemlist, 'channel ' + self.ch + ' returned no news for category ' + cat)
                    break


@parameterized.parameterized_class(
    [{'ch': ch['ch'], 'title': title, 'itemlist': itemlist, 'serversFound': ch['serversFound'][title] if title in ch['serversFound'] else True, 'module': ch['module']} for ch in channels for
     title, itemlist in ch['menuItemlist'].items()])
class GenericChannelMenuItemTest(unittest.TestCase):
    def test_menu(self):
        print 'testing ' + self.ch + ' --> ' + self.title
        self.assertTrue(self.module.host, 'channel ' + self.ch + ' has not a valid hostname')
        self.assertTrue(self.itemlist, 'channel ' + self.ch + ' -> ' + self.title + ' is empty')
        self.assertTrue(self.serversFound,
                        'channel ' + self.ch + ' -> ' + self.title + ' has no servers on all results')

        if self.ch in chNumRis:  # i know how much results should be
            for content in chNumRis[self.ch]:
                if content in self.title:
                    risNum = len([i for i in self.itemlist if not i.nextPage])  # not count nextpage
                    self.assertEqual(chNumRis[self.ch][content], risNum,
                                     'channel ' + self.ch + ' -> ' + self.title + ' returned wrong number of results<br>'
                                     + str(risNum) + ' but should be ' + str(chNumRis[self.ch][content]) + '<br>' +
                                     '<br>'.join([i.title for i in self.itemlist if not i.nextPage]))
                    break

        for resIt in self.itemlist:
            print resIt.title + ' -> ' + resIt.url
            self.assertLess(len(resIt.fulltitle), 110,
                            'channel ' + self.ch + ' -> ' + self.title + ' might contain wrong titles<br>' + resIt.fulltitle)
            if resIt.url:
                self.assertIsInstance(resIt.url, str,
                                      'channel ' + self.ch + ' -> ' + self.title + ' -> ' + resIt.title + ' contain non-string url')
                self.assertIsNotNone(re.match(validUrlRegex, resIt.url),
                                     'channel ' + self.ch + ' -> ' + self.title + ' -> ' + resIt.title + ' might contain wrong url<br>' + resIt.url)
            if 'year' in resIt.infoLabels and resIt.infoLabels['year']:
                msgYear = 'channel ' + self.ch + ' -> ' + self.title + ' might contain wrong infolabels year<br>' + str(
                    resIt.infoLabels['year'])
                self.assert_(type(resIt.infoLabels['year']) is int or resIt.infoLabels['year'].isdigit(),
                             msgYear)
                self.assert_(int(resIt.infoLabels['year']) > 1900 and int(resIt.infoLabels['year']) < 2100,
                             msgYear)

            if resIt.title == typo(config.get_localized_string(30992), 'color kod bold'):  # next page
                nextPageItemlist = getattr(self.module, resIt.action)(resIt)
                self.assertTrue(nextPageItemlist,
                                'channel ' + self.ch + ' -> ' + self.title + ' has nextpage not working')

        print '<br>test passed'


@parameterized.parameterized_class(serversFinal)
class GenericServerTest(unittest.TestCase):
    def test_get_video_url(self):
        module = __import__('servers.%s' % self.name, fromlist=["servers.%s" % self.name])
        page_url = self.server.url
        print 'testing ' + page_url
        self.assert_(hasattr(module, 'test_video_exists'), self.name + ' has no test_video_exists')
        try:
            if module.test_video_exists(page_url)[0]:
                urls = module.get_video_url(page_url)
                server_parameters = servertools.get_server_parameters(self.name)
                self.assertTrue(urls or server_parameters.get("premium"),
                                self.name + ' scraper did not return direct urls for ' + page_url)
                print urls
                for u in urls:
                    spl = u[1].split('|')
                    if len(spl) == 2:
                        directUrl, headersUrl = spl
                    else:
                        directUrl, headersUrl = spl[0], ''
                    headers = {}
                    if headersUrl:
                        for name in headersUrl.split('&'):
                            h, v = name.split('=')
                            h = str(h)
                            headers[h] = str(v)
                        print headers
                    if 'magnet:?' in directUrl:  # check of magnet links not supported
                        continue
                    page = downloadpage(directUrl, headers=headers, only_headers=True, use_requests=True)
                    self.assertTrue(page.success, self.name + ' scraper returned an invalid link')
                    self.assertLess(page.code, 400, self.name + ' scraper returned a ' + str(page.code) + ' link')
                    contentType = page.headers['Content-Type']
                    self.assert_(contentType.startswith(
                        'video') or 'mpegurl' in contentType or 'octet-stream' in contentType or 'dash+xml' in contentType,
                                 self.name + ' scraper did not return valid url for link ' + page_url + '<br>Direct url: ' + directUrl + '<br>Content-Type: ' + contentType)
        except:
            import traceback
            logger.error(traceback.format_exc())


if __name__ == '__main__':
    if 'KOD_TST_CH' not in os.environ:
        unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(report_name='report', add_timestamp=False, combine_reports=True,
                                                           report_title='KoD Test Suite'), exit=False)
    else:
        unittest.main()
