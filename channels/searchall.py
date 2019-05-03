# -*- coding: utf-8 -*-

import Queue
import datetime
import glob
import os
import re
import threading
import time
import urllib
from threading import Thread
from unicodedata import normalize

import xbmc

from core import channeltools, httptools, tmdb, servertools
from lib.fuzzywuzzy import fuzz
from platformcode import platformtools

try:
    import json
except:
    import simplejson as json

from platformcode import config
from platformcode import logger
from core.item import Item

TMDB_KEY = tmdb.tmdb_auth_key  ######TMDB_KEY = '92db8778ccb39d825150332b0a46061d'
# TMDB_KEY = '92db8778ccb39d825150332b0a46061d'


TMDB_URL_BASE = 'http://api.themoviedb.org/3/'
TMDB_IMAGES_BASEURL = 'http://image.tmdb.org/t/p/'
INCLUDE_ADULT = True if config.get_setting("enableadultmode") else False
LANGUAGE_ID = 'it'

DTTIME = (datetime.datetime.utcnow() - datetime.timedelta(hours=5))
SYSTIME = DTTIME.strftime('%Y%m%d%H%M%S%f')
TODAY_TIME = DTTIME.strftime('%Y-%m-%d')
MONTH_TIME = (DTTIME - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
MONTH2_TIME = (DTTIME - datetime.timedelta(days=60)).strftime('%Y-%m-%d')
YEAR_DATE = (DTTIME - datetime.timedelta(days=365)).strftime('%Y-%m-%d')

TIMEOUT_TOTAL = config.get_setting("timeout")
MAX_THREADS = config.get_setting("maxthreads")

# TIMEOUT_TOTAL = config.get_setting("timeout", default=90)
# MAX_THREADS = config.get_setting("maxthreads", default=24)

NLS_Search_by_Channel = config.get_localized_string(30974)
NLS_Alternative_Search = config.get_localized_string(70021)
NLS_Search_by_Title = config.get_localized_string(30980)
NLS_Search_by_Person = config.get_localized_string(30981)
NLS_Search_by_Company = config.get_localized_string(30982)
NLS_Now_Playing = config.get_localized_string(30983)
NLS_Popular = config.get_localized_string(30984)
NLS_Top_Rated = config.get_localized_string(30985)
NLS_Search_by_Collection = config.get_localized_string(30986)
NLS_List_by_Genre = config.get_localized_string(30987)
NLS_Search_by_Year = config.get_localized_string(30988)
NLS_Search_Similar_by_Title = config.get_localized_string(30989)
NLS_Search_Tvshow_by_Title = config.get_localized_string(30990)
NLS_Most_Voted = config.get_localized_string(30996)
NLS_Oscar = config.get_localized_string(30997)
NLS_Last_2_months = config.get_localized_string(60534)
NLS_Library = config.get_localized_string(30991)
NLS_Next_Page = config.get_localized_string(30992)
NLS_Looking_For = config.get_localized_string(30993)
NLS_Searching_In = config.get_localized_string(30994)
NLS_Found_So_Far = config.get_localized_string(30995)
NLS_Info_Title = config.get_localized_string(30975)
NLS_Info_Person = config.get_localized_string(30979)
NLS_New_TVShow = config.get_localized_string(30978)
NLS_TVShow_onair = config.get_localized_string(30977)
NLS_TVShow_airing_today = config.get_localized_string(30976)

TMDb_genres = {}


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel="search",
                     title="[COLOR lightgreen]%s[/COLOR]" % NLS_Search_by_Channel,
                     action="mainlist",
                     thumbnail="http://i.imgur.com/pE5WSZp.png"),
                Item(channel="tvmoviedb",
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Alternative_Search,
                     action="mainlist",
                     url="search_movie_by_title",
                     thumbnail="https://s6.postimg.cc/6lll9b8c1/searching.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Search_by_Title,
                     action="search",
                     url="search_movie_by_title",
                     thumbnail="http://i.imgur.com/B1H1G8U.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Search_by_Person,
                     action="search",
                     url="search_person_by_name",
                     thumbnail="http://i.imgur.com/efuEeNu.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Search_by_Year,
                     action="search_movie_by_year",
                     url="search_movie_by_year",
                     thumbnail="https://d1kz0yd1invg7i.cloudfront.net/uploads/app/icon/1/calendar-icon-big.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Search_by_Collection,
                     action="search",
                     url="search_collection_by_name",
                     thumbnail="http://i.imgur.com/JmcvZDL.png"),
                Item(channel=item.channel,
                     title="[COLOR yellow]%s[/COLOR]" % NLS_Search_Similar_by_Title,
                     action="search",
                     url="search_similar_movie_by_title",
                     thumbnail="http://i.imgur.com/JmcvZDL.png"),
                Item(channel=item.channel,
                     title="[COLOR lime]%s[/COLOR]" % NLS_Search_Tvshow_by_Title,
                     action="search",
                     url="search_tvshow_by_title",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(TV Shows) [COLOR lime]%s[/COLOR]" % NLS_New_TVShow,
                     action="list_tvshow",
                     url='discover/tv?sort_by=popularity.desc&first_air_date.gte=%s&first_air_date.lte=%s&' % (
                         MONTH2_TIME, TODAY_TIME),
                     plot="1",
                     type="tvshow",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(TV Shows) [COLOR lime]%s[/COLOR]" % NLS_TVShow_onair,
                     action="list_tvshow",
                     url="tv/on_the_air?",
                     plot="1",
                     type="tvshow",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(TV Shows) [COLOR lime]%s[/COLOR]" % NLS_Popular,
                     action="list_tvshow",
                     url="tv/popular?",
                     plot="1",
                     type="tvshow",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(TV Shows) [COLOR lime]%s[/COLOR]" % NLS_Top_Rated,
                     action="list_tvshow",
                     url="tv/top_rated?",
                     plot="1",
                     type="tvshow",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(TV Shows) [COLOR lime]%s[/COLOR]" % NLS_TVShow_airing_today,
                     action="list_tvshow",
                     url="tv/airing_today?",
                     plot="1",
                     type="tvshow",
                     thumbnail="https://i.imgur.com/2ZWjLn5.jpg?1"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Now_Playing,
                     action="list_movie",
                     url="movie/now_playing?",
                     plot="1",
                     type="movie",
                     thumbnail="http://i.imgur.com/B16HnVh.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Popular,
                     action="list_movie",
                     url="movie/popular?",
                     plot="1",
                     type="movie",
                     thumbnail="http://i.imgur.com/8IBjyzw.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Top_Rated,
                     action="list_movie",
                     url="movie/top_rated?",
                     plot="1",
                     type="movie",
                     thumbnail="http://www.clipartbest.com/cliparts/RiG/6qn/RiG6qn79T.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Most_Voted,
                     action="list_movie",
                     url='discover/movie?certification_country=US&sort_by=vote_count.desc&',
                     plot="1",
                     type="movie",
                     thumbnail="http://i.imgur.com/5ShnO8w.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Oscar,
                     action="list_movie",
                     url='list/509ec17b19c2950a0600050d?',
                     plot="1",
                     type="movie",
                     thumbnail="http://i.imgur.com/5ShnO8w.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_Last_2_months,
                     action="list_movie",
                     url='discover/movie?primary_release_date.gte=%s&primary_release_date.lte=%s&' % (
                         YEAR_DATE, MONTH2_TIME),
                     plot="1",
                     type="movie",
                     thumbnail="http://i.imgur.com/CsizqUI.png"),
                Item(channel=item.channel,
                     title="(Movies) [COLOR yellow]%s[/COLOR]" % NLS_List_by_Genre,
                     action="list_genres",
                     type="movie",
                     thumbnail="http://i.imgur.com/uotyBbU.png")]

    return itemlist


