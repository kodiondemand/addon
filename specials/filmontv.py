# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------
from datetime import datetime
import glob, time, gzip, xbmc
from core import filetools, downloadtools, support, scrapertools
from core.item import Item
from platformcode import logger

host = "http://epg-guide.com/kltv.gz"
blacklisted_genres = ['attualita', 'scienza', 'religione', 'cucina', 'notiziario', 'altro', 'soap opera', 'viaggi',  'economia', 'tecnologia', 'magazine', 'show', 'reality show', 'lifestyle', 'societa', 'wrestling', 'azione', 'Musica', 'real life', 'real adventure', 'dplay original', 'natura', 'news', 'food', 'sport', 'moda', 'arte e cultura', 'crime', 'box set e serie tv', 'casa', 'storia', 'talk show', 'motori', 'attualit\xc3\xa0 e inchiesta', 'documentari', 'musica', 'spettacolo', 'medical', 'talent show', 'sex and love', 'beauty and style', 'news/current affairs', "children's/youth programmes", 'leisure hobbies', 'social/political issues/economics', 'education/science/factual topics', 'undefined content', 'show/game show', 'music/ballet/dance', 'sports', 'arts/culture', 'biografico', 'informazione', 'documentario']


def mainlist(item):
    support.log()

    itemlist = [Item(title=support.typo('Film in onda oggi', 'bold'), channel=item.channel, action='category', contentType='movie', thumbnail=support.thumb(thumb='movie.png')),
                Item(title=support.typo('Serie Tv in onda oggi', 'bold'), channel=item.channel, action='peliculas', contentType='tvshow', thumbnail=support.thumb(thumb='tvshow.png')),
                Item(title=support.typo('Guida tv per canale', 'bold'), channel=item.channel, action='listaCanali', thumbnail=support.thumb(thumb='on_the_air.png')),
                Item(title=support.typo('Canali live', 'bold'), channel=item.channel, action='live', thumbnail=support.thumb(thumb='tvshow_on_the_air.png'))]

    return itemlist


def getEpg():
    now = datetime.now()
    fileName = support.config.get_temp_file('guidatv-') + now.strftime('%Y %m %d')
    archiveName = fileName + '.gz'
    xmlName = fileName + '.xml'
    if not filetools.exists(archiveName):
        support.log('downloading epg')
        # cancello quelli vecchi
        for f in glob.glob(support.config.get_temp_file('guidatv-') + '*'):
            filetools.remove(f, silent=True)
        # inmemory = io.BytesIO(httptools.downloadpage(host).data)
        downloadtools.downloadfile(host, archiveName)
        support.log('opening gzip and writing xml')
        fStream = gzip.GzipFile(archiveName, mode='rb')
        guide = fStream.read().replace('\n', ' ').replace('><', '>\n<')
        with open(xmlName, 'w') as f:
            f.write(guide)
    # else:
    guide = open(xmlName)
    return guide


def category(item):
    itemlist = [Item(title="Tutti", all=True, channel=item.channel, action='peliculas', contentType=item.contentType)]
    category = ['Animazione', 'Avventura', 'Azione', 'Biografico', 'Brillante', 'Comico', 'Commedia', 'Crime', 'Documentario', 'Documentaristico', 'Drammatico', 'Famiglia', 'Fantascienza', 'Fantastico', 'Giallo', 'Guerra', 'Horror', 'Mistero', 'Musicale', 'Poliziesco', 'Sexy', 'Storico', 'Thriller', 'Western']

    for cat in category:
        itemlist.append(Item(title=cat, category=cat, channel=item.channel, action='peliculas', contentType=item.contentType))
    return support.thumb(itemlist)


