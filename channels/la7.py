# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per La7
# ------------------------------------------------------------

import requests
from core import support

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
    top =  [('Dirette {bold}', ['', 'live']),
            ('Replay {bold}', ['', 'replay_channels'])]

    menu = [('Programmi TV {bullet bold}', ['/tutti-i-programmi', 'peliculas', '', 'tvshow']),
            ('Teche La7 {bullet bold}', ['/i-protagonisti', 'peliculas', '', 'tvshow'])]

    search = ''
    return locals()


def live(item):
    itemlist = [item.clone(title=support.typo('La7', 'bold'), fulltitle='La7', url= host + '/dirette-tv', action='play', forcethumb = True, no_return=True),
                item.clone(title=support.typo('La7d', 'bold'), fulltitle='La7d', url= host + '/live-la7d', action='play', forcethumb = True, no_return=True)]
    return support.thumb(itemlist, live=True)


def replay_channels(item):
    itemlist = [item.clone(title=support.typo('La7', 'bold'), fulltitle='La7', url= host + '/rivedila7/0/la7', action='replay_menu', forcethumb = True),
                item.clone(title=support.typo('La7d', 'bold'), fulltitle='La7d', url= host + '/rivedila7/0/la7d', action='replay_menu', forcethumb = True)]
    return support.thumb(itemlist, live=True)


@support.scrape
def replay_menu(item):
    action = 'replay'
    patron = r'href="(?P<url>[^"]+)"><div class="giorno-text">\s*(?P<day>[^>]+)</div><[^>]+>\s*(?P<num>[^<]+)</div><[^>]+>\s*(?P<month>[^<]+)<'
    def itemHook(item):
        item.title = support.typo(item.day + ' ' + item.num + ' ' + item.month,'bold')
        return item
    return locals()


@support.scrape
def replay(item):
    action = 'play'
    patron = r'guida-tv"><[^>]+><[^>]+>(?P<hour>[^<]+)<[^>]+><[^>]+><[^>]+>\s*<a href="(?P<url>[^"]+)"><[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]+)"><[^>]+><[^>]+><[^>]+><[^>]+>\s*(?P<name>[^<]+)<[^>]+><[^>]+><[^>]+>(?P<plot>[^<]+)<'
    def itemHook(item):
        item.title = support.typo(item.hour + ' - ' + item.name,'bold')
        item.contentTitle = item.fulltitle = item.show = item.name
        item.thumbnail = 'http:' + item.t
        item.fanart = item.thumbnail
        item.forcethumb = True
        return item
    return locals()

def search(item, text):
    item.url = host + '/tutti-i-programmi'
    item.search = text
    return peliculas(item)

@support.scrape
def peliculas(item):
    search = item.search
    disabletmdb = True
    action = 'episodios'
    patron = r'<a href="(?P<url>[^"]+)"[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]+)"></div><div class="titolo">\s*(?P<title>[^<]+)<'
    def itemHook(item):
        item.thumbnail = 'http:' + item.t if item.t.startswith('//') else item.t if item.t else item.thumbnail
        item.fanart = item.thumb
        return item
    return locals()


@support.scrape
def episodios(item):
    data = support.match(item).data
    action = 'play'
    if '>puntate<' in data:
        patronBlock = r'>puntate<(?P<block>.*?)home-block-outbrain'
        url = support.match(data, patron=r'>puntate<[^>]+>[^>]+>[^>]+><a href="([^"]+)"').match
        data += support.match(host + url).data
    else:
        item.url += '/video'
        data = support.match(item).data

    patron = r'(?:<a href="(?P<url>[^"]+)">[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]*)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?(?:[^>]+>)?\s*(?P<title>[^<]+)<(?:[^>]+>[^>]+>[^>]+><div class="data">(?P<date>[^<]+))?|class="heading">[^>]+>(?P<Title>[^<]+).*?window.shareUrl = "(?P<Url>[^"]+)".*?poster:\s*"(?P<Thumb>[^"]+)", title: "(?P<desc>[^"]+)")'
    patronNext = r'<a href="([^"]+)">›'
    addVideolibrary = False

    def itemHook(item):
        if item.Thumb: item.t = item.Thumb
        item.thumbnail = 'http:' + item.t if item.t.startswith('//') else item.t if item.t else item.thumbnail
        if item.Title: item.title = support.typo(item.Title, 'bold')
        if item.date:
            item.title = support.re.sub(r'[Pp]untata (?:del )?\d+/\d+/\d+', '', item.title)
            item.title += support.typo(item.date, '_ [] bold')
        if item.desc: item.plot = item.desc
        item.forcethumb = True
        item.fanart = item.thumbnail
        return item
    return locals()


def play(item):
    support.info()
    data = support.match(item).data
    match = support.match(data, patron='/content/entry/data/(.*?).mp4').match
    if match:
        url = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/entry/data/' + support.match(item, patron='/content/entry/data/(.*?).mp4').match + '.mp4.urlset/master.m3u8'
        item = item.clone(title='Direct', url=url, server='directo', action='play')
    else:
        preurl = support.match(data, patron=r'preTokenUrl = "(.+?)"').match
        url = support.match(data, patron=r'''["]?dash["]?\s*:\s*["']([^"']+)["']''').match
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
    return support.servertools.find_video_items(item, data=url)