def list_movie(item):
    logger.info(" list_movie '%s/%s'" % (item.url, item.plot))

    results = [0, 0]
    page = int(item.plot)
    itemlist = build_movie_list(item, tmdb_get_data('%s&page=%d&' % (item.url, page), results=results))
    if page < results[0]:
        itemlist.append(Item(
            channel=item.channel,
            title="[COLOR orange]%s (%d/%d)[/COLOR]" % (NLS_Next_Page, page * len(itemlist), results[1]),
            action="list_movie",
            url=item.url,
            plot="%d" % (page + 1),
            type=item.type,
            viewmode="" if page <= 1 else "paged_list"))

    return itemlist


def list_tvshow(item):
    logger.info(" list_tvshow '%s/%s'" % (item.url, item.plot))

    results = [0, 0]
    page = int(item.plot)
    itemlist = build_movie_list(item, tmdb_get_data('%spage=%d&' % (item.url, page), results=results))
    if page < results[0]:
        itemlist.append(Item(
            channel=item.channel,
            title="[COLOR orange]%s (%d/%d)[/COLOR]" % (NLS_Next_Page, page * len(itemlist), results[1]),
            action="list_tvshow",
            url=item.url,
            plot="%d" % (page + 1),
            type=item.type,
            viewmode="" if page <= 1 else "paged_list"))

    return itemlist


