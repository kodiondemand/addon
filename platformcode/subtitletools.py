# -*- coding: utf-8 -*-

from __future__ import print_function
#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # It is very slow in PY2. In PY3 it is native
else:
    import urllib                                               # We use the native of PY2 which is faster

import os
import re
import string

from unicodedata import normalize
from core import filetools, httptools, jsontools, scrapertools

import xbmc
import xbmcgui
from platformcode import config, logger

if PY3: allchars = str.maketrans('', '')
if not PY3: allchars = string.maketrans('', '')
deletechars = ',\\/:*"<>|?'


# We extract the name of the series, season and chapter number example: 'fringe 1x01'
def regex_tvshow(compare, file, sub=""):
    regex_expressions = [r'[Ss]([0-9]+)[][._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                         r'[\._ \-]([0-9]+)x([0-9]+)([^\\/]*)',  # foo.1x09 
                         r'[\._ \-]([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',  # foo.109
                         r'([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                         r'[\\\\/\\._ -]([0-9]+)([0-9][0-9])[^\\/]*',
                         r'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',
                         r'Season ([0-9]+) Episode ([0-9]+)[^\\/]*',
                         r'[\\\\/\\._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
                         r'[[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',  # foo_[s01]_[e01]
                         r'[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',  # foo, s01e01, foo.s01.e01, foo.s01-e01
                         r's([0-9]+)ep([0-9]+)[^\\/]*',  # foo - s01ep03, foo - s1ep03
                         r'[Ss]([0-9]+)[][ ._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                         r'[\\\\/\\._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\\/]*)$',
                         r'[\\\\/\\._ \\[\\(-]([0-9]+)X([0-9]+)([^\\\\/]*)$'
                         ]
    sub_info = ""
    tvshow = 0

    for regex in regex_expressions:
        response_file = re.findall(regex, file)
        if len(response_file) > 0:
            print("Regex File Se: %s, Ep: %s," % (str(response_file[0][0]), str(response_file[0][1]),))
            tvshow = 1
            if not compare:
                title = re.split(regex, file)[0]
                for char in ['[', ']', '_', '(', ')', '.', '-']:
                    title = title.replace(char, ' ')
                if title.endswith(" "): title = title.strip()
                print("title: %s" % title)
                return title, response_file[0][0], response_file[0][1]
            else:
                break

    if (tvshow == 1):
        for regex in regex_expressions:
            response_sub = re.findall(regex, sub)
            if len(response_sub) > 0:
                try:
                    sub_info = "Regex Subtitle Ep: %s," % (str(response_sub[0][1]),)
                    if (int(response_sub[0][1]) == int(response_file[0][1])):
                        return True
                except:
                    pass
        return False
    if compare:
        return True
    else:
        return "", "", ""

        # Gets the name of the movie or episode of the series previously saved in plugin settings and then searches for it in the subtitles directory, if it finds them, activates them.


def set_Subtitle():
    logger.debug()

    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass"]
    subtitle_folder_path = filetools.join(config.get_data_path(), "subtitles")

    subtitle_type = config.get_setting("subtitle_type")

    if subtitle_type == "2":
        subtitle_path = config.get_setting("subtitlepath_file")
        logger.info("Con subtitulo : " + subtitle_path)
        xbmc.Player().setSubtitles(subtitle_path)
    else:
        if subtitle_type == "0":
            subtitle_path = config.get_setting("subtitlepath_folder")
            if subtitle_path == "":
                subtitle_path = subtitle_folder_path
                config.set_setting("subtitlepath_folder", subtitle_path)
        else:
            subtitle_path = config.get_setting("subtitlepath_keyboard")
            long_v = len(subtitle_path)
            if long_v > 0:
                if subtitle_path.startswith("http") or subtitle_path[long_v - 4, long] in exts:
                    logger.info("Con subtitulo : " + subtitle_path)
                    xbmc.Player().setSubtitles(subtitle_path)
                    return
            else:
                subtitle_path = subtitle_folder_path
                config.set_setting("subtitlepath_keyboard", subtitle_path)

        import glob

        subtitle_name = config.get_setting("subtitle_name").replace("amp;", "")
        tvshow_title, season, episode = regex_tvshow(False, subtitle_name)
        try:
            if episode != "":
                Subnames = glob.glob(filetools.join(subtitle_path, "Tvshows", tvshow_title,
                                                  "%s %sx%s" % (tvshow_title, season, episode) + "*.??.???"))
            else:
                Subnames = glob.glob(filetools.join(subtitle_path, "Movies", subtitle_name + "*.??.???"))
            for Subname in Subnames:
                if os.path.splitext(Subname)[1] in exts:
                    logger.info("Con subtitulo : " + filetools.split(Subname)[1])
                    xbmc.Player().setSubtitles((Subname))
        except:
            logger.error("error al cargar subtitulos")

            # Clean unicode characters


