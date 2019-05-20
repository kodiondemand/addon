# support functions that are needed by many channels, to no repeat the same code
import base64, urlparse, re, os, inspect
from core import httptools, scrapertoolsV2, servertools, tmdb
from core.item import Item
import urllib

from lib import unshortenit
from platformcode import logger, config
from channelselector import thumb
from channels import autoplay


def hdpass_get_servers(item):
    # Carica la pagina
    data = httptools.downloadpage(item.url).data.replace('\n', '')
    patron = r'<iframe(?: id="[^"]+")? width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
    url = scrapertoolsV2.find_single_match(data, patron).replace("?alta", "")
    url = url.replace("&download=1", "")
    if 'https' not in url:
        url = 'https:' + url

    if 'hdpass' or 'hdplayer' in url:
        data = httptools.downloadpage(url).data
       
        start = data.find('<div class="row mobileRes">')
        end = data.find('<div id="playerFront">', start)
        data = data[start:end]

        patron_res = '<div class="row mobileRes">(.*?)</div>'
        patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
        patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="([^"]+)" id="urlEmbed"\s*value="([^"]+)"\s*/>'

        res = scrapertoolsV2.find_single_match(data, patron_res)

        itemlist = []

        for res_url, res_video in scrapertoolsV2.find_multiple_matches(res, '<option.*?value="([^"]+?)">([^<]+?)</option>'):

            data = httptools.downloadpage(urlparse.urljoin(url, res_url)).data.replace('\n', '')

            mir = scrapertoolsV2.find_single_match(data, patron_mir)

            for mir_url, server in scrapertoolsV2.find_multiple_matches(mir, '<option.*?value="([^"]+?)">([^<]+?)</value>'):

                data = httptools.downloadpage(urlparse.urljoin(url, mir_url)).data.replace('\n', '')
                for media_label, media_url in scrapertoolsV2.find_multiple_matches(data, patron_media):
                    itemlist.append(Item(channel=item.channel,
                                         action="play",
                                         title=item.title+" ["+color(server, 'orange')+"]"+" - "+color(res_video, 'limegreen'),
                                         fulltitle=item.fulltitle,
                                         quality=res_video,
                                         show=item.show,
                                         thumbnail=item.thumbnail,
                                         contentType=item.contentType,
                                         server=server,
                                         url=url_decode(media_url)))
                    log("video -> ", res_video)

    return itemlist


def url_decode(url_enc):
    lenght = len(url_enc)
    if lenght % 2 == 0:
        len2 = lenght / 2
        first = url_enc[0:len2]
        last = url_enc[len2:lenght]
        url_enc = last + first
        reverse = url_enc[::-1]
        return base64.b64decode(reverse)

    last_car = url_enc[lenght - 1]
    url_enc[lenght - 1] = ' '
    url_enc = url_enc.strip()
    len1 = len(url_enc)
    len2 = len1 / 2
    first = url_enc[0:len2]
    last = url_enc[len2:len1]
    url_enc = last + first
    reverse = url_enc[::-1]
    reverse = reverse + last_car
    return base64.b64decode(reverse)


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"


def scrape(item, patron = '', listGroups = [], headers="", blacklist="", data="", patron_block="",
           patronNext="", action="findvideos", addVideolibrary = True):
    # patron: the patron to use for scraping page, all capturing group must match with listGroups
    # listGroups: a list containing the scraping info obtained by your patron, in order
    # accepted values are: url, title, thumb, quality, year, plot, duration, genre, rating

    # header: values to pass to request header
    # blacklist: titles that you want to exclude(service articles for example)
    # data: if you want to pass data manually, maybe because you need some custom replacement
    # patron_block: patron to get parts of the page (to scrape with patron attribute),
    #               if you need a "block inside another block" you can create a list, please note that all matches
    #               will be packed as string
    # patronNext: patron for scraping next page link
    # action: if you want results perform an action different from "findvideos", useful when scraping film by genres
    # url_host: string to prepend to scrapedurl, useful when url don't contain host
    # example usage:
    #   import support
    #   itemlist = []
    #   patron = 'blablabla'
    #   headers = [['Referer', host]]
    #   blacklist = 'Request a TV serie!'
    #   return support.scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'],
    #                           headers=headers, blacklist=blacklist)

    itemlist = []

    if not data:
        data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
        data = re.sub('\n|\t', ' ', data)
        # replace all ' with " and eliminate newline, so we don't need to worry about
        log('DATA =', data)

        block = data

        if patron_block:
            if type(patron_block) == str:
                patron_block = [patron_block]

            for n, regex in enumerate(patron_block):
                blocks = scrapertoolsV2.find_multiple_matches(block, regex)
                block = ""
                for b in blocks:
                    block += "\n" + b
                log('BLOCK ', n, '=', block)
    else:
        block = data
    if patron and listGroups:
        matches = scrapertoolsV2.find_multiple_matches(block, patron)
        log('MATCHES =', matches)

        known_keys = ['url', 'title', 'episode', 'thumb', 'quality', 'year', 'plot', 'duration', 'genere', 'rating'] #by greko aggiunto episode
        for match in matches:
            if len(listGroups) > len(match):  # to fix a bug
                match = list(match)
                match.extend([''] * (len(listGroups) - len(match)))

            scraped = {}
            for kk in known_keys:
                val = match[listGroups.index(kk)] if kk in listGroups else ''
                if val and (kk == "url" or kk == 'thumb') and 'http' not in val:
                    val = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+') + val
                scraped[kk] = val

            title = scrapertoolsV2.decodeHtmlentities(scraped["title"]).strip()
            plot = scrapertoolsV2.htmlclean(scrapertoolsV2.decodeHtmlentities(scraped["plot"]))

            if scraped["quality"] and scraped["episode"]: # by greko aggiunto episode
                longtitle = '[B]' + title + '[/B] - [B]' + scraped["episode"] + '[/B][COLOR blue][' + scraped["quality"] + '][/COLOR]' # by greko aggiunto episode
            elif scraped["episode"]: # by greko aggiunto episode
                longtitle = '[B]' + title + '[/B] - [B]' + scraped["episode"] + '[/B]' # by greko aggiunto episode
            else:
                longtitle = '[B]' + title + '[/B]'

            if item.infoLabels["title"] or item.fulltitle:  # if title is set, probably this is a list of episodes or video sources
                infolabels = item.infoLabels
            else:
                infolabels = {}
                if scraped["year"]:
                    infolabels['year'] = scraped["year"]
                if scraped["plot"]:
                    infolabels['plot'] = plot
                if scraped["duration"]:
                    matches = scrapertoolsV2.find_multiple_matches(scraped["duration"],r'([0-9])\s*?(?:[hH]|:|\.|,|\\|\/|\||\s)\s*?([0-9]+)')
                    for h, m in matches:
                        scraped["duration"] = int(h) * 60 + int(m)
                    if not matches:
                        scraped["duration"] = scrapertoolsV2.find_single_match(scraped["duration"], r'(\d+)')
                    infolabels['duration'] = int(scraped["duration"]) * 60
                if scraped["genere"]:
                    genres = scrapertoolsV2.find_multiple_matches(scraped["genere"], '[A-Za-z]+')
                    infolabels['genere'] = ", ".join(genres)
                if scraped["rating"]:
                    infolabels['rating'] = scrapertoolsV2.decodeHtmlentities(scraped["rating"])

            if scraped["title"] not in blacklist:
                it = Item(
                    channel=item.channel,
                    action=action,
                    contentType=item.contentType,
                    title=longtitle,
                    fulltitle=title,
                    show=title,
                    quality=scraped["quality"],
                    url=scraped["url"],
                    infoLabels=infolabels,
                    thumbnail=scraped["thumb"],
                    args=item.args
                )

                for lg in list(set(listGroups).difference(known_keys)):
                    it.__setattr__(lg, match[listGroups.index(lg)])

                itemlist.append(it)

        if (item.contentType == "episode" and (action != "findvideos" and action != "play")) \
                or (item.contentType == "movie" and action != "play"):
            tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        else:
            for it in itemlist:
                it.infoLabels = item.infoLabels

        if patronNext:
            nextPage(itemlist, item, data, patronNext, 2)

        if addVideolibrary and (item.infoLabels["title"] or item.fulltitle):
            item.fulltitle = item.infoLabels["title"]
            videolibrary(itemlist, item)

    return itemlist


def dooplay_get_links(item, host):
    # get links from websites using dooplay theme and dooplay_player
    # return a list of dict containing these values: url, title and server

    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    ret = []

    for type, post, nume, title, server in matches:
        postData = urllib.urlencode({
            "action": "doo_player_ajax",
            "post": post,
            "nume": nume,
            "type": type
        })
        dataAdmin = httptools.downloadpage(host + 'wp-admin/admin-ajax.php', post=postData,headers={'Referer': item.url}).data
        link = scrapertoolsV2.find_single_match(dataAdmin, "<iframe.*src='([^']+)'")
        ret.append({
            'url': link,
            'title': title,
            'server': server
        })

    return ret


def dooplay_get_episodes(item):
    itemlist = []
    item.contentType = "episode"
    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = '<li class="mark-[0-9]">.*?<img.*?data-lazy-src="([^"]+).*?([0-9] - [0-9]).*?<a href="([^"]+)">([^<>]+).*?([0-9]{4})'

    for scrapedthumb, scrapedep, scrapedurl, scrapedtitle, scrapedyear in scrapertoolsV2.find_multiple_matches(data, patron):
        scrapedep = scrapedep.replace(' - ', 'x')
        infoLabels = {}
        infoLabels['year'] = scrapedyear

        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="episode",
                 title=scrapedep + " " + scrapedtitle,
                 fulltitle=scrapedtitle,
                 show=item.fulltitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumb,
                 infoLabels=infoLabels
                 )
        )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    videolibrary(itemlist, item)
    return itemlist