def list_genres(item):
    logger.info(" list_genres")

    tmdb_genre(1)
    itemlist = []
    for genre_id, genre_name in TMDb_genres.iteritems():
        itemlist.append(
            Item(channel=item.channel,
                 title=genre_name,
                 action="list_movie",
                 url='genre/%d/movies?primary_release_date.gte=%s&primary_release_date.lte=%s&language=it' % (
                     genre_id, YEAR_DATE, TODAY_TIME),
                 plot="1"))

    return itemlist


def discover_list(item):
    from platformcode import unify
    from core import scrapertools
    itemlist = []

    result = tmdb.discovery(item)

    tvshow = False

    logger.debug(item)

    for elem in result:
        elem['tmdb_id'] = elem['id']
        if 'title' in elem:
            title = unify.normalize(elem['title']).capitalize()
            elem['year'] = scrapertools.find_single_match(elem['release_date'], '(\d{4})-\d+-\d+')
        else:
            title = unify.normalize(elem['name']).capitalize()
            tvshow = True

        new_item = Item(channel='searchall', title=title, infoLabels=elem, action='search_tmdb', extra=title,
                        category=config.get_localized_string(70695), context='')

        if tvshow:
            new_item.contentSerieName = title
        else:
            new_item.contentTitle = title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if item.page != '' and len(itemlist) > 0:
        next_page = str(int(item.page) + 1)
        # if not 'similar' in item.list_type:
        #    itemlist.append(item.clone(title='Pagina Siguente', page=next_page))
        # else:
        itemlist.append(Item(channel=item.channel, action='discover_list', title=config.get_localized_string(30992),
                             text_color="orange", search_type=item.search_type, list_type=item.list_type,
                             type=item.type, page=next_page))

    return itemlist


# Do not change the name of this function otherwise launcher.py won't create the keyboard dialog required to enter the search terms
def search(item, search_terms):
    if item.url == '': return []

    return globals()[item.url](item, search_terms) if item.url in globals() else []


def search_tvshow_by_title(item, search_terms):
    logger.info(" search_tvshow_by_title '%s'" % (search_terms))

    return list_movie(
        Item(channel=item.channel,
             url='search/tv?query=%s&' % search_terms,
             plot="1",
             type="tvshow"))


def search_movie_by_title(item, search_terms):
    logger.info(" search_movie_by_title '%s'" % (search_terms))

    return list_movie(
        Item(channel=item.channel,
             url='search/movie?query=%s&' % search_terms,
             plot="1",
             type="movie"))


def search_similar_movie_by_title(item, search_terms):
    logger.info(" search_similar_movie_by_title '%s'" % (search_terms))

    return list_movie(
        Item(channel=item.channel,
             url='search/movie?append_to_response=similar_movies,alternative_title&query=%s&' % search_terms,
             plot="1",
             type='movie'))


def search_movie_by_year(item):
    logger.info(" search_movie_by_year")
    now = datetime.datetime.now()
    year = int(now.year)
    result = []
    for i in range(150):
        year_to_search = year - i
        result.append(Item(channel=item.channel,
                           url='discover/movie?primary_release_year=%s&' % year_to_search,
                           plot="1",
                           type="movie",
                           title="%s" % year_to_search,
                           action="list_movie"))
    return result


