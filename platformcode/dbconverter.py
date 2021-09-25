# -*- coding: utf-8 -*-
import xbmc
from core import filetools, videolibrarytools
from core import videolibrarydb
from platformcode import config, logger, platformtools
from platformcode.xbmc_videolibrary import execute_sql_kodi, get_data, get_file_db
from time import time, strftime, localtime
import sqlite3

# conn = sqlite3.connect(get_file_db())
date = strftime('%Y-%m-%d %H:%M:%S', localtime(float(time())))

def save_all():
    movies = dict(videolibrarydb['movie'])
    tvshows = dict(videolibrarydb['tvshow'])
    videolibrarydb.close()

    for movie in movies.values():
        item = movie['item']
        item.no_reload = True
        add_video(item)
    for tvshow in tvshows.values():
        item = tvshow['item']
        item.no_reload = True
        add_video(item)
    # conn.close()

    reload()

def reload():
    movieid = get_id('idMovie', 'movie')
    showid = get_id('idShow', 'tvshow')
    payload = {"jsonrpc": "2.0",
               "method": "VideoLibrary.Scan",
               "id": 1}

    while xbmc.getCondVisibility('Library.IsScanningVideo()'): pass

    payload["directory"] = videolibrarytools.FOLDER_TVSHOWS
    get_data(payload)

    while xbmc.getCondVisibility('Library.IsScanningVideo()'): pass

    payload["directory"] = videolibrarytools.FOLDER_MOVIES
    get_data(payload)

    while xbmc.getCondVisibility('Library.IsScanningVideo()'): pass

    xbmc.executebuiltin('ReloadSkin()')


def add_video(item):
    global conn
    conn = sqlite3.connect(get_file_db())
    progress = platformtools.dialog_progress_bg('Sincronizzazione Libreria', item.title)
    progress.update(0)
    if item.contentType == 'movie':
        start = time()
        addMovie(item=item)
        logger.debug('TOTAL TIME:', time() - start)
    else:
        start = time()
        addTvShow(item=item)
        logger.debug('TOTAL TIME:', time() - start)
    videolibrarydb.close()
    conn.close()
    progress.close()


def get_path(item):
    logger.debug()
    p = item.strm_path if item.strm_path else item.nfo_path
    path = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)), p.split('\\')[0].split('/')[0])
    parent = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)))
    if item.contentType == 'movie':
        filepath = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)), p)
        file = item.strm_path.split('\\')[-1].split('/')[-1]
        return process_path(path), process_path(parent), file, filepath
    else:
        return process_path(path), process_path(parent)


def process_path(path):
    if '\\' in path: path += '\\'
    else: path += '/'
    return path


def get_id(column, table):
    sql = 'SELECT MAX({}) FROM {}'.format(column, table)
    nun_records, records = execute_sql_kodi(sql, conn=conn)
    if nun_records == 1: _id = records[0][0] + 1
    else: _id = 1
    return _id