def dooplay_films(item, blacklist=""):
    if item.contentType == 'movie':
        action = 'findvideos'
        patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="(?!data)([^"]+)".*?<span class="quality">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a></h3>.*?(?:<span>([0-9]{4})</span>|</article>).*?(?:<span>([0-9]+) min</span>|</article>).*?(?:<div class="texto">([^<>]+)|</article>).*?(?:genres">(.*?)</div>|</article>)'
    else:
        action = 'episodios'
        patron = '<article id="post-[0-9]+" class="item tvshows">.*?<img src="(?!data)([^"]+)".*?(?:<span class="quality">([^<>]+))?.*?<a href="([^"]+)">([^<>]+)</a></h3>.*?(?:<span>([0-9]{4})</span>|</article>).*?(?:<span>([0-9]+) min</span>|</article>).*?(?:<div class="texto">([^<>]+)|</article>).*?(?:genres">(.*?)</div>|</article>)'
    # patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    patronNext = '<div class="pagination">.*?class="current".*?<a href="([^"]+)".*?<div class="resppages">'
    itemlist = scrape(item, patron, ['thumb', 'quality', 'url', 'title', 'year', 'duration', 'plot', 'genre'], blacklist=blacklist, patronNext=patronNext, action=action, addVideolibrary=False)
    if itemlist and 'Successivo' in itemlist[-1].title:
        itemlist[-1].action = 'peliculas'

    return itemlist

    
