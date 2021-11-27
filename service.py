# -*- coding: utf-8 -*-
import os
import sys
import threading
import traceback
import xbmc
from platformcode import config

try:
    from urllib.parse import urlsplit
except ImportError:
    from urlparse import urlsplit
# on kodi 18 its xbmc.translatePath, on 19 xbmcvfs.translatePath
try:
    import xbmcvfs
    xbmc.translatePath = xbmcvfs.translatePath
except:
    pass
librerias = xbmc.translatePath(os.path.join(config.getRuntimePath(), 'lib'))
sys.path.insert(0, librerias)

from core import filetools, httptools, scrapertools, db, videolibrarydb
from lib import schedule
from platformcode import logger, platformtools, updater, xbmc_videolibrary
from specials import videolibrary

# if this service need to be reloaded because an update changed it
needsReload = False
# list of threads
threads = []


def check_for_update():
    if config.getSetting("update", "videolibrary"):
        videolibrary.update_videolibrary()


def updaterCheck():
    global needsReload
    # updater check
    updated, needsReload = updater.check(background=True)


def get_ua_list():
    # https://github.com/alfa-addon/addon/blob/master/plugin.video.alfa/platformcode/updater.py#L273
    logger.info()
    url = "http://omahaproxy.appspot.com/all?csv=1"

    try:
        current_ver = config.getSetting("chrome_ua_version", default="").split(".")
        data = httptools.downloadpage(url, alfa_s=True).data
        new_ua_ver = scrapertools.find_single_match(data, "win64,stable,([^,]+),")

        if not current_ver:
            config.setSetting("chrome_ua_version", new_ua_ver)
        else:
            for pos, val in enumerate(new_ua_ver.split('.')):
                if int(val) > int(current_ver[pos]):
                    config.setSetting("chrome_ua_version", new_ua_ver)
                    break
    except:
        logger.error(traceback.format_exc())


def run_threaded(job_func, args):
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()
    threads.append(job_thread)


def join_threads():
    logger.debug(threads)
    for th in threads:
        try:
            th.join()
        except:
            logger.error(traceback.format_exc())


