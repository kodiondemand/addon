# -*- coding: utf-8 -*-
import os
import sys
import unittest
import parameterized

from platformcode import config

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
    'guardaSerie TVclick': {
        'da controllare': 0
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


def getChannels():
    channel_list = channelselector.filterchannels("all")
    ret = []
    for chItem in channel_list:
        ch = chItem.channel
        if ch not in chBlackList:
            ret.append({'ch': ch})
    return ret


from specials import news

dictNewsChannels, any_active = news.get_channels_list()

servers_found = []


def getServers():
    ret = []
    for srv in servers_found:
        ret.append({'item': srv})
    return ret


@parameterized.parameterized_class(getChannels())
class GenericChannelTest(unittest.TestCase):
    def __init__(self, *args):
        self.module = __import__('channels.%s' % self.ch, fromlist=["channels.%s" % self.ch])
        super(GenericChannelTest, self).__init__(*args)

    def test_menuitems(self):
        hasChannelConfig = False
        mainlist = self.module.mainlist(Item())
        self.assertTrue(mainlist, 'channel ' + self.ch + ' has no menu')

        for it in mainlist:
            print 'testing ' + self.ch + ' -> ' + it.title
            if it.action == 'channel_config':
                hasChannelConfig = True
                continue
            if it.action == 'search':  # channel-specific
                continue
            itemlist = getattr(self.module, it.action)(it)
            self.assertTrue(itemlist, 'channel ' + self.ch + ' -> ' + it.title + ' is empty')
            if self.ch in chNumRis:  # i know how much results should be
                for content in chNumRis[self.ch]:
                    if content in it.title:
                        risNum = len([i for i in itemlist if not i.nextPage])  # not count nextpage
                        self.assertEqual(chNumRis[self.ch][content], risNum,
                                         'channel ' + self.ch + ' -> ' + it.title + ' returned wrong number of results')
                        break

            for resIt in itemlist:
                self.assertLess(len(resIt.fulltitle), 110,
                                'channel ' + self.ch + ' -> ' + it.title + ' might contain wrong titles\n' + resIt.fulltitle)
                if resIt.url:
                    self.assertIsInstance(resIt.url, str, 'channel ' + self.ch + ' -> ' + it.title + ' -> ' + resIt.title + ' contain non-string url')
                    self.assertIsNotNone(re.match(validUrlRegex, resIt.url),
                                         'channel ' + self.ch + ' -> ' + it.title + ' -> ' + resIt.title + ' might contain wrong url\n' + resIt.url)
                if 'year' in resIt.infoLabels and resIt.infoLabels['year']:
                    msgYear = 'channel ' + self.ch + ' -> ' + it.title + ' might contain wrong infolabels year\n' + str(
                        resIt.infoLabels['year'])
                    self.assert_(type(resIt.infoLabels['year']) is int or resIt.infoLabels['year'].isdigit(), msgYear)
                    self.assert_(int(resIt.infoLabels['year']) > 1900 and int(resIt.infoLabels['year']) < 2100, msgYear)

                if resIt.title == typo(config.get_localized_string(30992), 'color kod bold'):  # next page
                    nextPageItemlist = getattr(self.module, resIt.action)(resIt)
                    self.assertTrue(nextPageItemlist,
                                    'channel ' + self.ch + ' -> ' + it.title + ' has nextpage not working')

            # some sites might have no link inside, but if all results are without servers, there's something wrong
            servers = []
            for resIt in itemlist:
                if hasattr(self.module, resIt.action):
                    servers = getattr(self.module, resIt.action)(resIt)
                else:
                    servers = [resIt]

                if servers:
                    break
            self.assertTrue(servers, 'channel ' + self.ch + ' -> ' + it.title + ' has no servers on all results')
            for server in servers:
                srv = server.server.lower()
                if not srv:
                    continue
                module = __import__('servers.%s' % srv, fromlist=["servers.%s" % srv])
                page_url = server.url
                print 'testing ' + page_url
                self.assert_(hasattr(module, 'test_video_exists'), srv + ' has no test_video_exists')
                if module.test_video_exists(page_url)[0]:
                    urls = module.get_video_url(page_url)
                    server_parameters = servertools.get_server_parameters(srv)
                    self.assertTrue(urls or server_parameters.get("premium"), srv + ' scraper did not return direct urls for ' + page_url)
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
                        self.assertTrue(page.success, srv + ' scraper returned an invalid link')
                        self.assertLess(page.code, 400, srv + ' scraper returned a ' + str(page.code) + ' link')
                        contentType = page.headers['Content-Type']
                        self.assert_(contentType.startswith('video') or 'mpegurl' in contentType or 'octet-stream' in contentType or 'dash+xml' in contentType,
                                     srv + ' scraper did not return valid url for link ' + page_url + '\nDirect url: ' + directUrl + '\nContent-Type: ' + contentType)

        self.assertTrue(hasChannelConfig, 'channel ' + self.ch + ' has no channel config')

    def test_newest(self):
        for cat in dictNewsChannels:
            for ch in dictNewsChannels[cat]:
                if self.ch == ch[0]:
                    itemlist = self.module.newest(cat)
                    self.assertTrue(itemlist, 'channel ' + self.ch + ' returned no news for category ' + cat)
                    break


if __name__ == '__main__':
    unittest.main()