def dooplay_search(item, blacklist=""):
    if item.contentType == 'movie':
        type = 'movies'
        action = 'findvideos'
    else:
        type = 'tvshows'
        action = 'episodios'
    patron = '<div class="result-item">.*?<img src="([^"]+)".*?<span class="' + type + '">([^<>]+).*?<a href="([^"]+)">([^<>]+)</a>.*?<span class="year">([0-9]{4}).*?<div class="contenido"><p>([^<>]+)'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'
    return scrape(item, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot'], blacklist=blacklist, patronNext=patronNext, action=action)


def swzz_get_url(item):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:59.0) Gecko/20100101 Firefox/59.0'}

    if "/link/" in item.url:
        data = httptools.downloadpage(item.url, headers=headers).data
        if "link =" in data:
            data = scrapertoolsV2.find_single_match(data, 'link = "([^"]+)"')
            if 'http' not in data:
                data = 'https:' + data
        else:
            match = scrapertoolsV2.find_single_match(data, r'<meta name="og:url" content="([^"]+)"')
            match = scrapertoolsV2.find_single_match(data, r'URL=([^"]+)">') if not match else match

            if not match:
                from lib import jsunpack

                try:
                    data = scrapertoolsV2.find_single_match(data.replace('\n', ''), r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>")
                    data = jsunpack.unpack(data)

                    logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
                except:
                    logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

                data = scrapertoolsV2.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
                data, c = unshortenit.unwrap_30x_only(data)
            else:
                data = match
        if data.startswith('/'):
            data = urlparse.urljoin("http://swzz.xyz", data)
            if not "vcrypt" in data:
                data = httptools.downloadpage(data).data
        logger.debug("##### play /link/ data ##\n%s\n##" % data)
    else:
        data = item.url

    return data


def menu(itemlist, title='', action='', url='', contentType='movie', args=[]):
    # Function to simplify menu creation

    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename).replace('.py','')

    # Call typo function
    title = typo(title)

    if contentType == 'movie': extra = 'movie'
    else: extra = 'tvshow'

    itemlist.append(Item(
        channel = filename,
        title = title,
        action = action,
        url = url,
        extra = extra,
        args = args,
        contentType = contentType
    ))

    # Apply auto Thumbnails at the menus
    from channelselector import thumb
    thumb(itemlist)

    return itemlist


