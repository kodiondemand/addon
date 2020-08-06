# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Mediaset Play
# ------------------------------------------------------------

import requests, sys
from core import support
if sys.version_info[0] >= 3: from urllib.parse import urlencode, quote
else: from urllib import urlencode, quote

DRM = 'com.widevine.alpha'
post_url = '?assetTypes=HD,browser,widevine:HD,browser:SD,browser,widevine:SD,browser:SD&auto=true&balance=true&format=smil&formats=MPEG-DASH,MPEG4,M3U&tracking=true'

current_session = requests.Session()

data = {"cid": "dc4e7d82-89a5-4a96-acac-d3c7f2ca6d67", "platform": "pc", "appName": "web/mediasetplay-web/576ea90"}
res = current_session.post("https://api-ott-prod-fe.mediaset.net/PROD/play/idm/anonymous/login/v1.0", json=data, verify=False)

current_session.headers.update({'t-apigw': res.headers['t-apigw']})
current_session.headers.update({'t-cts': res.headers['t-cts']})

lic_url = 'https://widevine.entitlement.theplatform.eu/wv/web/ModularDrm/getRawWidevineLicense?releasePid=%s&account=http://access.auth.theplatform.com/data/Account/2702976343&schema=1.0&token=' + res.headers['t-cts'] + '|Accept=*/*&Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36|R{SSM}|'

tracecid=res.json()['response']['traceCid']
cwid=res.json()['response']['cwId']

res = current_session.get("https://api.one.accedo.tv/session?appKey=59ad346f1de1c4000dfd09c5&uuid=sdd",verify=False)
current_session.headers.update({'x-session': res.json()['sessionKey']})

host = ''
entry = 'https://api.one.accedo.tv/content/entry/{id}?locale=it'
entries = 'https://api.one.accedo.tv/content/entries?id={id}&locale=it'


@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-stations?sort=ShortTitle', 'live'])]

    menu = [('Film {bullet bold}', ['5acfcbc423eec6000d64a6bb', 'menu', ['Tutti','all','Cinema']]),
            ('Fiction / Serie TV {bullet bold}', ['5acfcb3c23eec6000d64a6a4', 'menu', ['Tutte','all','Fiction'], 'tvshow']),
            ('Programmi TV{ bullet bold}', ['', 'menu', ['Tutti','all','Programmi Tv'], 'tvshow']),
            ('Documentari {bullet bold}', ['5bfd17c423eec6001aec49f9', 'menu', ['Tutti','all','Documentari'], 'undefined']),
            ('Kids {bullet bold}', ['5acfcb8323eec6000d64a6b3', 'menu',['Tutti','all','Kids'], 'undefined']),
           ]

    search = ''
    return locals()



def search(item, text):
    support.log(text)
    item.search = text
    if not item.args:
        item.contentType = 'undefined'
        item.args=['','all','']
    itemlist = []
    try:
        itemlist += peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
    return itemlist

def menu(item):
    support.log()
    itemlist = [item.clone(title=support.typo(item.args[0],'bullet bold'), url='', action='peliculas')]
    if item.url:
        json = get_from_id(item)
        for it in json:
            if 'uxReference' in it: itemlist.append(item.clone(title=support.typo(it['title'], 'submenu'), url=it['uxReference'], args = '', action='peliculas'))
    itemlist.append(item.clone(title=support.typo('Cerca...','submenu bold'), url='', action ='search'))
    return itemlist

def live(item):
    support.log()
    itemlist = []
    json = current_session.get(item.url).json()['entries']
    for it in json:
        urls = []
        if it['tuningInstruction'] and not it['mediasetstation$digitalOnly']:
            guide=current_session.get('https://static3.mediasetplay.mediaset.it/apigw/nownext/' + it['callSign'] + '.json').json()['response']
            if 'restartUrl' in guide['currentListing']:
                urls = [guide['currentListing']['restartUrl']]
            else:
                for key in it['tuningInstruction']['urn:theplatform:tv:location:any']:
                    urls += key['publicUrls']
            plot = support.typo(guide['currentListing']['mediasetlisting$epgTitle'],'bold') + '\n' + guide['currentListing']['mediasetlisting$shortDescription'] + '\n' + guide['currentListing']['description'] + '\n\n' + support.typo('A Seguire:' + guide['nextListing']['mediasetlisting$epgTitle'], 'bold')
            itemlist.append(item.clone(title=support.typo(it['title'], 'bold'),
                                       fulltitle=it['title'],
                                       show=it['title'],
                                       contentTitle=it['title'],
                                       thumbnail=it['thumbnails']['channel_logo-100x100']['url'],
                                       forcethumb = True,
                                       urls=urls,
                                       plot=plot,
                                       action='play'))
    return itemlist

def peliculas(item):
    support.log()
    itemlist = []
    contentType = ''
    json = get_programs(item)
    for it in json:
        if item.search.lower() in it['title'].lower():
            if item.contentType == 'movie':
                action = 'findvideos'
                urls = []
                if 'media' not in it: it = subBrand(it['mediasetprogram$brandId'])[-1]
                if 'media' in it:
                    for key in it['media']:
                        urls.append(key['publicUrl'])
            elif item.contentType == 'tvshow':
                action = 'epmenu'
                urls = it['mediasetprogram$brandId']
            else:
                if 'media' in it:
                    action = 'findvideos'
                    contentType = 'movie'
                    urls = []
                    for key in it['media']:
                        urls.append(key['publicUrl'])
                else:
                    action = 'epmenu'
                    contentType = 'tvshow'
                    urls = it['mediasetprogram$brandId']
            if urls:
                itemlist.append(
                    item.clone(channel=item.channel,
                               action=action,
                               title=support.typo(it['title'], 'bold'),
                               fulltitle=it['title'],
                               show=it['title'],
                               contentType=contentType if contentType else item.contentType,
                               contentTitle=it['title'] if 'movie' in [contentType, item.contentType] else '',
                               contentSerieName=it['title'] if 'tvshow' in [contentType, item.contentType] else '',
                               thumbnail=it['thumbnails']['image_vertical-264x396']['url'] if 'image_vertical-264x396' in it['thumbnails'] else '',
                               fanart=it['thumbnails']['image_keyframe_poster-1280x720']['url'] if 'image_keyframe_poster-1280x720' in it['thumbnails'] else '',
                               plot=it['longDescription'] if 'longDescription' in it else it['description'] if 'description' in it else '',
                               urls=urls,
                               url=it['mediasetprogram$pageUrl']))
    return itemlist

