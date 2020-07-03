# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeForce
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()





headers = [['Referer', host]]


@support.menu
def mainlist(item):
    anime = ['/lista-anime/',
             ('In Corso',['/lista-anime-in-corso/', 'peliculas', 'corso']),
             ('Ultime Serie',['/category/anime/articoli-principali/','peliculas','last'])
            ]
    return locals()


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.contentType = 'tvshow'
            item.url = host
            item.args = 'newest'
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

def search(item, texto):
    support.log(texto)
    item.args = 'noorder'
    item.url = host + '/?s=' + texto + '&cat=6010'
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    anime = True
    action = 'episodios'
    if not item.args:
        pagination = ''
        patron = r'<a\s*href="(?P<url>[^"]+)"\s*title="(?P<title>[^"]+)">'
    elif item.args == 'corso':
        pagination = ''
        patron = r'<strong><a href="(?P<url>[^"]+)">(?P<title>.*?) [Ss][Uu][Bb]'
    else:
        patron = r'<a href="(?P<url>[^"]+)"[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: Sub| sub| SUB|")'

    if item.args == 'newest': item.action = 'findvideos'

    def itemHook(item):
        if 'sub-ita' in item.url:
            if item.args != 'newest': item.title = item.title + support.typo('Sub-ITA','_ [] color kod')
            item.contentLanguage = 'Sub-ITA'
        return item

    return locals()


@support.scrape
def episodios(item):
    anime = True
    data = support.match(item, headers=headers).data
    if '<h6>Streaming</h6>' in data:
        patron = r'<td style[^>]+>\s*.*?(?:<span[^>]+)?<strong>(?P<title>[^<]+)<\/strong>.*?<td style[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>'
    else:
        patron = r'<a\s*href="(?P<url>[^"]+)"\s*title="(?P<title>[^"]+)"\s*class="btn btn-dark mb-1">'
    def itemHook(item):
        support.log(item)
        if item.url.startswith('//'): item.url= 'https:' + item.url
        elif item.url.startswith('/'): item.url= 'https:/' + item.url
        return item
    action = 'findvideos'
    return locals()


def findvideos(item):
    support.log(item)
    # try:
    #     from urlparse import urljoin
    # except:
    #     from urllib.parse import urljoin
    # support.dbg()
    itemlist = []
    if 'vvvvid' in item.url:
        import requests
        from lib import vvvvid_decoder
        
        if support.match(item.url, string=True, patron=r'(\d+/\d+)').match:
            item.action = 'play'
            itemlist.append(item)
        else:
            # VVVVID vars
            vvvvid_host = 'https://www.vvvvid.it/vvvvid/ondemand/'
            vvvvid_headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

            # VVVVID session
            current_session = requests.Session()
            login_page = 'https://www.vvvvid.it/user/login'
            conn_id = current_session.get(login_page, headers=vvvvid_headers).json()['data']['conn_id']
            payload = {'conn_id': conn_id}


            # collect parameters
            show_id = support.match(item.url, string=True, patron=r'(\d+)').match
            ep_number = support.match(item.title, patron=r'(\d+)').match
            json_file = current_session.get(vvvvid_host + show_id + '/seasons/', headers=vvvvid_headers, params=payload).json()
            season_id = str(json_file['data'][0]['season_id'])
            json_file = current_session.get(vvvvid_host + show_id + '/season/' + season_id +'/', headers=vvvvid_headers, params=payload).json()

            # select the correct episode
            for episode in json_file['data']:
                support.log('Number',int(episode['number']),int(ep_number))
                if int(episode['number']) == int(ep_number):
                    url = vvvvid_decoder.dec_ei(episode['embed_info'] or episode['embed_info'])
                    if 'youtube' in url: item.url = url
                    item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
                    if 'https' not in item.url:
                        url = support.match(item, url='https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/playlist.m3u')[1]
                        url = url.split()[-1]
                        itemlist.append(item.clone(action= 'play', url= 'https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/' + url, server= 'directo'))

    elif 'adf.ly' in item.url:
        from servers.decrypters import adfly
        url = adfly.get_long_url(item.url)

    elif 'bit.ly' in item.url:
        url = support.httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location")

    else:
        url = host
        for u in item.url.split('/'):
            # support.log(i)
            if u and 'animeforce' not in u and 'http' not in u:
                url += '/' + u

        if 'php?' in url:
            url = support.httptools.downloadpage(url, only_headers=True, follow_redirects=False).headers.get("location")
            url = support.match(url, patron=r'class="button"><a href=(?:")?([^" ]+)', headers=headers).match
        else:
            url = support.match(url, patron=[r'<source src=(?:")?([^" ]+)',r'name="_wp_http_referer" value="([^"]+)"']).match
        if url.startswith('//'): url = 'https:' + url
        elif url.startswith('/'): url = 'https:/' + url


        itemlist.append(item.clone(action="play", title='Diretto', url=url, server='directo'))

    return support.server(item, itemlist=itemlist)
