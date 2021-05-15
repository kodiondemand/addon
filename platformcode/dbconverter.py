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

        if not self.videoExist:
            logger.debug('Add {}: {} to Kodi Library'.format(self.item.contentType, self.item.title))
            self.strPath, self.parentPath, self.strFilename, self.path = get_path(self.item)
            self.date = strftime('%Y-%m-%d %H:%M:%S', localtime(float(time())))
            ini = start = time()
            self.set_path()
            self.message += 'path:{}'.format(time() - start)
            start = time()
            self.set_sets()
            self.message += ', sets:{}'.format(time() - start)
            start = time()
            self.set_files()
            self.message += ', files:{}'.format(time() - start)
            start = time()
            self.set_rating()
            self.message += ', rating:{}'.format(time() - start)
            start = time()
            self.set_ids()
            self.message += ', ids:{}'.format(time() - start)
            start = time()
            self.set_actors()
            self.message += ', actors:{}'.format(time() - start)
            start = time()
            self.set_country()
            self.message += ', country:{}'.format(time() - start)
            start = time()
            self.set_genre()
            self.message += ', genre:{}'.format(time() - start)
            start = time()
            self.set_studio()
            self.message += ', studio:{}'.format(time() - start)
            start = time()
            if self.item.contentType == 'movie': self.set_movie()
            elif self.item.contentType == 'tvshow': self.set_tvshow()
            elif self.item.contentType == 'season': self.set_season()
            else: self.set_episode()
            self.message += ', video:{}'.format(time() - start)
            start = time()
            self.set_art()
            self.message += ', art:{}'.format(time() - start)
            # platformtools.dialog_ok('',self.message)
            logger.debug('TEMPO TOTALE:',time() - ini, self.message)
            payload = {
                "jsonrpc": "2.0",
                "method": "VideoLibrary.Scan",
                "directory": self.strPath,
                "id": 1
            }
            get_data(payload)
        
        conn.close()

    def get_id(self):
        Type = 'id' + self.item.contentType.replace('tv','').capitalize()
        sql = 'select {} from {}_view where (uniqueid_value like "{}" and uniqueid_type like "kod")'.format(Type, self.item.contentType, self.item.videolibrary_id)
        n, records = execute_sql_kodi(sql, conn=conn)
        if n: return True, records[0][0]

        sql = 'SELECT MAX({}) FROM {}_view'.format(Type, self.item.contentType)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if nun_records == 1: _id = records[0][0] + 1
        else: _id = 1
        return False, _id

    def set_path(self):
        sql = 'select idPath from path where (strPath like "{}")'.format(self.parentPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idParentPath = records[0][0]
        else:
            return

        sql = 'select idPath from path where (strPath like "{}")'.format(self.strPath)
        nun_records, records = execute_sql_kodi(sql, conn=conn)
        if records:
            self.idPath = records[0][0]
        else:
            self.idPath = get_id('idPath', 'path')

            sql = 'INSERT OR IGNORE INTO path (idPath, strPath, dateAdded, idParentPath, noUpdate) VALUES ( ?,  ?,  ?,  ?, ?)'
            params = (self.idPath, self.strPath, self.date, self.idParentPath, 1)
            n, records = execute_sql_kodi(sql, params, conn)

    def set_sets(self):
        self.idSet = None
        if self.info.get('set'):
            sql = 'SELECT idSet from sets where (strSet like "{}")'.format(self.info.get('set'))
            # params = self.info.get('set')
            n, records = execute_sql_kodi(sql, conn=conn)
            if records:
                self.idSet = records[0][0]
            else:
                self.idSet = get_id('idSet', 'sets')
                sql = 'INSERT OR IGNORE INTO sets (idSet, strSet, strOvervieW) VALUES ( ?,  ?,  ?)'
                params = (self.idSet, self.info.get('set'), self.info.get('setoverview'))
                n, records = execute_sql_kodi(sql, params, conn)
                if self.info.get('setposters'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set', 'type':'poster', 'url':self.info.get('setposters')[0]})
                if self.info.get('setfanarts'):
                    self.art.append({'media_id':self.idSet, 'media_type': 'set',  'type':'fanart', 'url':self.info.get('setfanarts')[0]})

    def set_files(self):
        self.idFile = get_id('idFile', 'files')
        if self.item.playcount:
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, playCount, lastPlayed, dateAdded) VALUES ( ?,  ?,  ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, self.item.playcount, self.item.lastplayed, self.date)
        else:
            sql = 'INSERT OR IGNORE INTO files (idFile, idPath, strFilename, dateAdded) VALUES ( ?,  ?,  ?,  ?)'
            params = (self.idFile, self.idPath, self.strFilename, self.date)
        n, records = execute_sql_kodi(sql, params, conn)

    def set_rating(self):
        self.rating_id = get_id('rating_id', 'rating')
        rating = self.info.get('rating', None)
        votes = self.info.get('votes', None)
        media_type = self.item.contentType
        sql = 'INSERT OR IGNORE INTO rating (rating_id, media_id, media_type, rating_type, rating, votes) VALUES ( ?,  ?,  ?, ?,  ?,  ?)'
        params = (self.rating_id, self.VideoId, media_type, 'tmdb', rating, votes)
        n, records = execute_sql_kodi(sql, params, conn)

    def set_ids(self):
        self.uniqueID = get_id('uniqueid_id', 'uniqueid')
        self.uniqueIdValue = self.item.videolibrary_id
        self.uniqueIDType = 'kod'
        sql = 'INSERT OR IGNORE INTO uniqueid (uniqueid_id, media_id, media_type, value, type) VALUES ( ?,  ?,  ?,  ?,  ?)'
        params = [(self.uniqueID, self.VideoId, self.item.contentType, self.uniqueIdValue, self.uniqueIDType)]
        n, records = execute_sql_kodi(sql, params, conn)

        i = self.uniqueID + 1
        for _id in ['imdb', 'tmdb', 'tvdb']:
            if _id +'_id' in self.info:
                params.append((i, self.VideoId, self.item.contentType, self.info[_id + '_id'], _id))
        if params:
            n, records = execute_sql_kodi(sql, params, conn)

    def set_actors(self):
        actor_id = get_id('actor_id', 'actor')
        actors = self.info.get('castandrole',[])
        if actors: actors.sort(key=lambda a: a[3])
        l_actors = []
        sql = 'select actor_id, name from actor'
        n, current_actors = execute_sql_kodi(sql, conn=conn)
        if current_actors: l_actors = [a[1] for a in current_actors]
        actor_params = []
        actor_link_params = []
        actor_sql = 'INSERT OR IGNORE INTO actor (actor_id, name, art_urls) VALUES (?, ?, ?)'
        actor_link_sql = 'INSERT OR IGNORE INTO actor_link (actor_id, media_id, media_type, role, cast_order) VALUES (?, ?, ?, ?, ?)'
        for actor in actors:
            if actor[0] not in l_actors:
                actor_params.append((actor_id, actor[0], actor[2]))
                actor_link_params.append((actor_id, self.VideoId, self.item.contentType, actor[1], actor[3]))
                if actor[2]:
                    self.art.append({'media_id':actor_id, 'media_type': 'actor', 'type':'thumb', 'url':actor[2]})
                actor_id += 1
            else:
                a_id = current_actors[actors.index(actor)][0]
                actor_link_params.append((a_id, self.VideoId, self.item.contentType, actor[1], actor[3]))
        # support.dbg()
        if actor_params:
            n, records = execute_sql_kodi(actor_sql, actor_params)
        if actor_link_params:
            n, records = execute_sql_kodi(actor_link_sql, actor_link_params)

        directors = self.info.get('director','').split(', ')
        directors_image = self.info.get('director_image',['' for d in directors])

        director_params = []
        director_link_params = []
        for d, director in enumerate(directors):
            if director not in l_actors:
                director_params.append((actor_id, director, directors_image[d]))
                if directors_image[d]:
                    self.art.append({'media_id':actor_id, 'media_type': 'director', 'type':'thumb', 'url':directors_image[d]})
                d_id = actor_id
                l_actors.append(director)
                current_actors.append((d_id, director))
                actor_id += 1
            else:
                d_id = current_actors[l_actors.index(director)][0]
                director_link_params.append((d_id, self.VideoId, self.item.contentType))
        if director_params:
            n, records = execute_sql_kodi(actor_sql, director_params)
        if director_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            n, records = execute_sql_kodi(sql, director_link_params)

        writers = self.info.get('writer','').split(', ')
        writers_image = self.info.get('writer_image',['' for w in writers])

        writer_params = []
        writer_link_params = []

        for w, writer in enumerate(writers):
            if writer not in l_actors:
                writer_params.append((actor_id, writer, writers_image[w]))
                d_id = actor_id
                l_actors.append(writer)
                current_actors.append((d_id, writer))
                actor_id += 1
            else:
                d_id = current_actors[l_actors.index(writer)][0]
                writer_link_params.append((d_id, self.VideoId, self.item.contentType))

        if writer_params:
            n, records = execute_sql_kodi(actor_sql, writer_params)
        if writer_link_params:
            sql = 'INSERT OR IGNORE INTO director_link (actor_id, media_id, media_type) VALUES (?, ?, ?)'
            n, records = execute_sql_kodi(sql, writer_link_params)

    def set_country(self):
        countrys = self.info.get('country','').split(', ')
        if countrys:
            for country in countrys:
                sql = 'select country_id from country where name = "{}"'.format(country)
                n, records = execute_sql_kodi(sql, conn=conn)
                if records:
                    _id = records[0][0]
                else:
                    _id = get_id('country_id', 'country')
                    sql = 'INSERT OR IGNORE INTO country (country_id, name) VALUES (?, ?)'
                    params = (_id, country)
                    n, records = execute_sql_kodi(sql, params, conn)
                sql = 'INSERT OR IGNORE INTO country_link (country_id, media_id, media_type) VALUES (?, ?, ?)'
                params = (_id, self.VideoId, self.item.contentType)
                n, records = execute_sql_kodi(sql, params, conn)

    def set_genre(self):
        genres = self.info.get('genre','').split(', ')
        if genres:
            for genre in genres:
                sql = 'select genre_id from genre where name = "{}"'.format(genre)
                n, records = execute_sql_kodi(sql, conn=conn)
                if records:
                    _id = records[0][0]
                else:
                    _id = get_id('genre_id', 'genre')
                    sql = 'INSERT OR IGNORE INTO genre (genre_id, name) VALUES (?, ?)'
                    params = (_id, genre)
                    n, records = execute_sql_kodi(sql, params, conn)
                sql = 'INSERT OR IGNORE INTO genre_link (genre_id, media_id, media_type) VALUES (?, ?, ?)'
                params = (_id, self.VideoId, self.item.contentType)
                n, records = execute_sql_kodi(sql, params, conn)

    def set_studio(self):
        studios = self.info.get('studio','').split(', ')
        if studios:
            for studio in studios:
                sql = 'select studio_id from studio where name = "{}"'.format(studio)
                n, records = execute_sql_kodi(sql, conn=conn)
                if records:
                    _id = records[0][0]
                else:
                    _id = get_id('studio_id', 'studio')
                    sql = 'INSERT OR IGNORE INTO studio (studio_id, name) VALUES (?, ?)'
                    params = (_id, studio)
                    n, records = execute_sql_kodi(sql, params, conn)
                sql = 'INSERT OR IGNORE INTO studio_link (studio_id, media_id, media_type) VALUES (?, ?, ?)'
                params = (_id, self.VideoId, self.item.contentType)
                n, records = execute_sql_kodi(sql, params, conn)

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
        n, records = execute_sql_kodi(sql, params, conn)
        if self.item.thumbnail:
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie', 'type':'poster', 'url':self.item.thumbnail})
        if self.item.fanart:
            self.art.append({'media_id':self.VideoId, 'media_type': 'movie',  'type':'fanart', 'url':self.item.fanart})
        # payload = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid": self.VideoId, "thumbnail":self.item.thumbnail, "art":{"poster": self.item.thumbnail, "fanart":self.item.fanart}}, "id": 1}
        # get_data(payload)
        # if self.idSet:
        #     payload = {"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieSetDetails", "params": {"setid": self.idSet, "art":{"poster": self.info['setposters'][0], "fanart":self.info['setfanarts'][0]}}, "id": 1}
        #     get_data(payload)



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
        n, records = execute_sql_kodi(sql, params, conn)

    def set_art(self):
        params = []
        art_urls = []
        _id = get_id('art_id', 'art')
        sql = 'select media_id, media_type, type from art'
        n, records = execute_sql_kodi(sql, conn=conn)
        if records:
            art_urls = [[u[0], u[1], u[2]] for u in records]
        for art in self.art:
            if [art ['media_id'], art['media_type'], art['type']] not in art_urls:
                params.append((_id, art['media_id'], art['media_type'], art['type'], art['url']))
                _id += 1
        if params:
            sql = 'INSERT OR IGNORE INTO art (art_id, media_id, media_type, type, url) VALUES (?, ?, ?, ?, ?)'
            n, records = execute_sql_kodi(sql, params, conn)


def add_video(item):
    if item.contentType == 'movie':
        addVideo(item=item)
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

    setposters = item.infoLabels.get('setposters',[])
    setfanarts = item.infoLabels.get('setfanarts',[])
    videoposters = [item.thumbnail] + item.infoLabels.get('posters',[])
    videofanarts = [item.fanart] + item.infoLabels.get('fanarts',[])

    for p in setposters:
        if p: posters += pstring.format('set.poster', p.replace('original', 'w500'), p)
    for p in setfanarts:
        if p: posters += pstring.format('set.fanart', p.replace('original', 'w500'), p)
    for p in videoposters: 
        if p: posters += pstring.format('poster', p.replace('original', 'w500'), p)

    fanarts += '<fanart>'
    for f in videofanarts:
        if f: fanarts += fstring.format(f.replace('original', 'w780'), f)
    fanarts += '</fanart>'

    return posters, fanarts