# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per La7
# ------------------------------------------------------------

import requests
from core import support
from platformcode import logger

DRM = 'com.widevine.alpha'
key_widevine = "https://la7.prod.conax.cloud/widevine/license"
host = 'https://www.la7.it'
headers = {
    'host_token': 'pat.la7.it',
    'host_license': 'la7.prod.conax.cloud',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'accept': '*/*',
    'accept-language': 'en,en-US;q=0.9,it;q=0.8',
    'dnt': '1',
    'te': 'trailers',
    'origin': 'https://www.la7.it',
    'referer': 'https://www.la7.it/',
}

@support.menu
def mainlist(item):
    top =  [('Dirette {bullet bold}', ['', 'live']),
            ('Replay {bullet bold}', ['', 'replay_channels'])]

    menu = [('Programmi TV {bullet bold}', ['/tutti-i-programmi', 'movies', '', 'tvshow']),
            ('Teche La7 {bullet bold}', ['/i-protagonisti', 'movies', '', 'tvshow'])]

    search = ''
    return locals()


def live(item):
    itemlist = [item.clone(title='La7', fulltitle='La7', url= host + '/dirette-tv', action='findvideos', forcethumb = True),
                item.clone(title='La7d', fulltitle='La7d', url= host + '/live-la7d', action='findvideos', forcethumb = True)]
    return support.thumb(itemlist, mode='live')


def replay_channels(item):
    itemlist = [item.clone(title='La7', fulltitle='La7', url= host + '/rivedila7/0/la7', action='replay_menu', forcethumb = True),
                item.clone(title='La7d', fulltitle='La7d', url= host + '/rivedila7/0/la7d', action='replay_menu', forcethumb = True)]
    return support.thumb(itemlist, mode='live')


@support.scrape
def replay_menu(item):
    action = 'replay'
    patron = r'href="(?P<url>[^"]+)"><div class="giorno-text">\s*(?P<day>[^>]+)</div><[^>]+>\s*(?P<num>[^<]+)</div><[^>]+>\s*(?P<month>[^<]+)<'
    def itemHook(item):
        item.title = '{} {} {}'.format(item.day, item.num, item.month)
        return item
    return locals()


@support.scrape
def replay(item):
    action = 'findvideos'
    patron = r'guida-tv"><[^>]+><[^>]+>(?P<hour>[^<]+)<[^>]+><[^>]+><[^>]+>\s*<a href="(?P<url>[^"]+)"><[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]+)"><[^>]+><[^>]+><[^>]+><[^>]+>\s*(?P<name>[^<]+)<[^>]+><[^>]+><[^>]+>(?P<plot>[^<]+)<'
    def itemHook(item):
        item.title = '{} - {}'.format(item.hour, item.name)
        item.contentTitle = item.fulltitle = item.show = item.name
        item.thumbnail = 'http:' + item.t
        item.fanart = item.thumbnail
        item.forcethumb = True
        return item
    return locals()

def search(item, text):
    logger.debug(text)
    item.url = host + '/tutti-i-programmi'
    item.search = text
    try:
        return movies(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error('search log:', line)
        return []


@support.scrape
def movies(item):
    search = item.search
    disableAll = True
    action = 'episodes'
    patron = r'<a href="(?P<url>[^"]+)"[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]+)"></div><div class="titolo">\s*(?P<title>[^<]+)<'
    def itemHook(item):
        prepose = ''
        if item.t.startswith('//'):
            prepose = 'http:'
        elif item.t.startswith('/'):
            prepose = host
        elif not item.t.startswith('http'):
            prepose = host + '/'
        item.thumbnail = prepose + item.t
        item.fanart = item.thumb
        return item
    return locals()


@support.scrape
def episodes(item):
    data = support.match(item).data
    action = 'findvideos'
    if '>puntate<' in data:
        patronBlock = r'>puntate<(?P<block>.*?)home-block-outbrain'
        url = support.match(data, patron=r'>puntate<[^>]+>[^>]+>[^>]+><a href="([^"]+)"').match
        data += support.match(host + url).data
    else:
        item.url += '/video'
        data = support.match(item).data

    patron = r'(?:<a href="(?P<url>[^"]+)">[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]*)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?(?:[^>]+>){6}?)\s*(?P<title>[^<]+)<(?:[^>]+>[^>]+>[^>]+><div class="data">(?P<date>[^<]+))?|class="heading">[^>]+>(?P<Title>[^<]+).*?window.shareUrl = "(?P<Url>[^"]+)".*?poster:\s*"(?P<Thumb>[^"]+)", title: "(?P<desc>[^"]+)"'
    patronNext = r'<a href="([^"]+)">›'
    videlibraryEnabled = False
    downloadEnabled = False

    def itemHook(item):
        if item.Thumb: item.t = item.Thumb
        item.thumbnail = 'http:' + item.t if item.t.startswith('//') else item.t if item.t else item.thumbnail
        if item.Title: item.title = item.Title
        if item.date:
            item.title = support.re.sub(r'[Pp]untata (?:del )?\d+/\d+/\d+', '', item.title)
            item.title = '{} [{}]'.format(item.title, item.date)
        if item.desc: item.plot = item.desc
        item.forcethumb = True
        item.fanart = item.thumbnail
        return item
    return locals()


def findvideos(item):
    logger.debug()
    return support.server(item, itemlist=[item.clone(server='directo', action='play')])

def play(item):
    logger.debug()
    data = support.match(item).data
    url = support.match(data, patron=r'''["]?dash["]?\s*:\s*["']([^"']+)["']''').match
    if url:
        preurl = support.match(data, patron=r'preTokenUrl = "(.+?)"').match
        tokenHeader = {
            'host': headers['host_token'],
            'user-agent': headers['user-agent'],
            'accept': headers['accept'],
            'accept-language': headers['accept-language'],
            'dnt': headers['dnt'],
            'te': headers['te'],
            'origin': headers['origin'],
            'referer': headers['referer'],
        }
        preAuthToken = requests.get(preurl, headers=tokenHeader,verify=False).json()['preAuthToken']
        licenseHeader = {
            'host': headers['host_license'],
            'user-agent': headers['user-agent'],
            'accept': headers['accept'],
            'accept-language': headers['accept-language'],
            'preAuthorization': preAuthToken,
            'origin': headers['origin'],
            'referer': headers['referer'],
        }
        preLic= '&'.join(['%s=%s' % (name, value) for (name, value) in licenseHeader.items()])
        tsatmp=str(int(support.time()))
        license_url= key_widevine + '?d=%s'%tsatmp
        lic_url='%s|%s|R{SSM}|'%(license_url, preLic)
        item.drm = DRM
        item.license = lic_url
    else:
        match = support.match(data, patron='/content/entry/data/(.*?).mp4').match
        if match:
            url = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/entry/data/' + support.match(item, patron='/content/entry/data/(.*?).mp4').match + '.mp4.urlset/master.m3u8'
            item = item.clone(url=url, server='directo', action='play')
    return support.servertools.find_video_items(item, data=url)