def typo(string, typography=''):

    kod_color = '0xFF65B3DA' #'0xFF0081C2'


    # Check if the typographic attributes are in the string or outside
    if typography:
        string = string + ' ' + typography
    if config.get_localized_string(30992) in string:
        string = string + ' >'

    # If there are no attributes, it applies the default ones
    attribute = ['[]','()','{}','submenu','color','bold','italic','_','--','[B]','[I]','[COLOR]']

    movie_word_list = ['film', 'serie', 'tv', 'anime', 'cinema', 'sala']
    search_word_list = ['cerca']
    categories_word_list = ['genere', 'categoria', 'categorie', 'ordine', 'lettera', 'anno', 'alfabetico', 'a-z', 'menu']

    if not any(word in string for word in attribute):
        if any(word in string.lower() for word in search_word_list):
            string = '[COLOR '+ kod_color +']' + string + '[/COLOR]'
        elif any(word in string.lower() for word in categories_word_list):
            string = ' > ' + string
        elif any(word in string.lower() for word in movie_word_list):
            string = '[B]' + string + '[/B]'

    # Otherwise it uses the typographical attributes of the string
    else:        
        if '[]' in string:
            string = '[' + re.sub(r'\s\[\]','',string) + ']'
        if '()' in string:
            string = '(' + re.sub(r'\s\(\)','',string) + ')'
        if '{}' in string:
            string = '{' + re.sub(r'\s\{\}','',string) + '}'
        if 'submenu' in string:
            string = ' > ' + re.sub(r'\ssubmenu','',string)
        if 'color' in string:
            color = scrapertoolsV2.find_single_match(string,'color ([a-z]+)')
            if color == 'kod' or '': color = kod_color
            string = '[COLOR '+ color +']' + re.sub(r'\scolor\s([a-z]+)','',string) + '[/COLOR]'
        if 'bold' in string:
            string = '[B]' + re.sub(r'\sbold','',string) + '[/B]'
        if 'italic' in string:
            string = '[I]' + re.sub(r'\sitalic','',string) + '[/I]' 
        if '_' in string:
            string = ' ' + re.sub(r'\s_','',string)
        if '--' in string:
            string = ' - ' + re.sub(r'\s--','',string)

    return string


def match(item, patron='', patron_block='', headers='', url=''):
    matches = []
    url = url if url else item.url
    data = httptools.downloadpage(url, headers=headers).data.replace("'", '"')
    data = re.sub('\n|\t', '', data)
    log('DATA= ', data)

    if patron_block:
        block = scrapertoolsV2.find_single_match(data, patron_block)
        log('BLOCK= ',block)
    else:
        block = data
        
    if patron:
        matches = scrapertoolsV2.find_multiple_matches(block, patron)
        log('MATCHES= ',matches)

    return matches, data


def videolibrary(itemlist, item, typography=''):
    if item.contentType != 'episode':
        action = 'add_pelicula_to_library'
        extra = 'findvideos'
        contentType = 'movie'
    else:
        action = 'add_serie_to_library'
        extra = 'episodios'
        contentType = 'tvshow'
    if not typography: typography = 'color kod bold'
    title = typo(config.get_localized_string(30161) + ' ' + typography)
    if inspect.stack()[1][3] == 'findvideos' and contentType == 'movie' or inspect.stack()[1][3] != 'findvideos' and contentType != 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                Item(channel=item.channel,
                     title=title,
                     contentType=contentType,
                     contentSerieName=item.fulltitle if contentType == 'tvshow' else '',
                     url=item.url,
                     action=action,
                     extra=extra,
                     contentTitle=item.fulltitle))


def nextPage(itemlist, item, data, patron, function_level=1):
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    
    next_page = scrapertoolsV2.find_single_match(data, patron)
    if 'http' not in next_page:
        next_page = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+') + next_page
    log('NEXT= ', next_page)

    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action=inspect.stack()[function_level][3],
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992), 'color kod bold'),
                 url=next_page,
                 args=item.args,
                 thumbnail=thumb()))

    return itemlist

def server(item, data='', headers='', AutoPlay=True, CheckLinks=True):
    
    __comprueba_enlaces__ = config.get_setting('comprueba_enlaces', item.channel)
    log(__comprueba_enlaces__ )
    __comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', item.channel)
    log(__comprueba_enlaces_num__ )

    if not data:
        data = httptools.downloadpage(item.url, headers=headers).data
        
    itemlist = servertools.find_video_items(data=str(data))

    for videoitem in itemlist:
        videoitem.title = "".join([item.title, ' ', typo(videoitem.title, 'color kod []')])
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType

    if __comprueba_enlaces__ and CheckLinks:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
    
    if AutoPlay == True:
        autoplay.start(itemlist, item)

    return itemlist


def aplay(item, itemlist, list_servers='', list_quality=''):
    if inspect.stack()[1][3] == 'mainlist':
        autoplay.init(item.channel, list_servers, list_quality)
        autoplay.show_option(item.channel, itemlist)
    else:
        autoplay.start(itemlist, item)


def log(stringa1="", stringa2="", stringa3="", stringa4="", stringa5=""):
    # Function to simplify the log
    # Automatically returns File Name and Function Name
    
    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename)    
    logger.info("[" + filename + "] - [" + inspect.stack()[1][3] + "] " + str(stringa1) + str(stringa2) + str(stringa3) + str(stringa4) + str(stringa5))