def _normalize(title, charset='utf-8'):
    '''Removes all accents and illegal chars for titles from the String'''
    if isinstance(title, unicode):
        title = string.translate(title, allchars, deletechars)
        try:
            title = title.encode("utf-8")
            title = normalize('NFKD', title).encode('ASCII', 'ignore')
        except UnicodeEncodeError:
            logger.error("Error de encoding")
    else:
        title = string.translate(title, allchars, deletechars)
        try:
            # iso-8859-1
            title = title.decode(charset).encode('utf-8')
            title = normalize('NFKD', unicode(title, 'utf-8'))
            title = title.encode('ASCII', 'ignore')
        except UnicodeEncodeError:
            logger.error("Error de encoding")
    return title

    # 


def searchSubtitle(item):
    if config.get_setting("subtitle_type") == 0:
        subtitlepath = config.get_setting("subtitlepath_folder")
        if subtitlepath == "":
            subtitlepath = filetools.join(config.get_data_path(), "subtitles")
            config.set_setting("subtitlepath_folder", subtitlepath)

    elif config.get_setting("subtitle_type") == 1:
        subtitlepath = config.get_setting("subtitlepath_keyboard")
        if subtitlepath == "":
            subtitlepath = filetools.join(config.get_data_path(), "subtitles")
            config.set_setting("subtitlepathkeyboard", subtitlepath)
        elif subtitlepath.startswith("http"):
            subtitlepath = config.get_setting("subtitlepath_folder")

    else:
        subtitlepath = config.get_setting("subtitlepath_folder")
    if subtitlepath == "":
        subtitlepath = filetools.join(config.get_data_path(), "subtitles")
        config.set_setting("subtitlepath_folder", subtitlepath)
    if not filetools.exists(subtitlepath):
        try:
            filetools.mkdir(subtitlepath)
        except:
            logger.error("error no se pudo crear path subtitulos")
            return

    path_movie_subt = xbmc.translatePath(filetools.join(subtitlepath, "Movies"))
    if not filetools.exists(path_movie_subt):
        try:
            filetools.mkdir(path_movie_subt)
        except:
            logger.error("error no se pudo crear el path Movies")
            return
    full_path_tvshow = ""
    path_tvshow_subt = xbmc.translatePath(filetools.join(subtitlepath, "Tvshows"))
    if not filetools.exists(path_tvshow_subt):
        try:
            filetools.mkdir(path_tvshow_subt)
        except:
            logger.error("error no pudo crear el path Tvshows")
            return
    if item.show in item.title:
        title_new = title = urllib.unquote_plus(item.title)
    else:
        title_new = title = urllib.unquote_plus(item.show + " - " + item.title)
    path_video_temp = xbmc.translatePath(filetools.join(config.get_runtime_path(), "resources", "subtitle.mp4"))
    if not filetools.exists(path_video_temp):
        logger.error("error : no existe el video temporal de subtitulos")
        return
    # path_video_temp = xbmc.translatePath(filetools.join( ,video_temp + ".mp4" ))

    title_new = _normalize(title_new)
    tvshow_title, season, episode = regex_tvshow(False, title_new)
    if episode != "":
        full_path_tvshow = xbmc.translatePath(filetools.join(path_tvshow_subt, tvshow_title))
        if not filetools.exists(full_path_tvshow):
            filetools.mkdir(full_path_tvshow)  # title_new + ".mp4"
        full_path_video_new = xbmc.translatePath(
            filetools.join(full_path_tvshow, "%s %sx%s.mp4" % (tvshow_title, season, episode)))
        logger.debug(full_path_video_new)
        listitem = xbmcgui.ListItem(title_new, iconImage="DefaultVideo.png", thumbnailImage="")
        listitem.setInfo("video", {"Title": title_new, "Genre": "Tv shows", "episode": int(episode), "season": int(season), "tvshowtitle": tvshow_title})

    else:
        full_path_video_new = xbmc.translatePath(filetools.join(path_movie_subt, title_new + ".mp4"))
        listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage="")
        listitem.setInfo("video", {"Title": title_new, "Genre": "Movies"})

    import time

    try:
        filetools.copy(path_video_temp, full_path_video_new)
        copy = True
        logger.debug("nuevo path =" + full_path_video_new)
        time.sleep(2)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(full_path_video_new, listitem)
        # xbmcPlayer = xbmc.Player(  xbmc.PLAYER_CORE_AUTO )
        xbmcPlayer = xbmc.Player()
        xbmcPlayer.play(playlist)

        # xbmctools.launchplayer(full_path_video_new,listitem)
    except:
        copy = False
        logger.error("Error : could not copy")

    time.sleep(1)

    if copy:
        if xbmc.Player().isPlayingVideo():
            xbmc.executebuiltin("RunScript(script.xbmc.subtitles)")
            while xbmc.Player().isPlayingVideo():
                continue

        time.sleep(1)
        filetools.remove(full_path_video_new)
        try:
            if full_path_tvshow != "":
                filetools.rmdir(full_path_tvshow)
        except OSError:
            pass