def get_images(item):

    pstring = '<thumb aspect="{}" preview="{}">{}</thumb>'
    sstring = '<thumb aspect="{}" type="season" season="{}">{}</thumb>'
    fstring = '<thumb preview="{}">{}</thumb>'

    posters = ''
    fanarts = ''

    videoposters = [item.thumbnail] + item.infoLabels.get('posters',[])
    videofanarts = [item.fanart] + item.infoLabels.get('fanarts',[])
    videoclearlogos = item.infoLabels.get('clearlogos',[])
    videocleararts = item.infoLabels.get('cleararts',[])
    videolanscapes = item.infoLabels.get('lanscapes',[])
    videobanners = item.infoLabels.get('banners',[])
    videodiscs = item.infoLabels.get('discs',[])
    if item.contentType == 'season':
        for p in videoposters:
            if p: posters += sstring.format('poster', item.contentSeason, p)
        for p in videoclearlogos:
            if p: posters += sstring.format('clearlogo', item.contentSeason, p)
        for p in videocleararts:
            if p: posters += sstring.format('clearart', item.contentSeason, p)
        for p in videolanscapes:
            if p: posters += sstring.format('lanscape', item.contentSeason, p)
        for p in videobanners:
            if p: posters += sstring.format('banner', item.contentSeason, p)
        for p in videodiscs:
            if p: posters += sstring.format('disc', item.contentSeason, p)
    else:
        for p in videoposters:
            if p: posters += pstring.format('poster', p.replace('original', 'w500'), p)
        for p in videoclearlogos:
            if p: posters += pstring.format('clearlogo', '', p)
        for p in videocleararts:
            if p: posters += pstring.format('clearart', '', p)
        for p in videolanscapes:
            if p: posters += pstring.format('lanscape', '', p)
        for p in videobanners:
            if p: posters += pstring.format('banner', '', p)
        for p in videodiscs:
            if p: posters += pstring.format('disc', '', p)


    if item.infoLabels['setid']:
        collection = videolibrarydb['collection'].get(item.infoLabels['setid'], {})
        setposters = collection.infoLabels.get('posters',[])
        setfanarts = collection.infoLabels.get('fanarts',[])
        setclearlogos = collection.infoLabels.get('clearlogos',[])
        setcleararts = collection.infoLabels.get('cleararts',[])
        setlanscapes = collection.infoLabels.get('lanscapes',[])
        setbanners = collection.infoLabels.get('banners',[])
        setdiscs = collection.infoLabels.get('discs',[])

        for p in setposters:
            if p: posters += pstring.format('set.poster', p.replace('original', 'w500'), p)
        for p in setfanarts:
            if p: posters += pstring.format('set.fanart', p.replace('original', 'w500'), p)
        for p in setclearlogos:
            if p: posters += pstring.format('set.clearlogo', '', p)
        for p in setcleararts:
            if p: posters += pstring.format('set.clearart', '', p)
        for p in setlanscapes:
            if p: posters += pstring.format('set.lanscape', '', p)
        for p in setbanners:
            if p: posters += pstring.format('set.banner', '', p)
        for p in setdiscs:
            if p: posters += pstring.format('set.disc', '', p)



    if item.contentType != 'season':
        fanarts += '<fanart>'
        for f in videofanarts:
            if f: fanarts += fstring.format(f.replace('original', 'w780'), f)
        fanarts += '</fanart>'

    return posters, fanarts


def execute_sql(sql_actions):
        cursor = conn.cursor()
        for sql, params in sql_actions:
            try:
                if type(params) == list:
                    cursor.executemany(sql, params)
                else:
                    cursor.execute(sql, params)
            except:
                logger.error('Unable to run SQL\nSQL:', sql,'\nPARAMS:', params)
        conn.commit()


