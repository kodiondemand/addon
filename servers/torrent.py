# -*- coding: utf-8 -*-

import re, os, sys, time, requests, xbmc, xbmcaddon

from core import filetools, httptools, jsontools
from core.support import info, match
from platformcode import config, platformtools, logger
from lib.guessit import guessit
from lib.torrentool.api import Torrent

if sys.version_info[0] >= 3:
    import urllib.parse as urllib
else:
    import urllib

monitor = filetools.join(config.get_data_path(), 'elementum_monitor.json')
extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg', '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg', '.mpe', '.mp4', '.ogg', '.wmv']


def test_video_exists(page_url):
    return True, ""


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user='', password='', video_password=''):
    # torrent_options = platformtools.torrent_client_installed(show_tuple=True)
    # if len(torrent_options) == 0:
    #     from platformcode import elementum_download
    #     if not elementum_download.download():
    #         return []
    info('server=torrent, the url is the good')

    if page_url.startswith('magnet:'):
        video_urls = [['magnet: [torrent]', page_url]]
    else:
        video_urls = [['.torrent [torrent]', page_url]]

    return video_urls


class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass

xbmc_player = XBMCPlayer()

def mark_auto_as_watched(item):

    time_limit = time.time() + 150
    while not platformtools.is_playing() and time.time() < time_limit:
        time.sleep(5)
    if item.subtitle:
        time.sleep(5)
        xbmc_player.setSubtitles(item.subtitle)

    if item.strm_path and platformtools.is_playing():
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)


def setting():
    elementum_setting = ''
    elementum_host = ''
    TorrentPath = ''
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.elementum")') == 1:
        try:
            elementum_setting = xbmcaddon.Addon(id='plugin.video.elementum')
            elementum_host = 'http://127.0.0.1:' + elementum_setting.getSetting('remote_port') + '/torrents/'
            TorrentPath = xbmc.translatePath(elementum_setting.getSetting('torrents_path'))
        except:
            pass

    return elementum_setting, elementum_host, TorrentPath


def elementum_download(item):
    elementum_setting, elementum_host, TorrentPath = setting()

    if elementum_setting:
        set_elementum(True)
        time.sleep(3)
        if config.get_setting('downloadpath').startswith('smb'):
            select = platformtools.dialog_yesno('Elementum', config.get_localized_string(70807))
            if select:
                xbmc.executebuiltin("RunPlugin(plugin://plugin.video.kod/?eyJjaGFubmVsIjoic2hvcnRjdXRzIiwgImFjdGlvbiI6IlNldHRpbmdPblBvc2l0aW9uIiwgImNhdGVnb3J5Ijo2LCAic2V0dGluZyI6MX0=)")
        else:
            TorrentName = match(item.url, patron=r'btih(?::|%3A)([^&%]+)', string=True).match
            post = 'uri=%s&file=null&all=1' % urllib.quote_plus(item.url)
            res = httptools.downloadpage(elementum_host  + 'add', post=post, timeout=5, alfa_s=True, ignore_response_code=True)
            # match(elementum_host  + 'add', post=post, timeout=5, alfa_s=True, ignore_response_code=True)
            while not filetools.isfile(filetools.join(elementum_setting.getSetting('torrents_path'), TorrentName + '.torrent')):
                time.sleep(1)

        monitor_update(TorrentPath, TorrentName)


