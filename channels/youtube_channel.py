# -*- coding: utf-8 -*-

try:
    import urllib.parse as urllib
except ImportError:
    import urllib

from core import jsontools, httptools
from core.item import Item
from platformcode import logger

CHANNELNAME = "youtube_channel"
YOUTUBE_V3_API_KEY = "AIzaSyCjsmBT0JZy1RT-PLwB-Zkfba87sa2inyI"


def youtube_api_call(method, parameters):
    logger.debug("method=" + method + ", parameters=" + repr(parameters))

    encoded_parameters = urllib.urlencode(parameters)

    url = "https://www.googleapis.com/youtube/v3/" + method + "?" + encoded_parameters + "&key=" + YOUTUBE_V3_API_KEY;
    logger.debug("url=" + url)

    data = httptools.downloadpage(url).data
    logger.debug("data=" + data)

    json_object = jsontools.load(data)

    return json_object


def youtube_get_user_playlists(user_id, pageToken=""):
    # Primero averigua el channel_id a partir del nombre del usuario
    json_object = youtube_api_call("channels", {"part": "id", "forUsername": user_id})
    channel_id = json_object["items"][0]["id"]

    # Ahora obtiene la lista de playlists del usuario
    json_object = youtube_api_call("playlists",
                                   {"part": "snippet,contentDetails", "channelId": channel_id, "maxResults": 50,
                                    "pageToken": pageToken})

    return json_object


def youtube_get_playlist_items(playlist_id, pageToken=""):
    json_object = youtube_api_call("playlistItems", {"part": "snippet", "playlistId": playlist_id, "maxResults": 50,
                                                     "pageToken": pageToken})

    return json_object


# Show all YouTube playlists for the selected channel
def playlists(item, channel_id, pageToken=""):
    logger.debug()
    itemlist = []

    json_object = youtube_get_user_playlists(channel_id, pageToken)

    for entry in json_object["items"]:
        logger.debug("entry=" + repr(entry))

        title = entry["snippet"]["title"]
        plot = entry["snippet"]["description"]
        thumbnail = entry["snippet"]["thumbnails"]["high"]["url"]
        url = entry["id"]

        # Appends a new item to the xbmc item list
        itemlist.append(Item(channel=CHANNELNAME, title=title, action="videos", url=url, thumbnail=thumbnail, plot=plot,
                             folder=True))

    try:
        nextPageToken = json_object["nextPageToken"]
        itemlist.extend(playlists(item, channel_id, nextPageToken))
    except:
        import traceback
        logger.error(traceback.format_exc())

    return itemlist


def latest_videos(item, channel_id):
    item.url = "http://gdata.youtube.com/feeds/api/users/" + channel_id + "/uploads?v=2&start-index=1&max-results=30"
    return videos(item)


# Show all YouTube videos for the selected playlist
def videos(item, pageToken=""):
    logger.debug()
    itemlist = []

    json_object = youtube_get_playlist_items(item.url, pageToken)

    for entry in json_object["items"]:
        logger.debug("entry=" + repr(entry))

        title = entry["snippet"]["title"]
        plot = entry["snippet"]["description"]
        thumbnail = entry["snippet"]["thumbnails"]["high"]["url"]
        url = entry["snippet"]["resourceId"]["videoId"]

        # Appends a new item to the xbmc item list
        itemlist.append(
            Item(channel=CHANNELNAME, title=title, action="play", server="youtube", url=url, thumbnail=thumbnail,
                 plot=plot, folder=False))

    try:
        nextPageToken = json_object["nextPageToken"]
        itemlist.extend(videos(item, nextPageToken))
    except:
        import traceback
        logger.error(traceback.format_exc())

    return itemlist


# Verificación automática de canales: Esta función debe devolver "True" si todo está ok en el canal.
def test(channel_id="TelevisionCanaria"):
    # Si hay algún video en alguna de las listas de reproducción lo da por bueno
    playlist_items = playlists(Item(), channel_id)
    for playlist_item in playlist_items:
        items_videos = videos(playlist_item)
        if len(items_videos) > 0:
            return True

    return False