class addMovie(object):
    def __init__(self, *args, **kwargs):
        self.art = []
        self.item = kwargs.get('item', None)
        self.info = self.item.infoLabels
        self.videoExist, self.VideoId = self.get_id()
        self.message = ''
        self.sql_actions = []

        if not self.videoExist:
            logger.debug('Add {}: {} to Kodi Library'.format(self.item.contentType, self.item.title))
            self.strPath, self.parentPath, self.strFilename, self.path = get_path(self.item)

            self.set_path()
            self.set_sets()
            self.set_files()
            self.set_rating()
            self.set_ids()
            self.set_actors()
            self.set_info('country')
            self.set_info('genre')
            self.set_info('studio')
            self.set_movie()
            self.set_art()

            execute_sql(self.sql_actions)

            # need if no movie in kodi library
            if not self.item.no_reload:
                if self.VideoId == 1:
                    payload = {
                        "jsonrpc": "2.0",
                        "method": "VideoLibrary.Scan",
                        "directory": self.strPath,
                        "id": 1
                    }
                    get_data(payload)
                else:
                    xbmc.executebuiltin('ReloadSkin()')
                # conn.close()

    def get_id(self):
        Type = 'id' + self.item.contentType.replace('tv', '').capitalize()
        sql = 'select {} from {}_view where (uniqueid_value = "{}" and uniqueid_type = "kod")'.format(Type, self.item.contentType, self.item.videolibrary_id)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if nun_records: return True, records[0][0]

        sql = 'SELECT MAX({}) FROM {}_view'.format(Type, self.item.contentType)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if nun_records == 1: _id = records[0][0] + 1
        else: _id = 1
        return False, _id

    def set_path(self):
        sql = 'select idPath from path where (strPath = "{}") limit 1'.format(self.parentPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idParentPath = records[0][0]
        else:
            self.idParentPath = get_id('idPath', 'path')
            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, strContent, strScraper, noUpdate) VALUES ({}, "{}", "{}", "{}", {})'.format(self.idParentPath, self.parentPath, 'movies', 'meatadata.local', 0)
            nun_records, records = execute_sql_kodi(sql, conn=conn)

        sql = 'select idPath from path where (strPath = "{}") limit 1'.format(self.strPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idPath = records[0][0]
        else:
            self.idPath = get_id('idPath', 'path')

            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, dateAdded, idParentPath, noUpdate) VALUES ( ?,  ?,  ?,  ?, ?)'
            params = (self.idPath, self.strPath, date, self.idParentPath, 1)
            self.sql_actions.append([sql, params])

    def set_sets(self):
        self.idSet = None
        if self.info.get('set'):
            sql = 'SELECT idSet from sets where (strSet = "{}") limit 1'.format(self.info.get('set'))
            collection_info = videolibrarydb['collection'][self.info.get('setid')].infoLabels
            logger.debug('COLLECTION INFO:',collection_info)
            nun_records, records = execute_sql_kodi(sql, conn=conn)
            if records:
                self.idSet = records[0][0]
            else:
                self.idSet = get_id('idSet', 'sets')
                sql = 'INSERT OR IGNORE INTO sets (idSet, strSet, strOvervieW) VALUES ( ?,  ?,  ?)'
                params = (self.idSet, self.info.get('set'), self.info.get('setoverview'))
                self.sql_actions.append([sql, params])
                if collection_info.get('posters'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set', 'type':'poster', 'url':collection_info.get('posters')[0]})
                if collection_info.get('fanarts'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'fanart', 'url':collection_info.get('fanarts')[0]})
                if collection_info.get('landscapes'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'landscape', 'url':collection_info.get('landscapes')[0]})
                if collection_info.get('banners'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'banner', 'url':collection_info.get('banners')[0]})
                if collection_info.get('clearlogos'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearlogo', 'url':collection_info.get('clearlogos')[0]})
                if collection_info.get('cleararts'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearart', 'url':collection_info.get('cleararts')[0]})
                if collection_info.get('discs'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearart', 'url':collection_info.get('discs')[0]})

    def set_files(self):
        self.idFile = get_id('idFile', 'files')
        if self.info.get('playcount', None):
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, playCount, lastPlayed, dateAdded) VALUES ( ?,  ?,  ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, self.info.get('playcount', None), self.item.lastplayed, date)
        else:
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, dateAdded) VALUES ( ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, date)
        self.sql_actions.append([sql, params])

    def set_rating(self):
        self.rating_id = get_id('rating_id', 'rating')
        rating = self.info.get('rating', None)
        votes = self.info.get('votes', None)
        media_type = self.item.contentType
        sql = 'INSERT OR IGNORE INTO rating (rating_id, media_id, media_type, rating_type, rating, votes) VALUES ( ?,  ?,  ?, ?,  ?,  ?)'
        params = (self.rating_id, self.VideoId, media_type, 'tmdb', rating, votes)
        self.sql_actions.append([sql, params])

    def set_ids(self):
        self.uniqueID = get_id('uniqueid_id', 'uniqueid')
        self.uniqueIdValue = self.item.videolibrary_id
        self.uniqueIDType = 'kod'
        sql = 'INSERT OR IGNORE INTO uniqueid (uniqueid_id, media_id, media_type, value, type) VALUES ( ?,  ?,  ?,  ?,  ?)'
        params = [(self.uniqueID, self.VideoId, self.item.contentType, self.uniqueIdValue, self.uniqueIDType)]

        i = self.uniqueID + 1

        for _id in ['imdb', 'tmdb', 'tvdb']:
            if _id +'_id' in self.info:
                params.append((i, self.VideoId, self.item.contentType, self.info[_id + '_id'], _id))
                i += 1
        self.sql_actions.append([sql, params])

    def set_actors(self):
        actors = self.info.get('castandrole', [])
        if actors: actors.sort(key=lambda a: a[3])
        actor_params = []
        actor_link_params = []
        director_link_params = []
        writer_params = []
        writer_link_params = []
        directors = self.info.get('director', '').split(', ')
        directors_image = self.info.get('director_image', [])
        if not directors_image: directors_image = ['' for d in directors]
        writers = self.info.get('writer', '').split(', ')
        writers_image = self.info.get('writer_image', [])
        if not writers_image: writers_image = ['' for w in writers]

        actor_sql = 'INSERT OR IGNORE INTO actor (name, art_urls) VALUES (?, ?)'
        actor_link_sql = 'INSERT OR IGNORE INTO actor_link (actor_id, media_id, media_type, role, cast_order) VALUES (?, ?, ?, ?, ?)'
        for actor in actors:
            actor_params.append((actor[0], actor[2]))
        for d, director in enumerate(directors):
            actor_params.append((director, directors_image[d]))
        for w, writer in enumerate(writers):
            actor_params.append((writer, writers_image[w]))

        if actor_params:
            nun_records, records = execute_sql_kodi(actor_sql, actor_params, conn)

        for actor in actors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(actor[0]))[1][0][0]
            actor_link_params.append((actor_id, self.VideoId, self.item.contentType, actor[1], actor[3]))
            if actor[2]:
                self.art.append({'media_id': actor_id, 'media_type': 'actor', 'type': 'thumb', 'url': actor[2]})

        for director in directors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(director))[1][0][0]
            director_link_params.append((actor_id, self.VideoId, self.item.contentType))

        for writer in writers:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(writer))[1][0][0]
            writer_link_params.append((actor_id, self.VideoId, self.item.contentType))

        if actor_link_params:
            self.sql_actions.append([actor_link_sql, actor_link_params])
        if director_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, director_link_params])

        if writer_params:
            self.sql_actions.append([actor_sql, writer_params])
        if writer_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, writer_link_params])

    def set_info(self, info_name):
        info_list = self.info.get(info_name, '').split(', ')
        if info_list:
            sql = 'INSERT OR IGNORE INTO {} (name) VALUES (?)'.format(info_name)
            params = [(info,) for info in info_list]
            nun_records, records = execute_sql_kodi(sql, params, conn)
            sql = 'INSERT OR IGNORE INTO {}_link ({}_id, media_id, media_type) VALUES (?, ?, ?)'.format(info_name, info_name)
            params = [(execute_sql_kodi('select {}_id from {} where name = "{}" limit 1'.format(info_name, info_name, info))[1][0][0],
                       self.VideoId, self.item.contentType) for info in info_list]
            self.sql_actions.append([sql, params])

    def set_movie(self):
        posters, fanarts = get_images(self.item)
        sql = 'INSERT OR IGNORE INTO movie (idMovie, idFile, c00, c01, c03, c05, c06, c08, c09, c11, c12, c14, c15, c16, c18, c19, c20, c21, c22, c23, idSet, premiered)'
        sql += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        params = (self.VideoId, # idMovie
                  self.idFile, # idFile
                  self.item.title, # c00
                  self.item.plot.replace('"', "'"), # c01
                  self.info.get('tagline'), # c03
                  self.rating_id, # c05
                  self.info.get('writer','').replace(',', ' /'), # c06
                  posters, # c08
                  self.uniqueID, #c09
                  self.info.get('duration', 0), # c11
                  self.info.get('mpaa'), # c12
                  self.info.get('genre','').replace(',', ' /') if self.info.get('genre') else None, # c14
                  self.info.get('director','').replace(',', ' /') if self.info.get('director') else None, # c15
                  self.info.get('originaltitle'), # c16
                  self.info.get('studio'), # c18
                  self.info.get('trailer'), # c19
                  fanarts, # c20
                  self.info.get('country','').replace(',', ' /') if self.info.get('country') else None, # c21
                  self.path, # c22
                  self.idPath, # c23
                  self.idSet, # idSet
                  self.info.get('premiered')) # premiered

        if self.item.thumbnail:
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie', 'type':'poster', 'url':self.item.thumbnail})
        if self.item.fanart:
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'fanart', 'url':self.item.fanart})
        if self.info.get('landscape'):
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'landscape', 'url':self.info.get('landscape')})
        if self.info.get('banner'):
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'banner', 'url':self.info.get('banner')})
        if self.info.get('clearlogo'):
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'clearlogo', 'url':self.info.get('clearlogo')})
        if self.info.get('clearart'):
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'clearart', 'url':self.info.get('clearart')})
        if self.info.get('disc'):
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'disc', 'url':self.info.get('disc')})

        self.sql_actions.append([sql, params])

    def set_art(self):
        params = []
        art_urls = []
        _id = get_id('art_id', 'art')
        arts = execute_sql_kodi('select media_id, media_type, type from art', conn=conn)[1]
        if arts:
            art_urls = [[u[0], u[1], u[2]] for u in arts]
        for art in self.art:
            if [art ['media_id'], art['media_type'], art['type']] not in art_urls:
                params.append((_id, art['media_id'], art['media_type'], art['type'], art['url']))
                _id += 1
        if params:
            sql = 'INSERT OR IGNORE INTO art (art_id, media_id, media_type, type, url) VALUES (?, ?, ?, ?, ?)'
            self.sql_actions.append([sql, params])