class AddonMonitor(xbmc.Monitor):
    def __init__(self):
        self.settings_pre = config.getAllSettingsAddon()

        self.updaterPeriod = None
        self.update_setting = None
        self.update_hour = None
        self.scheduleScreenOnJobs()
        self.scheduleUpdater()
        self.scheduleUA()

        if not needsReload:  # do not run videolibrary update if service needs to be reloaded
            # videolibrary wait
            update_wait = [0, 10000, 20000, 30000, 60000]
            wait = update_wait[int(config.getSetting("update_wait", "videolibrary"))]
            if wait > 0:
                xbmc.sleep(wait)
            if not config.getSetting("update", "videolibrary") == 2:
                run_threaded(check_for_update, [])
            self.scheduleVideolibrary()
        super(AddonMonitor, self).__init__()

    def onSettingsChanged(self):
        logger.debug('settings changed')
        settings_post = config.getAllSettingsAddon()
        # sometimes kodi randomly return default settings (rare but happens), this if try to workaround this
        if settings_post and settings_post.get('show_once', True):

            from platformcode import xbmc_videolibrary

            if self.settings_pre.get('downloadpath', None) != settings_post.get('downloadpath', None):
                xbmc_videolibrary.update_sources(settings_post.get('downloadpath', None),
                                                 self.settings_pre.get('downloadpath', None))

            # If the path of the video library has been changed, we call to check directories so that it creates it and automatically asks if to configure the video library
            if self.settings_pre.get("videolibrarypath", None) and self.settings_pre.get("videolibrarypath", None) != settings_post.get("videolibrarypath", None) or \
                self.settings_pre.get("folder_movies", None) and self.settings_pre.get("folder_movies", None) != settings_post.get("folder_movies", None) or \
                self.settings_pre.get("folder_tvshows", None) and self.settings_pre.get("folder_tvshows", None) != settings_post.get("folder_tvshows", None):
                videolibrary.move_videolibrary(self.settings_pre.get("videolibrarypath", ''),
                                               settings_post.get("videolibrarypath", ''),
                                               self.settings_pre.get("folder_movies", ''),
                                               settings_post.get("folder_movies", ''),
                                               self.settings_pre.get("folder_tvshows", ''),
                                               settings_post.get("folder_tvshows", ''))

            # if you want to autoconfigure and the video library directory had been created
            if not self.settings_pre.get("videolibrary_kodi", None) and settings_post.get("videolibrary_kodi", None):
                xbmc_videolibrary.set_content(silent=True)
            elif self.settings_pre.get("videolibrary_kodi", None) and not settings_post.get("videolibrary_kodi", None):
                xbmc_videolibrary.clean()

            if self.settings_pre.get('addon_update_timer') != settings_post.get('addon_update_timer'):
                schedule.clear('updater')
                self.scheduleUpdater()

            if self.update_setting != config.getSetting("update", "videolibrary") or self.update_hour != config.getSetting("everyday_delay", "videolibrary") * 4:
                schedule.clear('videolibrary')
                self.scheduleVideolibrary()

            if self.settings_pre.get('elementum_on_seed') != settings_post.get('elementum_on_seed') and settings_post.get('elementum_on_seed'):
                if not platformtools.dialogYesNo(config.getLocalizedString(70805), config.getLocalizedString(70806)):
                    config.setSetting('elementum_on_seed', False)
            if self.settings_pre.get("shortcut_key", '') != settings_post.get("shortcut_key", ''):
                xbmc.executebuiltin('Action(reloadkeymaps)')

            # backup settings
            filetools.copy(os.path.join(config.getDataPath(), "settings.xml"),
                           os.path.join(config.getDataPath(), "settings.bak"), True)
            logger.debug({k: self.settings_pre[k] for k in self.settings_pre
                          if k in settings_post and self.settings_pre[k] != settings_post[k]})

            self.settings_pre = config.getAllSettingsAddon()

    def onNotification(self, sender, method, data):
        logger.debug('METODO', method)
        if method == 'VideoLibrary.OnUpdate':
            xbmc_videolibrary.set_watched_on_kod(data)
            logger.debug('AGGIORNO')
        if method == 'Player.OnAVStart':
            logger.debug('CONTROLLO VIDEO IN PLAY')
            xbmc_videolibrary.mark_auto_as_watched()

    def onScreensaverActivated(self):
        logger.debug('screensaver activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onScreensaverDeactivated(self):
        logger.debug('screensaver deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()

    def scheduleUpdater(self):
        if not config.devMode():
            updaterCheck()
            self.updaterPeriod = config.getSetting('addon_update_timer')
            schedule.every(self.updaterPeriod).hours.do(updaterCheck).tag('updater')
            logger.debug('scheduled updater every ' + str(self.updaterPeriod) + ' hours')

    def scheduleUA(self):
        get_ua_list()
        schedule.every(1).day.do(get_ua_list)

    def scheduleVideolibrary(self):
        self.update_setting = config.getSetting("update", "videolibrary")
        # 2= daily 3=daily and when kodi starts
        if self.update_setting == 2 or self.update_setting == 3:
            self.update_hour = config.getSetting("everyday_delay", "videolibrary") * 4
            schedule.every().day.at(str(self.update_hour).zfill(2) + ':00').do(check_for_update).tag('videolibrary')
            logger.debug('scheduled videolibrary at ' + str(self.update_hour).zfill(2) + ':00')

    def scheduleScreenOnJobs(self):
        # pass
        schedule.every().second.do(platformtools.viewModeMonitor).tag('screenOn')
        # schedule.every().second.do(torrent.elementum_monitor).tag('screenOn')

    def onDPMSActivated(self):
        logger.debug('DPMS activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onDPMSDeactivated(self):
        logger.debug('DPMS deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()


if __name__ == "__main__":
    logger.info('Starting KoD service')

    # Test if all the required directories are created
    config.verifyDirectoriesCreated()

    import glob, xbmc
    from core import videolibrarytools, tmdb
    from core.item import Item

    if config.getSetting('videolibrary_kodi') and config.getSetting('show_once'):
        nun_records, records = xbmc_videolibrary.execute_sql_kodi('select * from path where strPath = "' +
                                                                  filetools.join(config.getSetting('videolibrarypath'),
                                                                                 config.getSetting('folder_tvshows')) +
                                                                  '/" and strScraper<>"metadata.local"')
        if nun_records:
            videolibrarytools.convert_videolibrary()


    if config.getSetting('autostart'):
        xbmc.executebuiltin('RunAddon(plugin.video.' + config.PLUGIN_NAME + ')')

    # check if the user has any connection problems
    from platformcode.checkhost import test_conn
    run_threaded(test_conn, (True, not config.getSetting('resolver_dns'), True, [], [], True))

    monitor = AddonMonitor()

    # mark as stopped all downloads (if we are here, probably kodi just started)
    from specials.downloads import stop_all
    try:
        stop_all()
    except:
        logger.error(traceback.format_exc())

    while True:
        try:
            schedule.run_pending()
        except:
            logger.error(traceback.format_exc())

        if needsReload:
            db.close()
            videolibrarydb.close()
            join_threads()

            logger.info('Relaunching service.py')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.kod", "enabled": false }}')
            xbmc.executeJSONRPC(
                '{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.kod", "enabled": true }}')
            logger.debug(threading.enumerate())
            break

        if monitor.waitForAbort(1):  # every second
            # db need to be closed when not used, it will cause freezes
            db.close()
            videolibrarydb.close()
            join_threads()
            break
