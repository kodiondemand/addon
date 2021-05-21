# -*- coding: utf-8 -*-
import datetime
import math
import os
import sys
import threading
import traceback
import xbmc
import xbmcgui
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
librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)

from core import videolibrarytools, filetools, channeltools, httptools, scrapertools, db
from lib import schedule
from platformcode import logger, platformtools, updater, xbmc_videolibrary
from specials import videolibrary
from servers import torrent


def update(path, p_dialog, i, t, serie, overwrite):
    logger.debug("Updating " + path)
    insertados_total = 0
    nfo_file = xbmc.translatePath(filetools.join(path, 'tvshow.nfo'))

    head_nfo, it = videolibrarytools.read_nfo(nfo_file)
    videolibrarytools.update_renumber_options(it, head_nfo, path)

    if not serie.library_url: serie = it
    category = serie.category

    # logger.debug("%s: %s" %(serie.contentSerieName,str(list_canales) ))
    for channel, url in serie.library_urls.items():
        serie.channel = channel
        module = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
        url = module.host + urlsplit(url).path
        serie.url = url

        ###### Redirection to the NewPct1.py channel if it is a clone, or to another channel and url if there has been judicial intervention
        try:
            head_nfo, it = videolibrarytools.read_nfo(nfo_file)         # Refresh the .nfo to collect updates
            if it.emergency_urls:
                serie.emergency_urls = it.emergency_urls
            serie.category = category
        except:
            logger.error(traceback.format_exc())

        channel_enabled = channeltools.is_enabled(serie.channel)

        if channel_enabled:

            heading = config.get_localized_string(20000)
            p_dialog.update(int(math.ceil((i + 1) * t)), heading, config.get_localized_string(60389) % (serie.contentSerieName, serie.channel.capitalize()))
            try:
                pathchannels = filetools.join(config.get_runtime_path(), "channels", serie.channel + '.py')
                logger.debug("loading channel: " + pathchannels + " " + serie.channel)

                if serie.library_filter_show:
                    serie.show = serie.library_filter_show.get(serie.channel, serie.contentSerieName)

                obj = __import__('channels.%s' % serie.channel, fromlist=[pathchannels])

                itemlist = obj.episodios(serie)

                try:
                    if int(overwrite) == 3:
                        # Overwrite all files (tvshow.nfo, 1x01.nfo, 1x01 [channel] .json, 1x01.strm, etc ...)
                        insertados, sobreescritos, fallidos, notusedpath = videolibrarytools.save_tvshow(serie, itemlist)
                        #serie= videolibrary.check_season_playcount(serie, serie.contentSeason)
                        #if filetools.write(path + '/tvshow.nfo', head_nfo + it.tojson()):
                        #    serie.infoLabels['playcount'] = serie.playcount
                    else:
                        insertados, sobreescritos, fallidos = videolibrarytools.save_episodes(path, itemlist, serie,
                                                                                              silent=True,
                                                                                              overwrite=overwrite)
                        #it = videolibrary.check_season_playcount(it, it.contentSeason)
                        #if filetools.write(path + '/tvshow.nfo', head_nfo + it.tojson()):
                        #    serie.infoLabels['playcount'] = serie.playcount
                    insertados_total += insertados

                except:
                    import traceback
                    logger.error("Error when saving the chapters of the series")
                    logger.error(traceback.format_exc())

            except:
                import traceback
                logger.error("Error in obtaining the episodes of: %s" % serie.show)
                logger.error(traceback.format_exc())

        else:
            logger.debug("Channel %s not active is not updated" % serie.channel)
    # Synchronize the episodes seen from the Kodi video library with that of KoD
    try:
        if config.is_xbmc():                # If it's Kodi, we do it
            from platformcode import xbmc_videolibrary
            xbmc_videolibrary.mark_content_as_watched_on_kod(filetools.join(path,'tvshow.nfo'))
    except:
        logger.error(traceback.format_exc())

    return insertados_total > 0


def check_for_update():
    if config.get_setting("update", "videolibrary"):
        videolibrary.update_videolibrary()