def elementum_monitor():
    # from core.support import dbg;dbg()
    path = xbmc.translatePath(config.get_setting('downloadlistpath'))
    elementum_setting, elementum_host, TorrentPath = setting()
    # active_torrent = filetools.listdir(TorrentPath)
    # logger.debug('ELEMENTUM:', elementum_setting, elementum_host, TorrentPath)

    if elementum_setting:
        # check if command file exist
        if filetools.isfile(monitor):
            json = jsontools.load(open(monitor, "r").read())
            Monitor = json['monitor']
        # else create it
        else:
            Monitor = jsontools.load('{"monitor":{},"settings":{}}')
            json = jsontools.dump(Monitor)
            filetools.write(monitor, json, silent=True)

        if len(Monitor) > 0:
            try:
                data = requests.get(elementum_host + '/list', timeout=2).json()
            except:
                data = ''
            if data:
                # from core.support import dbg;dbg()
                for it in data:
                    progress = round(it['progress'], 2)
                    status = it['status']
                    name = it['id']
                    if name in Monitor:
                        jsontools.update_node(progress, Monitor[name]['file'], 'downloadProgress', path, silent=True)
                        jsontools.update_node(4, Monitor[name]['file'], 'downloadStatus', path, silent=True)
                        if status in ['Paused']:
                            jsontools.update_node(0, Monitor[name]['file'], 'downloadStatus', path, silent=True)
                        if status in ['Seeding', 'Finished'] and not config.get_setting('elementum_on_seed'):
                            monitor_update(TorrentPath, name, remove=True)
                            dlJson = jsontools.load(open(filetools.join(path, Monitor[name]['file']), "r").read())
                            jsontools.update_node(dlJson['downloadSize'], Monitor[name]['file'], 'downloadCompleted', path, silent=True)
                            jsontools.update_node(2, Monitor[name]['file'], 'downloadStatus', path, silent=True)
                            requests.get(elementum_host + 'pause/' + name)
                            filetools.remove(filetools.join(TorrentPath, name + '.torrent'))
                            filetools.remove(filetools.join(TorrentPath, name + '.fastresume'))
                            # time.sleep(1)
                            # rename(Monitor[name]['file'])


def monitor_update(TorrentPath, value, remove=False):
    elementum_setting, elementum_host, TorrentPath = setting()
    json = jsontools.load(open(monitor, "r").read())
    Monitor = json['monitor']
    info = Torrent.from_file(filetools.join(TorrentPath, value + '.torrent'))
    logger.debug('ELEMENTUM MONITOR', Monitor)
    path = xbmc.translatePath(config.get_setting('downloadlistpath'))

    if not value in Monitor:
        Monitor[value]={}
        Monitor[value]['name'] = info.name
        Monitor[value]['size'] = info.total_size
        File = find_file(value)
        Monitor[value]['file'] = File
        json = jsontools.dump(json)
        filetools.write(monitor, json, silent=True)

        backupFilename = jsontools.load(open(filetools.join(path, File), "r").read())['downloadFilename']
        jsontools.update_node(value, File, 'TorrentName', path, silent=True)
        jsontools.update_node(info.total_size, File, 'downloadSize', path, silent=True)
        jsontools.update_node(backupFilename, File, 'backupFilename', path, silent=True)
        jsontools.update_node(info.name, File, 'downloadFilename', path, silent=True)

    elif remove:
        Monitor.pop(value)
        jsontools.dump(json)
        filetools.write(monitor, jsontools.dump(json), silent=True)

    if len(Monitor) == 0: set_elementum()


def set_elementum(SET=False):
    elementum_setting, elementum_host, TorrentPath = setting()
    json = jsontools.load(open(monitor, "r").read())
    backup_setting = json['settings']
    write = False
    if SET:
        elementum_setting.setSetting('download_storage', '0')  
        if elementum_setting.getSetting('logger_silent') == False or not 'logger_silent' in backup_setting:
            elementum_setting.setSetting('logger_silent', 'true')
            backup_setting['logger_silent'] = 'false'

        # if elementum_setting.getSetting('download_storage') != 0 or not 'download_storage' in backup_setting:
        #     backup_setting['download_storage'] = elementum_setting.getSetting('download_storage')           # Backup Setting
        #     elementum_setting.setSetting('download_storage', '0')                                    # Set Setting

        if elementum_setting.getSetting('download_path') != config.get_setting('downloadpath') or not 'download_path' in backup_setting:
            backup_setting['download_path'] = elementum_setting.getSetting('download_path')              # Backup Setting
            elementum_setting.setSetting('download_path', config.get_setting('downloadpath'))        # Set Setting
        write = True

    elif backup_setting:
        elementum_setting.setSetting('logger_silent', backup_setting['logger_silent'])
        elementum_setting.setSetting('download_storage', '1')
        # elementum_setting.setSetting('download_storage', backup_setting['download_storage'])
        elementum_setting.setSetting('download_path', backup_setting['download_path'])
        json['settings'] = {}
        write = True
    if write:
        json = jsontools.dump(json)
        filetools.write(monitor, json, silent=True)
        time.sleep(1)


