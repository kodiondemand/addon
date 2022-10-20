# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per accuradio
# ------------------------------------------------------------

import random
from core import httptools, support
from platformcode import logger

host = 'https://www.accuradio.com'
api_url = host + '/c/m/json/{}/'
headers = [['Referer', host]]



def mainlist(item):
    itemlist = []
    item.action = 'peliculas'
    js = httptools.downloadpage(api_url.format('brands')).json
    for it in js.get('features',[]):
        itemlist.append(
            item.clone(url= '{}/{}'.format(host,it.get('canonical_url','')),
                       title=support.typo(it['name'],'italic') + support.typo(it.get('channels',''),'_ [] color kod')
            ))
    for it in js.get('brands',[]):
        itemlist.append(
            item.clone(url= '{}/{}'.format(host,it.get('canonical_url','')),
                       title=support.typo(it['name'],'bullet bold') + support.typo(it.get('channels',''),'_ [] color kod')
            ))

    itemlist.append(item.clone(title=support.typo('Cerca...', 'bold color kod'), action='search', thumbnail=support.thumb('search')))
    support.channel_config(item, itemlist)
    return itemlist


@support.scrape
def peliculas(item):
    # debug=True
    action = 'playradio'
    patron = r'data-id="(?P<id>[^"]+)"\s*data-oldid="(?P<oldid>[^"]+)".*?data-name="(?P<title>[^"]+)(?:[^>]+>){2}<img src="(?P<thumb>[^"]+)(?:[^>]+>){16}\s*(?P<plot>[^<]+)'
    return locals()


def playradio(item):
    import xbmcgui, xbmc
    items = httptools.downloadpage('{}/playlist/json/{}/?ando={}&rand={}'.format(host, item.id, item.oldid, random.random())).json
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    for i in items:
        if 'id' in i:
            url = i['primary'] + i['fn'] + '.m4a'
            title = i['title']
            artist = i['track_artist']
            album = i['album']['title']
            year = i['album']['year']
            thumb = 'https://www.accuradio.com/static/images/covers300' + i['album']['cdcover']
            duration = i.get('duration',0)
            info = {'duration':duration,
                    'album':album,
                    'artist':artist,
                    'title':title,
                    'year':year,
                    'mediatype':'music'}
            item = xbmcgui.ListItem(title, path=url)
            item.setArt({'thumb':thumb, 'poster':thumb, 'icon':thumb})
            item.setInfo('music',info)
            playlist.add(url, item)
    xbmc.Player().play(playlist)


def search(item, text):
    support.info(text)
    item.url = host + '/search/' + text
    itemlist = []
    try:
        data = support.match(item.url).data
        artists = support.match(data, patronBlock=r'artistResults(.*?)</ul', patron=r'href="(?P<url>[^"]+)"\s*>(?P<title>[^<]+)').matches
        if artists:
            for url, artist in artists:
                itemlist.append(item.clone(title=support.typo(artist,'bullet bold'), thumbnail=support.thumb('music'), url=host+url, action='peliculas'))
        item.data = data
        itemlist += peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return itemlist