def updaterCheck():
    # updater check
    updated, needsReload = updater.check(background=True)
    if needsReload:
        xbmc.executescript(__file__)
        exit(0)


def get_ua_list():
    # https://github.com/alfa-addon/addon/blob/master/plugin.video.alfa/platformcode/updater.py#L273
    logger.info()
    url = "http://omahaproxy.appspot.com/all?csv=1"

    try:
        current_ver = config.get_setting("chrome_ua_version", default="").split(".")
        data = httptools.downloadpage(url, alfa_s=True).data
        new_ua_ver = scrapertools.find_single_match(data, "win64,stable,([^,]+),")

        if not current_ver:
            config.set_setting("chrome_ua_version", new_ua_ver)
        else:
            for pos, val in enumerate(new_ua_ver.split('.')):
                if int(val) > int(current_ver[pos]):
                    config.set_setting("chrome_ua_version", new_ua_ver)
                    break
    except:
        logger.error(traceback.format_exc())


def run_threaded(job_func, args):
    job_thread = threading.Thread(target=job_func, args=args)
    job_thread.start()


class AddonMonitor(xbmc.Monitor):
    def __init__(self):
        self.settings_pre = config.get_all_settings_addon()

        self.updaterPeriod = None
        self.update_setting = None
        self.update_hour = None
        self.scheduleScreenOnJobs()
        self.scheduleUpdater()
        self.scheduleUA()

        # videolibrary wait
        update_wait = [0, 10000, 20000, 30000, 60000]
        wait = update_wait[int(config.get_setting("update_wait", "videolibrary"))]
        if wait > 0:
            xbmc.sleep(wait)
        if not config.get_setting("update", "videolibrary") == 2:
            run_threaded(check_for_update, (False,))
        self.scheduleVideolibrary()
        super(AddonMonitor, self).__init__()

    def onSettingsChanged(self):
        logger.debug('settings changed')
        settings_post = config.get_all_settings_addon()
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
                xbmc_videolibrary.ask_set_content(silent=True)
            elif self.settings_pre.get("videolibrary_kodi", None) and not settings_post.get("videolibrary_kodi", None):
                xbmc_videolibrary.clean()

            if self.settings_pre.get('addon_update_timer') != settings_post.get('addon_update_timer'):
                schedule.clear('updater')
                self.scheduleUpdater()

            if self.update_setting != config.get_setting("update", "videolibrary") or self.update_hour != config.get_setting("everyday_delay", "videolibrary") * 4:
                schedule.clear('videolibrary')
                self.scheduleVideolibrary()

            if self.settings_pre.get('elementum_on_seed') != settings_post.get('elementum_on_seed') and settings_post.get('elementum_on_seed'):
                if not platformtools.dialog_yesno(config.get_localized_string(70805), config.get_localized_string(70806)):
                    config.set_setting('elementum_on_seed', False)
            if self.settings_pre.get("shortcut_key", '') != settings_post.get("shortcut_key", ''):
                xbmc.executebuiltin('Action(reloadkeymaps)')

            # backup settings
            filetools.copy(os.path.join(config.get_data_path(), "settings.xml"),
                           os.path.join(config.get_data_path(), "settings.bak"), True)
            logger.debug({k: self.settings_pre[k] for k in self.settings_pre
                          if k in settings_post and self.settings_pre[k] != settings_post[k]})

            self.settings_pre = config.get_all_settings_addon()

    def onNotification(self, sender, method, data):
        if method == 'VideoLibrary.OnUpdate':
            xbmc_videolibrary.set_watched_on_kod(data)
            logger.debug('AGGIORNO')

    def onScreensaverActivated(self):
        logger.debug('screensaver activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onScreensaverDeactivated(self):
        logger.debug('screensaver deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()

    def scheduleUpdater(self):
        if not config.dev_mode():
            updaterCheck()
            self.updaterPeriod = config.get_setting('addon_update_timer')
            schedule.every(self.updaterPeriod).hours.do(updaterCheck).tag('updater')
            logger.debug('scheduled updater every ' + str(self.updaterPeriod) + ' hours')

    def scheduleUA(self):
        get_ua_list()
        schedule.every(1).day.do(get_ua_list)

    def scheduleVideolibrary(self):
        self.update_setting = config.get_setting("update", "videolibrary")
        # 2= daily 3=daily and when kodi starts
        if self.update_setting == 2 or self.update_setting == 3:
            self.update_hour = config.get_setting("everyday_delay", "videolibrary") * 4
            schedule.every().day.at(str(self.update_hour).zfill(2) + ':00').do(run_threaded, check_for_update, (False,)).tag('videolibrary')
            logger.debug('scheduled videolibrary at ' + str(self.update_hour).zfill(2) + ':00')

    def scheduleScreenOnJobs(self):
        schedule.every().second.do(platformtools.viewmodeMonitor).tag('screenOn')
        schedule.every().second.do(torrent.elementum_monitor).tag('screenOn')

    def onDPMSActivated(self):
        logger.debug('DPMS activated, un-scheduling screen-on jobs')
        schedule.clear('screenOn')

    def onDPMSDeactivated(self):
        logger.debug('DPMS deactivated, re-scheduling screen-on jobs')
        self.scheduleScreenOnJobs()


if __name__ == "__main__":
    logger.info('Starting KoD service')

    # Test if all the required directories are created
    config.verify_directories_created()

    if config.get_setting('autostart'):
        xbmc.executebuiltin('RunAddon(plugin.video.' + config.PLUGIN_NAME + ')')

    # port old db to new
    old_db_name = filetools.join(config.get_data_path(), "kod_db.sqlite")
    if filetools.isfile(old_db_name):
        try:
            import sqlite3

            old_db_conn = sqlite3.connect(old_db_name, timeout=15)
            old_db = old_db_conn.cursor()
            old_db.execute('select * from viewed')

            for ris in old_db.fetchall():
                if ris[1]:  # tvshow
                    show = db['viewed'].get(ris[0], {})
                    show[str(ris[1]) + 'x' + str(ris[2])] = ris[3]
                    db['viewed'][ris[0]] = show
                else:  # film
                    db['viewed'][ris[0]] = ris[3]
        except:
            pass
        finally:
            filetools.remove(old_db_name, True, False)

    # replace tvdb to tmdb for series
    if config.get_setting('videolibrary_kodi') and config.get_setting('show_once'):
        nun_records, records = xbmc_videolibrary.execute_sql_kodi('select * from path where strPath like "' +
                                           filetools.join(config.get_setting('videolibrarypath'), config.get_setting('folder_tvshows')) +
                                           '%" and strScraper="metadata.tvdb.com"')
        if nun_records:
            import xbmcaddon
            # change language
            tvdbLang = xbmcaddon.Addon(id="metadata.tvdb.com").getSetting('language')
            newLang = tvdbLang + '-' + tvdbLang.upper()
            xbmcaddon.Addon(id="metadata.tvshows.themoviedb.org").setSetting('language', newLang)
            updater.refreshLang()

            # prepare to replace strSettings
            path_settings = xbmc.translatePath(
                "special://profile/addon_data/metadata.tvshows.themoviedb.org/settings.xml")
            settings_data = filetools.read(path_settings)
            strSettings = ' '.join(settings_data.split()).replace("> <", "><")
            strSettings = strSettings.replace("\"", "\'")

            # update db
            nun_records, records = xbmc_videolibrary.execute_sql_kodi(
                'update path set strScraper="metadata.tvshows.themoviedb.org", strSettings="' + strSettings + '" where strPath like "' +
                filetools.join(config.get_setting('videolibrarypath'), config.get_setting('folder_tvshows')) +
                '%" and strScraper="metadata.tvdb.com"')

            # scan new info
            xbmc.executebuiltin('UpdateLibrary(video)')
            xbmc.executebuiltin('CleanLibrary(video)')
            while xbmc.getCondVisibility('Library.IsScanningVideo()'):
                xbmc.sleep(1000)

    # check if the user has any connection problems
    from platformcode.checkhost import test_conn
    run_threaded(test_conn, (True, not config.get_setting('resolver_dns'), True, [], [], True))

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

        if monitor.waitForAbort(1):  # every second
            # db need to be closed when not used, it will cause freezes
            db.close()
            break