def epmenu(item):
    support.log()
    itemlist = []
    entries = current_session.get('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?byCustomValue={brandId}{' + item.urls + '}').json()['entries']
    for entry in entries:
        if 'mediasetprogram$subBrandId' in entry:
            itemlist.append(
                item.clone(action='episodios',
                            title=support.typo(entry['description'], 'bold'),
                            subBrandId=entry['mediasetprogram$subBrandId']))
    if len(itemlist) == 1: return episodios(itemlist[0])
    return itemlist



def episodios(item):
    support.log()
    itemlist = []
    episode = ''
    # entries = current_session.get('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?byCustomValue={brandId}{' + item.urls + '}').json()['entries']

    # for entry in entries:
    #     support.log(entry)
    #     if 'mediasetprogram$subBrandId' in entry and entry['description'].lower() not in ['Prossimi appuntamenti tv', 'clip']:
    #         subBrandId = entry['mediasetprogram$subBrandId']
    #         break

    json = current_session.get('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs?byCustomValue={subBrandId}{' + item.subBrandId + '}').json()['entries']
    for it in json:
        urls = []
        if 'media' in it:
            for key in it['media']:
                urls.append(key['publicUrl'])
        if urls:
            title = it['title'].split('-')[-1].strip()
            if it['tvSeasonNumber'] and it['tvSeasonEpisodeNumber']:
                item.infoLabels['season'] = it['tvSeasonNumber']
                item.infoLabels['episode'] = it['tvSeasonEpisodeNumber']
                episode = '%dx%02d - ' % (it['tvSeasonNumber'], it['tvSeasonEpisodeNumber'])
            itemlist.append(
                item.clone(action='findvideos',
                           title=support.typo(episode + title, 'bold'),
                           contentType='episode',
                           thumbnail=it['thumbnails']['image_vertical-264x396']['url'] if 'image_vertical-264x396' in it['thumbnails'] else '',
                           fanart=it['thumbnails']['image_keyframe_poster-1280x720']['url'] if 'image_keyframe_poster-1280x720' in it['thumbnails'] else '',
                           plot=it['longDescription'] if 'longDescription' in it else it['description'],
                           urls=urls,
                           url=it['mediasetprogram$pageUrl']))
    if episode: support.videolibrary(itemlist, item)
    return sorted(itemlist, key=lambda it: it.title)

def findvideos(item):
    support.log()
    itemlist = [support.Item(server = 'directo', title = 'Direct', url = item.urls, action = 'play')]
    return support.server(item, itemlist=itemlist, Download=False)

def play(item):
    support.log()
    if not item.urls: urls = item.url
    else: urls = item.urls
    for url in urls:
        new_url = support.httptools.downloadpage(url, allow_redirects=True).url
        if '.mpd' in new_url:
            data = new_url
            sec_data = support.match(url + post_url).data
            if support.match(sec_data, patron=r'(security)').match:
                item.drm = DRM
                item.license = lic_url % support.match(sec_data, patron=r'pid=([^|]+)').match
                data = support.match(sec_data, patron=r'<video src="([^"]+)').match

    return support.servertools.find_video_items(item, data=data)

def subBrand(json):
    support.log()
    subBrandId = current_session.get('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-brands?byCustomValue={brandId}{' + json + '}').json()['entries'][-1]['mediasetprogram$subBrandId']
    json = current_session.get('https://feed.entertainment.tv.theplatform.eu/f/PR1GhC/mediaset-prod-all-programs?byCustomValue={subBrandId}{' + subBrandId + '}').json()['entries']
    return json

def get_from_id(item):
    support.log()
    json = current_session.get(entry.format(id=item.url)).json()
    if 'components' in json:
        id = quote(",".join(json["components"]))
        json = current_session.get(entries.format(id=id)).json()
    if 'entries' in json:
        return json['entries']
    return {}

def get_programs(item, ret=[], args={}):
    support.log()
    hasMore = False
    if not args:
        if item.url:
            args['uxReference'] = item.url
            args['platform'] = 'pc'
        else:
            args = {"query": "*:*"}
            if item.args[2]:
                args['categories'] = item.args[2]

        args['cwId'] = cwid
        args['traceCid'] = tracecid
        args['hitsPerPage'] = 500
        args['page'] = '0'

    if 'all' in item.args: url = 'https://api-ott-prod-fe.mediaset.net/PROD/play/rec/azlisting/v1.0?' + urlencode(args)
    else: url="https://api-ott-prod-fe.mediaset.net/PROD/play/rec/cataloguelisting/v1.0?" + urlencode(args)
    json = current_session.get(url).json()
    if 'response' in json:
        json = json['response']
    if 'hasMore' in json:
        hasMore = json['hasMore']
    if 'components' in json:
        id = quote(",".join(json["components"]))
        json = current_session.get(entries.format(id=id)).json()
    if 'entries' in json:
        ret += json['entries']
    if hasMore:
        args['page'] = str(int(args['page']) + 1)
        return get_programs(item, ret, args)
    else:
        return ret