def search_person_by_name(item, search_terms):
    logger.info(" search_person_by_name '%s'" % (search_terms))

    persons = tmdb_get_data("search/person?query=%s&" % search_terms)

    itemlist = []
    for person in persons:
        name = normalize_unicode(tmdb_tag(person, 'name'))
        poster = tmdb_image(person, 'profile_path')
        fanart = ''
        for movie in tmdb_tag(person, 'known_for', []):
            if tmdb_tag_exists(movie, 'backdrop_path'):
                fanart = tmdb_image(movie, 'backdrop_path', 'w1280')
                break

        # extracmds = [
        #     (NLS_Info_Person, "RunScript(script.extendedinfo,info=extendedactorinfo,id=%s)" % str(tmdb_tag(person, 'id')))] \
        #     if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)') else []

        itemlist.append(Item(
            channel=item.channel,
            action='search_movie_by_person',
            extra=str(tmdb_tag(person, 'id')),
            title=name,
            thumbnail=poster,
            viewmode='list',
            fanart=fanart,
            type='movie'
            # extracmds=extracmds
        ))

    return itemlist


def search_movie_by_person(item):
    logger.info(" search_movie_by_person '%s'" % (item.extra))

    # return list_movie(
    #     Item(channel=item.channel,
    #          url="discover/movie?with_people=%s&primary_release_date.lte=%s&sort_by=primary_release_date.desc&" % (
    #              item.extra, TODAY_TIME),
    #          plot="1"))

    person_movie_credits = tmdb_get_data(
        "person/%s/movie_credits?primary_release_date.lte=%s&sort_by=primary_release_date.desc&" % (
            item.extra, TODAY_TIME))
    movies = []
    if person_movie_credits:
        movies.extend(tmdb_tag(person_movie_credits, 'cast', []))
        movies.extend(tmdb_tag(person_movie_credits, 'crew', []))

    # Movie person list is not paged
    return build_movie_list(item, movies)


def search_collection_by_name(item, search_terms):
    logger.info(" search_collection_by_name '%s'" % (search_terms))

    collections = tmdb_get_data("search/collection?query=%s&" % search_terms)

    itemlist = []
    for collection in collections:
        name = normalize_unicode(tmdb_tag(collection, 'name'))
        poster = tmdb_image(collection, 'poster_path')
        fanart = tmdb_image(collection, 'backdrop_path', 'w1280')

        itemlist.append(Item(
            channel=item.channel,
            action='search_movie_by_collection',
            extra=str(tmdb_tag(collection, 'id')),
            title=name,
            thumbnail=poster,
            viewmode='list',
            fanart=fanart,
            type='movie'
        ))

    return itemlist


def search_movie_by_collection(item):
    logger.info(" search_movie_by_collection '%s'" % (item.extra))

    collection = tmdb_get_data("collection/%s?" % item.extra)

    # Movie collection list is not paged
    return build_movie_list(item, collection['parts']) if 'parts' in collection else []


def build_movie_list(item, movies):
    if movies is None: return []

    itemlist = []
    for movie in movies:
        t = tmdb_tag(movie, 'title')
        if t == '':
            t = re.sub('\s(|[(])(UK|US|AU|\d{4})(|[)])$', '', tmdb_tag(movie, 'name'))
        title = normalize_unicode(t)
        title_search = normalize_unicode(t, encoding='ascii')
        if not all(ord(char) < 128 for char in title): continue
        poster = tmdb_image(movie, 'poster_path')
        fanart = tmdb_image(movie, 'backdrop_path', 'w1280')
        jobrole = normalize_unicode(
            ' [COLOR yellow][' + tmdb_tag(movie, 'job') + '][/COLOR]' if tmdb_tag_exists(movie, 'job') else '')
        genres = normalize_unicode(
            ' / '.join([tmdb_genre(genre).upper() for genre in tmdb_tag(movie, 'genre_ids', [])]))
        year = tmdb_tag(movie, 'release_date')[0:4] if tmdb_tag_exists(movie, 'release_date') else ''
        plot = normalize_unicode(tmdb_tag(movie, 'overview'))
        rating = tmdb_tag(movie, 'vote_average')
        votes = tmdb_tag(movie, 'vote_count')

        extrameta = {'plot': plot}
        if year != "": extrameta["Year"] = year
        if genres != "": extrameta["Genre"] = genres
        if votes:
            extrameta["Rating"] = rating
            extrameta["Votes"] = "%d" % votes

        # extracmds = [(NLS_Info_Title, "RunScript(script.extendedinfo,info=extendedinfo,id=%s)" % str(tmdb_tag(movie, 'id')))] \
        #     if xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)') else [('Movie/Show Info', 'XBMC.Action(Info)')]

        found = False
        kodi_db_movies = kodi_database_movies(title)
        for kodi_db_movie in kodi_db_movies:
            logger.info('Kod.database set for local playing(%s):\n%s' % (title, str(kodi_db_movie)))
            if year == str(kodi_db_movie["year"]):
                found = True

                # If some, less relevant, keys are missing locally
                # try to get them through TMDB anyway.
                try:
                    poster = kodi_db_movie["art"]["poster"]
                    fanart = kodi_db_movie["art"]["fanart"]
                except KeyError:
                    poster = poster
                    fanart = fanart

                itemlist.append(Item(
                    channel=item.channel,
                    action='play',
                    url=kodi_db_movie["file"],
                    title='[COLOR orange][%s][/COLOR] ' % NLS_Library + kodi_db_movie["title"] + jobrole,
                    thumbnail=poster,
                    category=genres,
                    plot=plot,
                    viewmode='movie_with_plot',
                    fanart=fanart,
                    infoLabels=extrameta,
                    folder=False,
                ))

        if not found:
            logger.info('Kod.database set for channels search(%s)' % title)
            itemlist.append(Item(
                channel=item.channel,
                action='do_channels_search',
                extra=url_quote_plus(title_search) + '{}' + item.type + '{}' + year,
                title=title + jobrole,
                thumbnail=poster,
                category=genres,
                plot=plot,
                viewmode='movie_with_plot',
                fanart=fanart,
                infoLabels=extrameta,
            ))

    return itemlist