def saveSubtitleName(item):
    if not item.show or item.show in item.title:
        title = item.title
    else:
        title = item.show + " - " + item.title
    try:
        title = _normalize(title)
    except:
        pass

    tvshow_title, season, episode = regex_tvshow(False, title)
    if episode != "":
        # title = "% %sx%s" %(tvshow_title,season,episode)
        config.set_setting("subtitle_name", title)
    else:
        config.set_setting("subtitle_name", title)
    return


def get_from_subdivx(sub_url):

    """
    :param sub_url: Download url of the subtitle hosted on suvdivx.com For Example: http://www.subdivx.com/bajar.php?id=573942&u=8

    :return: The path to the unzipped subtitle
    """

    logger.debug()

    sub = ''
    sub_dir = os.path.join(config.get_data_path(), 'temp_subs')

    if os.path.exists(sub_dir):
        for sub_file in os.listdir(sub_dir):
            old_sub = os.path.join(sub_dir, sub_file)
            os.remove(old_sub)
    else:
        os.mkdir(sub_dir)

    sub_url = sub_url.replace("&amp;", "&")
    sub_data = httptools.downloadpage(sub_url, follow_redirects=False)
    if 'x-frame-options' not in sub_data.headers:
        sub_url = '%s' % sub_data.headers['location']
        ext = sub_url[-4::]
        file_id = "subtitle%s" % ext
        filename = os.path.join(sub_dir, file_id)
        try:
            data_dl = httptools.downloadpage(sub_url).data
            filetools.write(filename, data_dl)
            sub = extract_file_online(sub_dir, filename)
        except:
           logger.debug('sub invalid')
    else:
       logger.debug('sub invalid')
    return sub


def extract_file_online(path, filename):

    """
    :param path: Path where the compressed file is located

    :param filename:  

    :return:  
    """

    logger.debug()

    url = "http://online.b1.org/rest/online/upload"

    data = httptools.downloadpage(url, file=filename).data

    result = jsontools.load(scrapertools.find_single_match(data, "result.listing = ([^;]+);"))
    compressed = result["name"]
    extracted = result["children"][0]["name"]

    dl_url = "http://online.b1.org/rest/online/download/%s/%s" % (compressed, extracted)
    extracted_path = os.path.join(path, extracted)
    data_dl = httptools.downloadpage(dl_url).data
    filetools.write(extracted_path, data_dl)

    return extracted_path
