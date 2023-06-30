# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per tunein
# ------------------------------------------------------------

from core import httptools, support
from platformcode import logger


host = 'http://api.radiotime.com'
args = 'formats=mp3,aac,ogg,flash,html,hls,wma&partnerId=RadioTime&itemToken='


@support.menu
def mainlist(item):
    menu = [('Musica {bullet music}' ,['/categories/music?{}'.format(args), 'radio', '',  'music']),
            ('Sport {bullet music}' ,['/categories/sports?{}'.format(args), 'radio', '',  'music']),
            ('Notizie e Dibattiti {bullet music}' ,['/categories/c57922?{}'.format(args), 'radio', ''  'music']),
            ('Podcast {bullet music}' ,['/categories/c100000088?{}'.format(args), 'radio', '',  'music']),
            ('Audiolibri {bullet music}' ,['/categories/c100006408?{}'.format(args), 'radio', '',  'music']),
            ('Luogo {bullet music}' ,['/categories/regions?{}'.format(args), 'radio', '',  'music']),
            ('Lingua {bullet music}' ,['/categories/languages?{}'.format(args), 'radio', '',  'music'])]
    search =''
    return locals()


def search(item, text):
    support.info(text)
    itemlist = list()

    try:
        js = httptools.downloadpage('{}/profiles?fullTextSearch=true&query={}&{}'.format(host, text, args)).json
        data = js.get('Items', {})
        for c in data:
            if c.get('Pivots',{}).get('More',{}).get('Url', ''):
                data = httptools.downloadpage(c.get('Pivots',{}).get('More',{}).get('Url', '')).json.get('Items',{})
            else:
                data = c.get('Children')
            if data:
                itemlist.extend(buildItemList(item, data))

        if js.get('Paging', {}).get('Next'):
            support.nextPage(itemlist, item, next_page=js.get('Paging', {}).get('Next'))
        return itemlist
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error(line)
        return []


def radio(item):
    itemlist = list()
    js = dict()
    if item.data:
        data = item.data
    else:
        js = httptools.downloadpage(item.url).json
        data = js.get('Items', {})

    itemlist = buildItemList(item, data)
    if js.get('Paging', {}).get('Next'):
        support.nextPage(itemlist, item, next_page=js.get('Paging', {}).get('Next'))

    return itemlist



def buildItemList(item, data):
    itemlist = list()
    # support.dbg()
    for c in data:
        item.data = ''
        item.action = 'radio'
        token = c.get('Context',{}).get('Token','')
        if not token:
            token = c.get('Actions', {}).get('Context',{}).get('Token','')
        if not c.get('Title', c.get('AccessibilityTitle')) or 'premium' in c.get('Title', c.get('AccessibilityTitle')).lower():
            continue

        if c.get('Children'):
            if len(data) > 1:
                if c.get('Pivots',{}).get('More',{}).get('Url', ''):
                    itm = item.clone(title=c.get('Title', c.get('AccessibilityTitle')),
                                    url=c.get('Pivots',{}).get('More',{}).get('Url', ''),
                                    token=token)
                else:
                    itm = item.clone(title=c.get('Title', c.get('AccessibilityTitle')),
                                    data=c.get('Children'),
                                    token=token)
            else:
                if c.get('Pivots',{}).get('More',{}).get('Url', ''):
                    data = httptools.downloadpage(c.get('Pivots',{}).get('More',{}).get('Url', '')).json.get('Items', {})
                else:
                    data = c.get('Children')
                return buildItemList(item, data)

        elif c.get('GuideId'):
            title = c.get('Title', c.get('AccessibilityTitle'))
            plot = '[B]{}[/B]\n{}'.format(c.get('Subtitle', ''), c.get('Description', ''))
            thumbnail = c.get('Image', '')
            if c.get('GuideId').startswith('s'):
                itm = item.clone(title=title,
                                plot=plot,
                                thumbnail=thumbnail,
                                url = 'http://opml.radiotime.com/Tune.ashx?render=json&id={}&{}{}'.format(c.get('GuideId'), args, token),
                                action = 'findvideos')

            else:
                itm = item.clone(title=title,
                                plot=plot,
                                thumbnail=thumbnail,
                                url = c.get('Actions', {}).get('Browse',{}).get('Url',''))


        elif c.get('Actions', {}).get('Browse',{}).get('Url',''):
            title = c.get('Title', c.get('AccessibilityTitle'))
            itm = item.clone(title = title,
                            url = c.get('Actions', {}).get('Browse',{}).get('Url',''))


        itemlist.append(itm)

    return itemlist


def findvideos(item):
    item.action = 'play'

    js = httptools.downloadpage(item.url, cloudscraper=True).json.get('body',  {})
    video_urls = list()
    for it in js:
        video_urls.append(['m3u8 [{}]'.format(it.get('bitrate')), it.get('url')])

    item.referer = False
    item.server = 'directo'
    item.video_urls = video_urls
    return [item]