def normalize_unicode(string, encoding='utf-8'):
    if string is None: string = ''
    return normalize('NFKD', string if isinstance(string, unicode) else unicode(string, encoding, 'ignore')).encode(
        encoding, 'ignore')


def tmdb_get_data(url="", results=[0, 0], language=True):
    url = TMDB_URL_BASE + "%sinclude_adult=%s&api_key=%s" % (url, INCLUDE_ADULT, TMDB_KEY)
    # Temporary fix until tmdb fixes the issue with getting the genres by language!
    if language: url += "&language=%s" % LANGUAGE_ID
    response = get_json_response(url)
    results[0] = response['total_pages'] if 'total_pages' in response else 0
    results[1] = response['total_results'] if 'total_results' in response else 0

    if response:
        if "results" in response:
            return response["results"]
        elif "items" in response:
            return response["items"]
        elif "tv_credits" in response:
            return response["tv_credits"]["cast"]
        else:
            return response


def tmdb_tag_exists(entry, tag):
    return isinstance(entry, dict) and tag in entry and entry[tag] is not None


def tmdb_tag(entry, tag, default=""):
    return entry[tag] if isinstance(entry, dict) and tag in entry else default


def tmdb_image(entry, tag, width='original'):
    return TMDB_IMAGES_BASEURL + width + '/' + tmdb_tag(entry, tag) if tmdb_tag_exists(entry, tag) else ''


def tmdb_genre(id):
    if id not in TMDb_genres:
        genres = tmdb_get_data("genre/list?", language="it")
        for genre in tmdb_tag(genres, 'genres', []):
            TMDb_genres[tmdb_tag(genre, 'id')] = tmdb_tag(genre, 'name')

    return TMDb_genres[id] if id in TMDb_genres and TMDb_genres[id] != None else str(id)


def kodi_database_movies(title):
    json_query = \
        '{"jsonrpc": "2.0",\
            "params": {\
               "sort": {"order": "ascending", "method": "title"},\
               "filter": {"operator": "is", "field": "title", "value": "%s"},\
               "properties": ["title", "art", "file", "year"]\
            },\
            "method": "VideoLibrary.GetMovies",\
            "id": "libMovies"\
        }' % title
    response = get_xbmc_jsonrpc_response(json_query)
    return response["result"]["movies"] if response and "result" in response and "movies" in response["result"] else []


def get_xbmc_jsonrpc_response(json_query=""):
    try:
        response = xbmc.executeJSONRPC(json_query)
        response = unicode(response, 'utf-8', errors='ignore')
        response = json.loads(response)
        logger.info(" jsonrpc %s" % response)
    except Exception, e:
        logger.info(" jsonrpc error: %s" % str(e))
        response = None
    return response