def find_file(hash):
    path = xbmc.translatePath(config.get_setting('downloadlistpath'))
    files = filetools.listdir(path)
    for f in files:
        filepath = filetools.join(path, f)
        json = jsontools.load(filetools.read(filepath))
        if ('downloadServer' in json and 'url' in json['downloadServer'] and hash in json['downloadServer']['url']) or ('url' in json and hash in json['url']):
            break
    return filetools.split(filepath)[-1]


def elementum_actions(parameter, TorrentHash):
    elementum_setting, elementum_host, TorrentPath = setting()
    if elementum_setting:
        try:
            if parameter == 'delete': monitor_update(TorrentPath, TorrentHash, remove=True)
            requests.get('%s/%s/%s' %(elementum_host, parameter, TorrentHash))
        except:
            pass


def process_filename(filename, Title, ext=True):
    extension = os.path.splitext(filename)[-1]
    parsedTitle = guessit(filename)
    t = parsedTitle.get('title', '')
    episode = ''
    s = ' - '
    if parsedTitle.get('episode') and parsedTitle.get('season'):
        if type(parsedTitle.get('season')) == list:
            episode += str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
        else:
            episode += str(parsedTitle.get('season'))

        if type(parsedTitle.get('episode')) == list:
                episode += 'x' + str(parsedTitle.get('episode')[0]).zfill(2) + '-' + str(parsedTitle.get('episode')[-1]).zfill(2)
        else:
            episode += 'x' + str(parsedTitle.get('episode')).zfill(2)
    elif parsedTitle.get('season') and type(parsedTitle.get('season')) == list:
        episode += s + config.get_localized_string(30140) + " " +str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
    elif parsedTitle.get('season'):
        episode += s + config.get_localized_string(60027) % str(parsedTitle.get('season'))
    if parsedTitle.get('episode_title'):
        episode += s + parsedTitle.get('episode_title')
    title = (t if t else Title) + s + episode + (extension if ext else '')
    return title


def rename(File):
    jsonPath = xbmc.translatePath(config.get_setting('downloadlistpath'))
    json = jsontools.load(open(filetools.join(jsonPath, File), "r").read())
    filePath = filetools.join(xbmc.translatePath(config.get_setting('downloadpath')), json['downloadFilename'])

    if json['infoLabels']['mediatype'] == 'movie':
        if filetools.isdir(filePath):
            extension = ''
            files = filetools.listdir(filePath)
            oldName = json['downloadFilename']
            newName = json['backupFilename']
            for f in files:
                ext = os.path.splitext(f)[-1]
                if ext in extensions_list: extension = ext
                filetools.rename(filetools.join(filePath, f), f.replace(oldName, newName))
            filetools.rename(filePath, newName)
            jsontools.update_node(filetools.join(newName, newName + extension), File, 'downloadFilename', jsonPath)

        else:
            oldName = json['downloadFilename']
            newName = json['backupFilename'] + os.path.splitext(oldName)[-1]
            filetools.rename(filePath, newName)
            jsontools.update_node(newName, File, 'downloadFilename', jsonPath)
    else:
        sep = '/' if filePath.lower().startswith("smb://") else os.sep
        FolderName = json['backupFilename'].split(sep)[0]
        Title = re.sub(r'(\s*\[[^\]]+\])', '', FolderName)
        if filetools.isdir(filePath):
            files = filetools.listdir(filePath)
            file_dict = {}
            for f in files:
                title = process_filename(f, Title, ext=False)
                ext = os.path.splitext(f)[-1]
                name = os.path.splitext(f)[0]
                if title not in file_dict and ext in extensions_list:
                    file_dict[title] = name

            for title, name in file_dict.items():
                for f in files:
                    if name in f:
                        filetools.rename(filetools.join(filePath, f), f.replace(name, title))

            filetools.rename(filePath, FolderName)
            jsontools.update_node(FolderName, File, 'downloadFilename', jsonPath)
        else:
            filename = filetools.split(filePath)[-1]
            title = process_filename(filename, Title)
            NewFolder = filetools.join(config.get_setting('downloadpath'), FolderName)
            if not filetools.isdir(NewFolder):
                filetools.mkdir(NewFolder)
            from_folder = filetools.join(config.get_setting('downloadpath'), filename)
            to_folder = filetools.join(config.get_setting('downloadpath'), FolderName, title)
            filetools.move(from_folder, to_folder)
            jsontools.update_node(filetools.join(FolderName, title), File, 'downloadFilename', jsonPath)