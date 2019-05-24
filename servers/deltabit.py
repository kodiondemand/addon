# -*- coding: utf-8 -*-

import time
import urllib

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File Does not Exist" in data:
        return False, "[deltabit] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(deltabit page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('"', "'")
    page_url_post = scrapertools.find_single_match(data, "<Form method='POST' action='([^']+)'>")
    imhuman = "&imhuman=" + scrapertools.find_single_match(data, "name='imhuman' value='([^']+)'").replace(" ", "+")
    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")}) + imhuman
    time.sleep(6)
    data = httptools.downloadpage(page_url_post, post=post).data
##    logger.info("(data page_url='%s')" % data)
    sources = scrapertools.find_single_match(data, 'sources: \[([^\]]+)\]')
    
    for media_url in scrapertools.find_multiple_matches(sources, '"([^"]+)"'):
        ext = scrapertools.get_filename_from_url(media_url)[-4:]
        video_urls.append(["%s [deltabit]" % (ext), media_url])    
    return video_urls

##    logger.info("deltabit url=" + page_url)
##    data = httptools.downloadpage(page_url).data
##    code = scrapertools.find_multiple_matches(data, '<input type="hidden" name="[^"]+" value="([^"]+)"')
##    time.sleep(6)
##    data = httptools.downloadpage(page_url+'?op='+code[0]+\
##                                  '&id='+code[1]+'&fname='+code[2]+'&hash='+code[3]).data
##    
##    logger.info("DATA deltabit : %s" % data)



##    https://deltabit.co/6zragsekoole?op=download1&usr_login=%27%27&id=6zragsekoole&fname=New.Amsterdam.2018.Episodio.1.Come.Posso.Aiutare.iTALiAN.WEBRip.x264-GeD.mkv&referer=%27%27&hash=24361-79-32-1557854113-cc51baafbf1530f43b746133fbd293ee    
##    https://deltabit.co/6zragsekoole?op=download1&usr_login=''&id=6zragsekoole&fname=New.Amsterdam.2018.Episodio.1.Come.Posso.Aiutare.iTALiAN.WEBRip.x264-GeD.mkv&referer=''&hash=24361-79-32-1557854113-cc51baafbf1530f43b746133fbd293ee

##    video_urls = page_url+'?op='+code[0]+'&usr_login='+code[1]+'&id='+code[2]+'&fname='+code[3]+'&referer='+code[4]+'&hash='+code[5]

##    logger.info("Delta bit [%s]: " % page_url)
    
##    code = scrapertools.find_single_match(data, 'name="code" value="([^"]+)')
##    hash = scrapertools.find_single_match(data, 'name="hash" value="([^"]+)')
##    post = "op=download1&code=%s&hash=%s&imhuman=Proceed+to+video" %(code, hash)
##    data1 = httptools.downloadpage("http://m.vidtome.stream/playvideo/%s" %code, post=post).data
##    video_urls = []
##    media_urls = scrapertools.find_multiple_matches(data1, 'file: "([^"]+)')
##    for media_url in media_urls:
##        ext = scrapertools.get_filename_from_url(media_url)[-4:]
##        video_urls.append(["%s [vidtomestream]" % (ext), media_url])
##    video_urls.reverse()
##    for video_url in video_urls:
##        logger.info("%s" % (video_url[0]))
##    return video_urls


