# -*- coding: utf-8 -*-

import os
import re
import string
import urllib
from unicodedata import normalize

import xbmc
import xbmcgui

from platformcode import config, logger

allchars = string.maketrans('', '')
deletechars = ',\\/:*"<>|?'


# Extraemos el nombre de la serie, temporada y numero de capitulo ejemplo: 'fringe 1x01'
def regex_tvshow(compare, file, sub=""):
    regex_expressions = ['[Ss]([0-9]+)[][._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                         '[\._ \-]([0-9]+)x([0-9]+)([^\\/]*)',  # foo.1x09 
                         '[\._ \-]([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',  # foo.109
                         '([0-9]+)([0-9][0-9])([\._ \-][^\\/]*)',
                         '[\\\\/\\._ -]([0-9]+)([0-9][0-9])[^\\/]*',
                         'Season ([0-9]+) - Episode ([0-9]+)[^\\/]*',
                         'Season ([0-9]+) Episode ([0-9]+)[^\\/]*',
                         '[\\\\/\\._ -][0]*([0-9]+)x[0]*([0-9]+)[^\\/]*',
                         '[[Ss]([0-9]+)\]_\[[Ee]([0-9]+)([^\\/]*)',  # foo_[s01]_[e01]
                         '[\._ \-][Ss]([0-9]+)[\.\-]?[Ee]([0-9]+)([^\\/]*)',  # foo, s01e01, foo.s01.e01, foo.s01-e01
                         's([0-9]+)ep([0-9]+)[^\\/]*',  # foo - s01ep03, foo - s1ep03
                         '[Ss]([0-9]+)[][ ._-]*[Ee]([0-9]+)([^\\\\/]*)$',
                         '[\\\\/\\._ \\[\\(-]([0-9]+)x([0-9]+)([^\\\\/]*)$',
                         '[\\\\/\\._ \\[\\(-]([0-9]+)X([0-9]+)([^\\\\/]*)$'
                         ]
    sub_info = ""
    tvshow = 0

    for regex in regex_expressions:
        response_file = re.findall(regex, file)
        if len(response_file) > 0:
            print "Regex File Se: %s, Ep: %s," % (str(response_file[0][0]), str(response_file[0][1]),)
            tvshow = 1
            if not compare:
                title = re.split(regex, file)[0]
                for char in ['[', ']', '_', '(', ')', '.', '-']:
                    title = title.replace(char, ' ')
                if title.endswith(" "): title = title.strip()
                print "title: %s" % title
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

        # Obtiene el nombre de la pelicula o capitulo de la serie guardado previamente en configuraciones del plugin 
        # y luego lo busca en el directorio de subtitulos, si los encuentra los activa.


def set_Subtitle():
    logger.info()

    exts = [".srt", ".sub", ".txt", ".smi", ".ssa", ".ass"]
    subtitle_folder_path = os.path.join(config.get_data_path(), "subtitles")

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
            long = len(subtitle_path)
            if long > 0:
                if subtitle_path.startswith("http") or subtitle_path[long - 4, long] in exts:
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
                Subnames = glob.glob(os.path.join(subtitle_path, "Tvshows", tvshow_title,
                                                  "%s %sx%s" % (tvshow_title, season, episode) + "*.??.???"))
            else:
                Subnames = glob.glob(os.path.join(subtitle_path, "Movies", subtitle_name + "*.??.???"))
            for Subname in Subnames:
                if os.path.splitext(Subname)[1] in exts:
                    logger.info("Con subtitulo : " + os.path.split(Subname)[1])
                    xbmc.Player().setSubtitles((Subname))
        except:
            logger.error("error al cargar subtitulos")

            # Limpia los caracteres unicode


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
            subtitlepath = os.path.join(config.get_data_path(), "subtitles")
            config.set_setting("subtitlepath_folder", subtitlepath)

    elif config.get_setting("subtitle_type") == 1:
        subtitlepath = config.get_setting("subtitlepath_keyboard")
        if subtitlepath == "":
            subtitlepath = os.path.join(config.get_data_path(), "subtitles")
            config.set_setting("subtitlepathkeyboard", subtitlepath)
        elif subtitlepath.startswith("http"):
            subtitlepath = config.get_setting("subtitlepath_folder")

    else:
        subtitlepath = config.get_setting("subtitlepath_folder")
    if subtitlepath == "":
        subtitlepath = os.path.join(config.get_data_path(), "subtitles")
        config.set_setting("subtitlepath_folder", subtitlepath)
    if not os.path.exists(subtitlepath):
        try:
            os.mkdir(subtitlepath)
        except:
            logger.error("error no se pudo crear path subtitulos")
            return

    path_movie_subt = xbmc.translatePath(os.path.join(subtitlepath, "Movies"))
    if not os.path.exists(path_movie_subt):
        try:
            os.mkdir(path_movie_subt)
        except:
            logger.error("error no se pudo crear el path Movies")
            return
    full_path_tvshow = ""
    path_tvshow_subt = xbmc.translatePath(os.path.join(subtitlepath, "Tvshows"))
    if not os.path.exists(path_tvshow_subt):
        try:
            os.mkdir(path_tvshow_subt)
        except:
            logger.error("error no pudo crear el path Tvshows")
            return
    if item.show in item.title:
        title_new = title = urllib.unquote_plus(item.title)
    else:
        title_new = title = urllib.unquote_plus(item.show + " - " + item.title)
    path_video_temp = xbmc.translatePath(os.path.join(config.get_runtime_path(), "resources", "subtitle.mp4"))
    if not os.path.exists(path_video_temp):
        logger.error("error : no existe el video temporal de subtitulos")
        return
    # path_video_temp = xbmc.translatePath(os.path.join( ,video_temp + ".mp4" ))

    title_new = _normalize(title_new)
    tvshow_title, season, episode = regex_tvshow(False, title_new)
    if episode != "":
        full_path_tvshow = xbmc.translatePath(os.path.join(path_tvshow_subt, tvshow_title))
        if not os.path.exists(full_path_tvshow):
            os.mkdir(full_path_tvshow)  # title_new + ".mp4"
        full_path_video_new = xbmc.translatePath(
            os.path.join(full_path_tvshow, "%s %sx%s.mp4" % (tvshow_title, season, episode)))
        logger.info(full_path_video_new)
        listitem = xbmcgui.ListItem(title_new, iconImage="DefaultVideo.png", thumbnailImage="")
        listitem.setInfo("video",
                         {"Title": title_new, "Genre": "Tv shows", "episode": int(episode), "season": int(season),
                          "tvshowtitle": tvshow_title})

    else:
        full_path_video_new = xbmc.translatePath(os.path.join(path_movie_subt, title_new + ".mp4"))
        listitem = xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage="")
        listitem.setInfo("video", {"Title": title_new, "Genre": "Movies"})

    import shutil, time

    try:
        shutil.copy(path_video_temp, full_path_video_new)
        copy = True
        logger.info("nuevo path =" + full_path_video_new)
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
        logger.error("Error : no se pudo copiar")

    time.sleep(1)

    if copy:
        if xbmc.Player().isPlayingVideo():
            xbmc.executebuiltin("RunScript(script.xbmc.subtitles)")
            while xbmc.Player().isPlayingVideo():
                continue

        time.sleep(1)
        os.remove(full_path_video_new)
        try:
            if full_path_tvshow != "":
                os.rmdir(full_path_tvshow)
        except OSError:
            pass


def saveSubtitleName(item):
    if item.show in item.title:
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