def peliculas(item, f=None, ):
    f = getEpg()
    titles = [item.lastTitle] if not item.titles else item.titles
    itemlist = []
    pag = item.pag if item.pag else 0

    channel = ''
    title = ''
    episode = ''
    plot = ''
    thumbnail = ''
    actors = []
    director = ''
    year = ''
    genres = []
    genre = ''
    country = ''
    skip = False

    f.seek(pag)
    line = True
    while line:
        line = f.readline()
        if '<programme' in line:
            channel = scrapertools.find_single_match(line, r'channel="([^"]+)"')
        elif '<title' in line:
            title = scrapertools.find_single_match(line, r'>([^<]+?)(?: - (?:1\s*\^\s*TV|Prima\s*T[Vv]))?<')
            if not title or title in titles or title == 'EPG non disponibile':
                skip = True
        elif not skip and '<desc' in line:
            genre, episode, plot = scrapertools.find_single_match(line, r'>(?:\[([^\]]+)\])?(S[0-9]+\s*Ep?[0-9]+)?(?:\s*-\s*)?([^<]+)')
            if plot:
                CY = scrapertools.find_single_match(plot, r'(\D{3}) (\d{4})')
                if CY: country, year = CY
                director = scrapertools.find_single_match(plot, r'Regia di ([^;|<]+)')
            if episode and item.contentType == 'movie': skip = True
        elif not skip and '<category' in line:
            genre = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<actor' in line:
        #     match = scrapertools.find_single_match(line, r'(?:role="([^"]*)")?>([^<]+)<')
        #     actors.append([match[1], match[0]])
        # elif not skip and '<director' in line:
        #     director = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<date' in line:
        #     year = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<country' in line:
        #     country = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<episode-num' in line:
        #     episode = scrapertools.find_single_match(line, r'>([^<]+)<')
        #     if item.contentType == 'movie':
        #         skip = True
        # elif not skip and '<icon' in line:
        #     thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif '</programme' in line:
            if genre in blacklisted_genres: skip = True
            elif genre: genres = genre.split('/')
            if not skip:
                titles.append(title)
                if (item.contentType == 'movie' and genres and (item.category in genres or item.all == True)) or (item.contentType == 'tvshow' and episode):
                    if episode:
                        episode = scrapertools.get_season_and_episode(episode)
                        se, ep = episode.split('x')
                    else:
                        se, ep = ('', '')
                    itemlist.append(Item(
                        channel=item.channel,
                        action='new_search',
                        title=support.typo(title + (' - ' + episode if episode else ''), 'bold'),
                        contentTitle=title if item.contentType == 'movie' else '',
                        contentSerieName=title if item.contentType == 'tvshow' else '',
                        contentSeason=se,
                        contentEpisodeNumber=ep,
                        fulltitle=title,
                        search_text=title,
                        mode=item.contentType,
                        thumbnail=thumbnail if thumbnail else item.thumbnail,
                        contentType=item.contentType,
                        channel_name=channel,
                        plot=plot,
                        infoLabels={
                            'director': director,
                            'genre': genres,
                            'country': country,
                            'year': year,
                            'season': se,
                            'episode': ep
                        }
                    ))

            channel = ''
            title = ''
            episode = ''
            plot = ''
            thumbnail = ''
            actors = []
            director = ''
            year = ''
            genres = []
            genre = ''
            country = ''
            skip = False

            if len(itemlist) >= 40:
                itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), pag= f.tell(), thumbnail=support.thumb(), lastTitle=titles[-1]))
                break
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    f.close()
    return itemlist

def listaCanali(item):
    itemlist = []
    f = getEpg()
    thumbnail = None
    skip = False
    line = True
    while line:
        line = f.readline()
        if '<channel' in line:
            channelID = scrapertools.find_single_match(line, r'id="([^"]+)"')
        elif '<display-name' in line:
            channelName = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif not skip and '<icon' in line:
            thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif not skip and '<programme' in line:
            break
        if '</channel' in line:
            if not skip and thumbnail: #and 'channel="' + channel + '"' in f:
                itemlist.append(Item(
                    channel=item.channel,
                    action='guidatv',
                    title=support.typo(channelName, 'bold'),
                    channelID=channelID,
                    thumbnail=thumbnail
                ))
            thumbnail = None
            skip = False
    # return itemlist
    # logger.info([i.title for i in itemlist])
    f.close()
    return sorted(itemlist, key=lambda x: x.title)