def url_quote_plus(input_string):
    try:
        return urllib.quote_plus(input_string.encode('utf8', 'ignore'))
    except:
        return urllib.quote_plus(unicode(input_string, "utf-8").encode("utf-8"))


def get_json_response(url=""):
    response = httptools.downloadpage(url).data
    try:
        results = json.loads(response)
    except:
        logger.info(" Exception: Could not get new JSON data from %s" % url)
        results = []
    return results


def channel_search(queue, channel_parameters, category, title_year, tecleado):
    try:
        search_results = []

        title_search = urllib.unquote_plus(tecleado)

        exec "from channels import " + channel_parameters["channel"] + " as module"
        mainlist = module.mainlist(Item(channel=channel_parameters["channel"]))

        for item in mainlist:
            if item.action != "search" or category and item.extra != category:
                continue

            for res_item in module.search(item.clone(), tecleado):
                title = res_item.fulltitle

                # If the release year is known, check if it matches the year found in the title
                if title_year > 0:
                    year_match = re.search('\(.*(\d{4}).*\)', title)
                    if year_match and abs(int(year_match.group(1)) - title_year) > 1:
                        continue

                # Clean up a bit the returned title to improve the fuzzy matching
                title = re.sub(r'\(.*\)', '', title)  # Anything within ()
                title = re.sub(r'\[.*\]', '', title)  # Anything within []

                # Check if the found title fuzzy matches the searched one
                if fuzz.token_sort_ratio(title_search, title) > 85:
                    res_item.title = "[COLOR azure]" + res_item.title + "[/COLOR][COLOR orange] su [/COLOR][COLOR green]" + \
                                     channel_parameters["title"] + "[/COLOR]"
                    search_results.append(res_item)

        queue.put(search_results)

    except:
        logger.error("No se puede buscar en: " + channel_parameters["title"])
        import traceback
        logger.error(traceback.format_exc())


def do_channels_search(item):
    logger.info(" do_channels_search")

    tecleado, category, title_year = item.extra.split('{}')

    try:
        title_year = int(title_year)
    except:
        title_year = 0

    itemlist = []

    channels_path = os.path.join(config.get_runtime_path(), "channels", '*.json')
    logger.info(" channels_path=" + channels_path)

    # channel_language = config.get_setting("channel_language")
    channel_language = auto_filter()
    logger.info(" channel_language=" + channel_language)
    if channel_language == "":
        channel_language = "all"
        logger.info(" channel_language=" + channel_language)

    progreso = platformtools.dialog_progress_bg(NLS_Looking_For % urllib.unquote_plus(tecleado))

    channel_files = sorted(glob.glob(channels_path))

    search_results = Queue.Queue()
    completed_channels = 0
    number_of_channels = 0

    start_time = int(time.time())

    for infile in channel_files:

        basename_without_extension = os.path.basename(infile)[:-5]

        channel_parameters = channeltools.get_channel_parameters(basename_without_extension)

        # No busca si es un canal inactivo
        if channel_parameters["active"] != True:
            continue

        # En caso de busqueda por categorias
        if category and category not in channel_parameters["categories"]:
            continue

        # No busca si el canal es en un idioma filtrado
        if channel_language != "all" and channel_parameters["language"] != channel_language:
            continue

        # No busca si es un canal excluido de la busqueda global
        include_in_global_search = channel_parameters["include_in_global_search"]
        if include_in_global_search == True:
            # Buscar en la configuracion del canal
            include_in_global_search = config.get_setting("include_in_global_search", basename_without_extension)
        if include_in_global_search == False:
            continue

        t = Thread(target=channel_search, args=[search_results, channel_parameters, category, title_year, tecleado])
        t.setDaemon(True)
        t.start()
        number_of_channels += 1

        while threading.active_count() >= MAX_THREADS:

            delta_time = int(time.time()) - start_time
            if len(itemlist) <= 0:
                timeout = None  # No result so far,lets the thread to continue working until a result is returned
            elif delta_time >= TIMEOUT_TOTAL:
                progreso.close()
                itemlist = sorted(itemlist, key=lambda item: item.fulltitle)
                return itemlist
            else:
                timeout = TIMEOUT_TOTAL - delta_time  # Still time to gather other results

            progreso.update(completed_channels * 100 / number_of_channels)

            try:
                itemlist.extend(search_results.get(timeout=timeout))
                completed_channels += 1
            except:
                progreso.close()
                itemlist = sorted(itemlist, key=lambda item: item.fulltitle)
                return itemlist

    while completed_channels < number_of_channels:

        delta_time = int(time.time()) - start_time
        if len(itemlist) <= 0:
            timeout = None  # No result so far,lets the thread to continue working until a result is returned
        elif delta_time >= TIMEOUT_TOTAL:
            break  # At least a result matching the searched title has been found, lets stop the search
        else:
            timeout = TIMEOUT_TOTAL - delta_time  # Still time to gather other results

        progreso.update(completed_channels * 100 / number_of_channels)

        try:
            itemlist.extend(search_results.get(timeout=timeout))
            completed_channels += 1
        except:
            # Expired timeout raise an exception
            break

    progreso.close()

    # todo 1 : impostare una visualizzazione % di avanzamento (serve?)
    # todo 2 : verificare la formattazione dei titoli estratti
    # todo 3 : gestione numero threads e timeout
    if config.get_setting("findlinks") == True and "{}movie{}" in item.extra:
        itemlist = links_list(itemlist)
        itemlist = sorted(itemlist, key=lambda item: item.title.lower())
    else:
        itemlist = sorted(itemlist, key=lambda item: item.fulltitle)

    return itemlist


