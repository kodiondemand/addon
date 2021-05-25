# -*- coding: utf-8 -*-
import xbmc, os, math
from core import filetools, support
from core.videolibrarydb import videolibrarydb
from platformcode import config, logger, platformtools
from platformcode.xbmc_videolibrary import execute_sql_kodi, get_data, get_file_db
from time import time, strftime, localtime
import sqlite3

conn = sqlite3.connect(get_file_db())


class addVideo(object):
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
            self.date = strftime('%Y-%m-%d %H:%M:%S', localtime(float(time())))


            if self.item.contentType == 'movie':
                self.set_path()
                self.set_sets()
            self.set_files()
            self.set_rating()
            self.set_ids()
            self.set_actors()
            self.set_info('country')
            self.set_info('genre')
            self.set_info('studio')

            if self.item.contentType == 'movie': self.set_movie()
            elif self.item.contentType == 'tvshow': self.set_tvshow()
            elif self.item.contentType == 'season': self.set_season()
            else: self.set_episode()

            self.set_art()

            cursor = conn.cursor()
            for sql, params in self.sql_actions:
                if type(params) == list:
                    cursor.executemany(sql, params)
                else:
                    cursor.execute(sql, params)
            conn.commit()

            # need if no movie in kodi library
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
        conn.close()

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
            return

        sql = 'select idPath from path where (strPath = "{}") limit 1'.format(self.strPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idPath = records[0][0]
        else:
            self.idPath = get_id('idPath', 'path')

            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, dateAdded, idParentPath, noUpdate) VALUES ( ?,  ?,  ?,  ?, ?)'
            params = (self.idPath, self.strPath, self.date, self.idParentPath, 1)
            self.sql_actions.append([sql, params])

    def set_sets(self):
        self.idSet = None
        if self.info.get('set'):
            sql = 'SELECT idSet from sets where (strSet = "{}") limit 1'.format(self.info.get('set'))
            collection_info = videolibrarydb['collection'][self.info.get('setid')].infoLabels
            nun_records, records = execute_sql_kodi(sql, conn=conn)
            if records:
                self.idSet = records[0][0]
            else:
                self.idSet = get_id('idSet', 'sets')
                sql = 'INSERT OR IGNORE INTO sets (idSet, strSet, strOvervieW) VALUES ( ?,  ?,  ?)'
                params = (self.idSet, self.info.get('set'), self.info.get('setoverview'))
                self.sql_actions.append([sql, params])
                if collection_info.get('poster'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set', 'type':'poster', 'url':collection_info.get('poster')})
                if collection_info.get('fanart'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'fanart', 'url':collection_info.get('fanart')})
                if collection_info.get('landscape'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'landscape', 'url':collection_info.get('landscape')})
                if collection_info.get('banner'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'banner', 'url':collection_info.get('banner')})
                if collection_info.get('clearlogo'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearlogo', 'url':collection_info.get('clearlogo')})
                if collection_info.get('clearart'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearart', 'url':collection_info.get('clearart')})
                if collection_info.get('disc'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'clearart', 'url':collection_info.get('disc')})

    def set_files(self):
        self.idFile = get_id('idFile', 'files')
        if self.item.playcount:
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, playCount, lastPlayed, dateAdded) VALUES ( ?,  ?,  ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, self.item.playcount, self.item.lastplayed, self.date)
        else:
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, dateAdded) VALUES ( ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, self.date)
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
        directors_image = self.info.get('director_image', ['' for d in directors])
        writers = self.info.get('writer', '').split(', ')
        writers_image = self.info.get('writer_image', ['' for w in writers])

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



    def set_tvshow(self):
        posters, fanarts = get_images(self.item)
        sql = 'INSERT OR IGNORE INTO tvshow (idMovie, idFile, c00, c01, c03, c05, c06, c08, c09, c11, c12, c14, c15, c16, c18, c19, c20, c21, c22, c23, idSet, premiered)'
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
        nun_records, records = execute_sql_kodi(sql, params, conn)

    def set_art(self):
        params = []
        art_urls = []
        _id = get_id('art_id', 'art')
        art_urls = [[u[0], u[1], u[2]] for u in execute_sql_kodi('select media_id, media_type, type from art', conn=conn)[1]]
        for art in self.art:
            if [art ['media_id'], art['media_type'], art['type']] not in art_urls:
                params.append((_id, art['media_id'], art['media_type'], art['type'], art['url']))
                _id += 1
        if params:
            sql = 'INSERT OR IGNORE INTO art (art_id, media_id, media_type, type, url) VALUES (?, ?, ?, ?, ?)'
            self.sql_actions.append([sql, params])


def add_video(item):
    if item.contentType == 'movie':
        start = time()
        addVideo(item=item)
        logger.debug('TOTAL TIME:', time() - start)
    else:
        i = 0
        seasons = videolibrarydb['season'][item.videolibrary_id]
        episodes = videolibrarydb['episode'][item.videolibrary_id]
        t = len(seasons) + len(episodes) + 1
        # progress = platformtools.dialog_progress_bg('Sincronizzazione Libreria', item.title)
        # progress.update(0)
        addVideo(item=item)
        # progress.update(int(math.ceil((i + 1) * t)))
        for season in seasons:
            addVideo(item=season)
            # progress.update(int(math.ceil((i + 1) * t)))
        for episode in episodes:
            addVideo(item=episode['item'])
            # progress.update(int(math.ceil((i + 1) * t)))
        # progress.close()

def get_path(item):
    filepath = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)), item.strm_path)
    path = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)), item.strm_path.split('\\')[0].split('/')[0])
    parent = filetools.join(config.get_videolibrary_config_path(), config.get_setting("folder_{}s".format(item.contentType)))
    file = item.strm_path.split('\\')[-1].split('/')[-1]
    return process_path(path), process_path(parent), file, filepath

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




    fanarts += '<fanart>'
    for f in videofanarts:
        if f: fanarts += fstring.format(f.replace('original', 'w780'), f)
    fanarts += '</fanart>'

    return posters, fanarts