def guidatv(item):
    itemlist = []
    f = getEpg()
    days = []
    for day in range(11, 18):days.append(xbmc.getLocalizedString(day))

    channel = ''
    title = ''
    episode = ''
    plot = ''
    thumbnail = ''
    actors = []
    director = ''
    year = ''
    genres = []
    country = ''
    start = ''
    stop = ''
    skip = False

    line = True
    while line:
        line = f.readline()
        if '<programme' in line:
            start, stop, channel = scrapertools.find_single_match(line,r'start="([^"]*)" stop="([^"]*)" channel="([^"]+)"')
            if channel != item.channelID:
                skip = True
        elif not skip and '<title' in line:
            title = scrapertools.find_single_match(line, r'>([^<]+?)<')
            if title == 'EPG non disponibile':
                skip = True
        elif not skip and '<desc' in line:
            genre, episode, plot = scrapertools.find_single_match(line, r'>(?:\[([^\]]+)\])?(S[0-9]+\s*Ep?[0-9]+)?(?:\s*-\s*)?([^<]+)')
            if plot:
                CY = scrapertools.find_single_match(plot, r'(\D{3}) (\d{4})')
                if CY: country, year = CY
                director = scrapertools.find_single_match(plot, r'Regia di ([^;|<]+)')
            if genre: genres.append(genre)
            if episode and item.contentType == 'movie':skip = True
        elif not skip and '<category' in line:
            genre = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<actor' in line:
        #     match = scrapertools.find_single_match(line, r'(?:role="([^"]*)")?>([^<]+)<')
        #     actors.append([match[1], match[0]])
        # elif not skip and '<director' in line:
        #     director = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<date' in line:
        #     year = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<category' in line:
        #     genres.append(scrapertools.find_single_match(line, r'>([^<]+)<'))
        # elif not skip and '<country' in line:
        #     country = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<episode-num' in line:
        #     episode = scrapertools.find_single_match(line, r'>([^<]+)<')
        # elif not skip and '<icon' in line:
        #     thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif '</programme' in line:
            if not skip:
                if genre: genres = genre.split('/')
                tzHour = int(start.split('+')[1][:2])
                start = time.strptime(start.split(' ')[0], '%Y%m%d%H%M%S')
                stop = time.strptime(stop.split(' ')[0], '%Y%m%d%H%M%S')
                duration = days[start.tm_wday] + ' alle ' + str(start.tm_hour + tzHour).zfill(2) + ':' + str(start.tm_min).zfill(2) + ' - ' + str(stop.tm_hour + tzHour).zfill(2) + ':' + str(stop.tm_min).zfill(2) + ' - '
                itemlist.append(Item(
                    channel=item.channel,
                    action='new_search',
                    title=duration + support.typo(title + (' - ' + episode if episode else ''), 'bold'),
                    fulltitle=title,
                    search_text=title,
                    mode=item.contentType,
                    thumbnail=thumbnail if thumbnail else item.thumbnail,
                    contentType=item.contentType,
                    channel_name=channel,
                    infoLabels={
                        'title': title,
                        'plot': plot,
                        'castandrole': actors,
                        'director': director,
                        'genre': genres,
                        'country': country,
                        'year': year
                    }
                ))

            channel = ''
            title = ''
            episode = ''
            plot = ''
            thumbnail = ''
            actors = []
            director = ''
            year = ''
            genres = []
            country = ''
            start = ''
            stop = ''
            skip = False
    f.close()
    return itemlist


def new_search(item):
    from specials import search
    item.channel = 'search'
    # se risultato certo, vai dritto alla ricerca per id
    if item.infoLabels['tmdb_id']:
        return search.channel_search(item)
    else:
        return search.new_search(item)


def live(item):
    itemlist = []
    from channels import raiplay#, mediasetplay
    itemlist += raiplay.live(raiplay.mainlist(Item())[0])
    # itemlist += mediasetplay.live(mediasetplay.mainlist(Item())[0])
    return itemlist