def links_list(itemlist):
    logger.info(" links_list")
    itemlistresults = []
    itemlistlist = []
    allthreads = []
    global_search_results = Queue.Queue()

    # create and collect threads
    for item in itemlist:
        t = Thread(target=list_single_site, args=[global_search_results, item])
        t.setDaemon(True)
        allthreads.append(t)

    # start threads
    for thread in allthreads:
        try:
            thread.start()
        except:
            logger.error("thread error !")

    # join threads, to wait all threads end before going on
    for thread in allthreads:
        thread.join()

    # collect results
    while not global_search_results.empty():
        for item in global_search_results.get():
            if not item_url_in_itemlist(item, itemlistresults):
                channelformatteditem = rewrite_item_title(item)
                if channelformatteditem is not None:
                    itemlistresults.append(channelformatteditem)

    return itemlistresults


def list_single_site(queue, item):
    logger.info(" list_single_site")
    channelitemlist = []
    try:
        # logger.info(item.channel + " start channel search " + time.strftime("%Y-%m-%d %H:%M:%S"))
        module_to_call = getattr(__import__("channels"), item.channel)
        channelitemlist = module_to_call.findvideos(item)
        queue.put(channelitemlist)
        # logger.info(item.channel + " end channel search " + time.strftime("%Y-%m-%d %H:%M:%S"))
    except:
        try:
            # logger.info(item.channel + " start servertools search " + time.strftime("%Y-%m-%d %H:%M:%S"))
            # logger.info("no findvideos defined in channel functions, calling servertools.findvideos to find links")
            servertools_itemlist = []
            headers = [['Referer', item.channel]]
            data = httptools.downloadpage(item.url, headers=headers).data
            list_servertools = servertools.findvideos(data)
            for item_servertools in list_servertools:
                servertools_itemlist.append(Item(channel=item.channel,
                                                 action="play",
                                                 fulltitle=item.title,
                                                 server=item_servertools[0],
                                                 thumbnail=item_servertools[3],
                                                 title=item.title,
                                                 url=item_servertools[1]))
            queue.put(servertools_itemlist)
            # logger.info(item.channel + " end servertools search " + time.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception, e:
            logger.error('exception in list_single_site: ' + str(e))
    return channelitemlist


# utility function
def item_url_in_itemlist(item, itemlist):
    logger.info(" item_url_in_itemlist")
    i = 0
    while i < len(itemlist):
        if itemlist[i].url == item.url:
            # logger.info("elemento eliminato : " + item.url)
            return True
        i = i + 1
    return False


# utility function, optional
def rewrite_item_title(item):
    logger.info(" rewrite_item_title")
    if "download" not in item.title.lower():
        item.title = "[COLOR yellow][%s][/COLOR][COLOR orange][%s][/COLOR] %s" % (
            item.server, item.channel, item.fulltitle)
    else:
        return None
    return item