class addTvShow(object):
    def __init__(self, *args, **kwargs):
        self.art = []
        self.sql_actions = []
        self.posters = ''
        self.fanarts = ''
        self.item = kwargs.get('item', None)
        self.info = self.item.infoLabels
        self.seasons = videolibrarydb['season'][self.item.videolibrary_id]
        self.episodes = videolibrarydb['episode'][self.item.videolibrary_id]
        self.imdb_id = self.info.get('imdb_id', '')
        self.tmdb_id = self.info.get('tmdb_id', '')
        self.tvdb_id = self.info.get('tvdb_id', '')
        self.exist, self.idShow = self.get_idShow()
        self.idSeasons = self.get_idSeasons()
        self.idEpisodes = self.get_idEpisodes()
        self.strPath, self.parentPath = get_path(self.item)
        logger.debug('Add {}: {} to Kodi Library'.format(self.item.contentType, self.item.title))

        self.set_path()
        self.set_files()
        self.set_rating()
        self.set_ids()
        self.set_season()
        self.set_actors()
        self.set_episode_actors()
        self.set_info('country')
        self.set_info('genre')
        self.set_info('studio')
        self.set_tvshow()
        self.set_episodes()
        self.set_art()

        execute_sql(self.sql_actions)

        # need if no movie in kodi library
        if not self.item.no_reload:
            if self.idShow == 1:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "VideoLibrary.Scan",
                    "directory": self.strPath,
                    "id": 1
                }
                get_data(payload)
            else:
                xbmc.executebuiltin('ReloadSkin()')
            # conn.close()

    def get_idShow(self):
        sql = 'select idShow from tvshow_view where uniqueid_value = {} and uniqueid_type = "kod"'.format(self.info['tmdb_id'])
        n, records = execute_sql_kodi(sql)
        if n: return True, records[0][0]
        else: return False, get_id('idShow', 'tvshow_view')

    def get_idSeasons(self):
        r = {}
        sql = 'select idSeason, season from seasons_view where idShow = {}'.format(self.idShow)
        n, records = execute_sql_kodi(sql)
        maxId = get_id('idSeason', 'seasons')

        if n:
            seasons = [s[1] for s in records]
            for season in self.seasons.keys():
                if season.contentSeason not in seasons:
                    r[season] = maxId
                    self.get_season_images(season, maxId)
                    maxId += 1
        else:
            for season in self.seasons:
                r[season] = maxId
                self.get_season_images(season, maxId)
                maxId += 1
        return r

    def get_season_images(self, season, _id):
        item = self.seasons[season]
        posters, fanarts = get_images(item)
        self.posters += posters

        if item.thumbnail:
            self.art.append({'media_id':_id, 'media_type': 'season', 'type':'poster', 'url':item.thumbnail})
        if item.fanart:
            self.art.append({'media_id':_id, 'media_type': 'season',  'type':'fanart', 'url':item.fanart})
        if item.landscape:
            self.art.append({'media_id':_id, 'media_type': 'season',  'type':'landscape', 'url':item.landscape})
        if item.banner:
            self.art.append({'media_id':_id, 'media_type': 'season',  'type':'banner', 'url':item.banner})
        if item.clearlogo:
            self.art.append({'media_id':_id, 'media_type': 'season',  'type':'clearlogo', 'url':item.clearlogo})
        if item.clearart:
            self.art.append({'media_id':_id, 'media_type': 'season',  'type':'clearart', 'url':item.clearart})

    def get_idEpisodes(self):
        sql = 'select idEpisode, c12, c13 from episode_view where idShow = {}'.format(self.idShow)
        n, records = execute_sql_kodi(sql)
        r = {}
        episodes = [v['item'] for v in videolibrarydb['episode'][self.item.videolibrary_id].values()]
        maxId = get_id('idEpisode', 'episode_view')
        if n:
            record_episodes = ['{}x{:02d}'.format(int(s[1]), int(s[2])) for s in records]
            for episode in episodes:
                e = '{}x{:02d}'.format(episode.contentSeason, episode.contentEpisodeNumber)
                if e not in record_episodes:
                    r[e] = maxId
                    maxId += 1

        else:
            for episode in episodes:
                e = '{}x{:02d}'.format(episode.contentSeason, episode.contentEpisodeNumber)
                r[e] = maxId
                maxId += 1
        return r

    def set_path(self):
        sql = 'select idPath from path where (strPath = "{}") limit 1'.format(self.parentPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idParentPath = records[0][0]
        else:
            self.idParentPath = get_id('idPath', 'path')
            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, strContent, strScraper, noUpdate) VALUES ({}, "{}", "{}", "{}", {})'.format(self.idParentPath, self.parentPath, 'tvshows', 'meatadata.local', 0)
            nun_records, records = execute_sql_kodi(sql, conn=conn)

        sql = 'select idPath from path where (strPath = "{}") limit 1'.format(self.strPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idPath = records[0][0]
        else:
            self.idPath = get_id('idPath', 'path')

            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, dateAdded, idParentPath, noUpdate) VALUES (?,  ?,  ?,  ?, ?)'
            params = (self.idPath, self.strPath, date, self.idParentPath, 1)
            self.sql_actions.append([sql, params])

            sql = 'INSERT OR IGNORE INTO tvshowlinkpath (idShow, idPath) VALUES (?,  ?)'
            params = (self.idShow, self.idPath)
            self.sql_actions.append([sql, params])

    def set_files(self):
        files = {}
        sql = 'select idFile, strFilename from files where idPath={}'.format(self.idPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            files = {r[1].replace('.strm',''):r[0] for r in records}
        self.idFiles = {}
        idFile = get_id('idFile', 'files')
        # support.dbg()
        for episode in self.idEpisodes.keys():
            if episode in files.keys():
                self.idFiles[episode] = files[episode]
                sql = 'update files set playCount= {} where idFile= {}'.format(self.episodes[episode]['item'].infoLabels.get('playcount', None), files[episode])
                self.sql_actions.append([sql, ''])
            else:
                if self.episodes[episode]['item'].infoLabels.get('playcount', None):
                    sql = 'INSERT INTO files (idFile, idPath, strFilename, playCount, lastPlayed, dateAdded) VALUES ( ?,  ?,  ?,  ?,  ?,  ?)'
                    params = (idFile, self.idPath, episode + '.strm', self.episodes[episode]['item'].infoLabels.get('playcount', None), self.item.lastplayed, date)
                else:
                    sql = 'INSERT INTO files (idFile, idPath, strFilename, dateAdded) VALUES ( ?,  ?,  ?,  ?)'
                    params = (idFile, self.idPath, episode + '.strm', date)
                self.idFiles[episode] = idFile
                idFile += 1
                self.sql_actions.append([sql, params])

    def set_rating(self):
        self.rating_id = get_id('rating_id', 'rating')
        if not self.exist:
            rating = self.info.get('rating', None)
            votes = self.info.get('votes', None)
            sql = 'INSERT OR IGNORE INTO rating (rating_id, media_id, media_type, rating_type, rating, votes) VALUES ( ?,  ?,  ?, ?,  ?,  ?)'
            params = (self.rating_id, self.idShow, 'tvshow', 'tmdb', rating, votes)
            self.sql_actions.append([sql, params])

        self.episodes_rating_id = {}
        rating_id = self.rating_id
        if not self.exist: rating_id += 1
        for episode, _id in self.idEpisodes.items():
            item = self.episodes[episode]['item']
            info = item.infoLabels
            rating = info.get('rating', None)
            votes = info.get('votes', None)
            sql = 'INSERT OR IGNORE INTO rating (rating_id, media_id, media_type, rating_type, rating, votes) VALUES ( ?,  ?,  ?, ?,  ?,  ?)'
            params = (rating_id, self.idShow, 'episode', 'tmdb', rating, votes)
            self.sql_actions.append([sql, params])
            self.episodes_rating_id[episode] = _id

    def set_ids(self):
        self.uniqueIDs = {}
        uniqueID = get_id('uniqueid_id', 'uniqueid')
        self.uniqueID = uniqueID
        if not self.exist:
            sql = 'INSERT OR IGNORE INTO uniqueid (uniqueid_id, media_id, media_type, value, type) VALUES ( ?,  ?,  ?,  ?,  ?)'
            params = [(uniqueID, self.idShow, 'tvshow', self.item.videolibrary_id, 'kod')]

            uniqueID += 1

            for _id in ['imdb', 'tmdb', 'tvdb']:
                if _id +'_id' in self.info:
                    params.append((uniqueID, self.idShow, 'tvshow', self.info[_id + '_id'], _id))
                    uniqueID += 1
            self.sql_actions.append([sql, params])

        for episode, _id in self.idEpisodes.items():
            item = self.episodes[episode]['item']
            info = item.infoLabels
            sql = 'INSERT OR IGNORE INTO uniqueid (uniqueid_id, media_id, media_type, value, type) VALUES ( ?,  ?,  ?,  ?,  ?)'
            params = [(uniqueID, _id, 'episode', info['episode_id'], 'kod')]
            self.uniqueIDs[episode] = uniqueID
            uniqueID += 1

            for t in ['imdb', '', 'tvdb']:
                if 'episode{}_id'.format(t) in self.info:
                    params.append((uniqueID, t, 'episode', self.info[t + 'episode{}_id'.format(t)], t if t else 'tmdb'))
                    uniqueID += 1
            self.sql_actions.append([sql, params])

    def set_season(self):
        sql = 'INSERT OR IGNORE INTO seasons (idSeason, idShow, season, name) VALUES ( ?,  ?,  ?,  ?)'
        params = []
        for season, _id in self.idSeasons.items():
            item = self.seasons[season]
            name = item.title
            params.append((_id, self.idShow, season, name))
        self.sql_actions.append([sql, params])

    def set_actors(self):
        actors = self.info.get('castandrole', [])
        if actors: actors.sort(key=lambda a: a[3])
        actor_params = []
        actor_link_params = []
        director_link_params = []
        writer_params = []
        writer_link_params = []
        directors = self.info.get('director', '').split(', ')
        directors_image = self.info.get('director_image', [])
        if not directors_image: directors_image = ['' for d in directors]
        writers = self.info.get('writer', '').split(', ')
        writers_image = self.info.get('writer_image',[])
        if not writers_image: writers_image = ['' for w in writers]

        actor_sql = 'INSERT OR IGNORE INTO actor (name, art_urls) VALUES (?, ?)'
        actor_link_sql = 'INSERT OR IGNORE INTO actor_link (actor_id, media_id, media_type, role, cast_order) VALUES (?, ?, ?, ?, ?)'
        for actor in actors:
            actor_params.append((actor[0], actor[2]))
        for d, director in enumerate(directors):
            actor_params.append((director, directors_image[d]))
        for w, writer in enumerate(writers):
            actor_params.append((writer, writers_image[w]))

        if actor_params:
            nun_records, records = execute_sql_kodi(actor_sql, actor_params, conn)

        for actor in actors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(actor[0]))[1][0][0]
            actor_link_params.append((actor_id, self.idShow, 'tvshow', actor[1], actor[3]))
            if actor[2]:
                self.art.append({'media_id': actor_id, 'media_type': 'actor', 'type': 'thumb', 'url': actor[2]})

        for director in directors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(director))[1][0][0]
            director_link_params.append((actor_id, self.idShow, 'tvshow'))

        for writer in writers:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(writer))[1][0][0]
            writer_link_params.append((actor_id, self.idShow, 'tvshow'))

        if actor_link_params:
            self.sql_actions.append([actor_link_sql, actor_link_params])
        if director_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, director_link_params])

        if writer_params:
            self.sql_actions.append([actor_sql, writer_params])
        if writer_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, writer_link_params])

    def set_episode_actors(self):
        actors = []
        directors = []
        directors_image = []
        writers = []
        writers_image = []

        for ep in self.episodes.values():
            info = ep['item'].infoLabels
            actors += info.get('castandrole', [])
            directors += self.info.get('director', '').split(', ')
            directors_image += self.info.get('director_image') if self.info.get('director_image') else ['' for d in directors]
            writers += self.info.get('writer', '').split(', ')
            writers_image += self.info.get('writer_image') if self.info.get('writer_image') else ['' for w in writers]

        if actors: actors.sort(key=lambda a: a[3])
        actor_params = []
        actor_link_params = []
        director_link_params = []
        writer_params = []
        writer_link_params = []


        actor_sql = 'INSERT OR IGNORE INTO actor (name, art_urls) VALUES (?, ?)'
        actor_link_sql = 'INSERT OR IGNORE INTO actor_link (actor_id, media_id, media_type, role, cast_order) VALUES (?, ?, ?, ?, ?)'
        for actor in actors:
            actor_params.append((actor[0], actor[2]))
        for d, director in enumerate(directors):
            actor_params.append((director, directors_image[d]))
        for w, writer in enumerate(writers):
            actor_params.append((writer, writers_image[w]))

        if actor_params:
            nun_records, records = execute_sql_kodi(actor_sql, actor_params, conn)

        for actor in actors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(actor[0]))[1][0][0]
            actor_link_params.append((actor_id, self.idShow, 'episode', actor[1], actor[3]))
            if actor[2]:
                self.art.append({'media_id': actor_id, 'media_type': 'actor', 'type': 'thumb', 'url': actor[2]})

        for director in directors:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(director))[1][0][0]
            director_link_params.append((actor_id, self.idShow, 'episode'))

        for writer in writers:
            actor_id = execute_sql_kodi('select actor_id from actor where name="{}" limit 1'.format(writer))[1][0][0]
            writer_link_params.append((actor_id, self.idShow, 'episode'))

        if actor_link_params:
            self.sql_actions.append([actor_link_sql, actor_link_params])
        if director_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, director_link_params])

        if writer_params:
            self.sql_actions.append([actor_sql, writer_params])
        if writer_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            self.sql_actions.append([sql, writer_link_params])

    def set_info(self, info_name):
        info_list = self.info.get(info_name, '').split(', ')
        if info_list:
            sql = 'INSERT OR IGNORE INTO {} (name) VALUES (?)'.format(info_name)
            params = [(info,) for info in info_list]
            nun_records, records = execute_sql_kodi(sql, params, conn)
            sql = 'INSERT OR IGNORE INTO {}_link ({}_id, media_id, media_type) VALUES (?, ?, ?)'.format(info_name, info_name)
            params = [(execute_sql_kodi('select {}_id from {} where name = "{}" limit 1'.format(info_name, info_name, info))[1][0][0],
                       self.idShow, self.item.contentType) for info in info_list]
            self.sql_actions.append([sql, params])

    def set_tvshow(self):
        posters, fanarts = get_images(self.item)
        self.posters += posters
        self.fanarts += fanarts
        sql = 'INSERT OR IGNORE INTO tvshow (idShow, c00, c01, c02, c04, c05, c06, c08, c09, c11, c12, c13, c14, c16)'
        sql += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        params = (self.idShow, # idShow
                  self.item.title, # c00
                  self.item.plot, # c01
                  self.info.get('status'), # c02
                  self.rating_id, # c04
                  self.info.get('premiered'), # c05
                  self.posters, # c06
                  self.info.get('genre','').replace(',', ' /') if self.info.get('genre') else None, # c08
                  self.info.get('originaltitle'), # c09
                  self.fanarts, # c11
                  self.uniqueID, #c12
                  self.info.get('mpaa'), # c13
                  self.info.get('studio'), # c14
                  self.info.get('trailer'), # c16
                 )

        if self.item.thumbnail:
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow', 'type':'poster', 'url':self.item.thumbnail})
        if self.item.fanart:
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'fanart', 'url':self.item.fanart})
        if self.info.get('landscape'):
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'landscape', 'url':self.info.get('landscape')})
        if self.info.get('banner'):
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'banner', 'url':self.info.get('banner')})
        if self.info.get('clearlogo'):
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'clearlogo', 'url':self.info.get('clearlogo')})
        if self.info.get('clearart'):
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'clearart', 'url':self.info.get('clearart')})
        if self.info.get('disc'):
            self.art.append({'media_id':self.idShow, 'media_type': 'tvshow',  'type':'disc', 'url':self.info.get('disc')})

        self.sql_actions.append([sql, params])

    def set_episodes(self):
        params = []
        sql = 'INSERT OR IGNORE INTO episode (idEpisode, idFile, c00, c01, c03, c04, c05, c06, c10, c12, c13, c14, c15, c16, c17, c18, c19, c20, idShow, idSeason)'
        sql += 'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        for episode, _id in sorted(self.idEpisodes.items()):
            item = self.episodes[episode]['item']
            info = item.infoLabels
            params.append((_id, # idEpisode
                           self.idFiles[episode], # idFile
                           item.title, # c00
                           info['plot'], # c01
                           self.episodes_rating_id[episode], # c03
                           info.get('writer'), # c04
                           info.get('aired'), # c05
                           '<thumb>{}</thumb>'.format(info.get('poster_path')), # c06
                           info.get('director'), # c10
                           info.get('season'), # c12
                           info.get('episode'), # c13
                           info.get('originaltitle'), # c14
                           -1, -1, -1, # c15 c16, c17
                           '{}{}.strm'.format(self.strPath, episode), # c18
                           self.idPath, # c19
                           self.uniqueIDs[episode], # 20
                           self.idShow, # idShow
                           self.idSeasons[info.get('season')]
            ))

            self.art.append({'media_id':_id, 'media_type': 'episode', 'type':'thumb', 'url':info.get('poster_path')})

        self.sql_actions.append([sql, params])

    def set_art(self):
        params = []
        art_urls = []
        _id = get_id('art_id', 'art')
        arts = execute_sql_kodi('select media_id, media_type, type from art', conn=conn)[1]
        if arts:
            art_urls = [[u[0], u[1], u[2]] for u in arts]
        for art in self.art:
            if [art['media_id'], art['media_type'], art['type']] not in art_urls:
                params.append((_id, art['media_id'], art['media_type'], art['type'], art['url']))
                _id += 1
        if params:
            sql = 'INSERT OR IGNORE INTO art (art_id, media_id, media_type, type, url) VALUES (?, ?, ?, ?, ?)'
            self.sql_actions.append([sql, params])













