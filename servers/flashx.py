# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import os
import time

from core import httptools, scrapertools
from lib import jsunpack
from platformcode import config, logger, platformtools

flashx_data = ""
flashx_hash_f = ""
flashx_post = ""

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)
    global flashx_data
    try:
        flashx_data = httptools.downloadpage(page_url, cookies="xfsts=pfp5dj3e6go1l2o1").data
    except:
        try:
            flashx_data = httptools.downloadpage(page_url).data
        except:
            return False,  config.get_localized_string(70296) % "FlashX"
    bloque = scrapertools.find_single_match(flashx_data, '(?s)Form method="POST" action(.*?)span')
    flashx_id = scrapertools.find_single_match(bloque, 'name="id" value="([^"]+)"')
    fname = scrapertools.find_single_match(bloque, 'name="fname" value="([^"]+)"')
    global flashx_hash_f
    flashx_hash_f = scrapertools.find_single_match(bloque, 'name="hash" value="([^"]+)"')
    imhuman = scrapertools.find_single_match(bloque, "value='([^']+)' name='imhuman'")
    global flashx_post
    flashx_post = 'op=download1&usr_login=&id=%s&fname=%s&referer=&hash=%s&imhuman=%s' % (
        flashx_id, urllib.quote(fname), flashx_hash_f, imhuman)
    if 'file was deleted' in flashx_data or 'File Not Found (Deleted or Abused)' in flashx_data:
        return False, config.get_localized_string(70292) % "FlashX"
    elif 'Video is processing now' in flashx_data:
        return False, config.get_localized_string(70293) % "FlashX"
    elif 'Too many views per minute' in flashx_data:
        return False, config.get_localized_string(70300) % "FlashX"

    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    pfxfx = ""
    data = flashx_data
    data = data.replace("\n", "")
    cgi_counter = scrapertools.find_single_match(data,
                                                 """(?is)src=.(https://www.flashx.../counter.cgi.*?[^(?:'|")]+)""")
    cgi_counter = cgi_counter.replace("%0A", "").replace("%22", "")
    playnow = scrapertools.find_single_match(data, 'https://www.flashx.../dl[^"]+')
    # Para obtener el f y el fxfx
    js_fxfx = "https://www." + scrapertools.find_single_match(data.replace("//", "/"),
                                                              """(?is)(flashx.../js\w+/c\w+.*?[^(?:'|")]+)""")
    if len(js_fxfx) > 15:
        data_fxfx = httptools.downloadpage(js_fxfx).data
        mfxfx = scrapertools.find_single_match(data_fxfx, 'get.*?({.*?})').replace("'", "").replace(" ", "")
        matches = scrapertools.find_multiple_matches(mfxfx, '(\w+):(\w+)')
        for f, v in matches:
            pfxfx += f + "=" + v + "&"
    logger.debug("mfxfxfx1= %s" % js_fxfx)
    logger.debug("mfxfxfx2= %s" % pfxfx)
    if pfxfx == "":
        pfxfx = "f=fail&fxfx=6"
    coding_url = 'https://www.flashx.co/flashx.php?%s' % pfxfx
    
    # Obligatorio descargar estos 2 archivos, porque si no, muestra error
    httptools.downloadpage(coding_url, cookies=False)
    httptools.downloadpage(cgi_counter, cookies=False)
    
    ts = int(time.time())
    flash_ts = scrapertools.find_single_match(flashx_hash_f, '-(\d{10})-')
    wait_time = int(flash_ts) - ts
    platformtools.dialog_notification('Cargando flashx', 'Espera de %s segundos requerida' % wait_time)
    
    try:
        time.sleep(wait_time)
    except:
        time.sleep(6)

    data = httptools.downloadpage(playnow, post = flashx_post).data
    # Si salta aviso, se carga la pagina de comprobacion y luego la inicial
    # LICENSE GPL3, de alfa-addon: https://github.com/alfa-addon/ ES OBLIGATORIO AÑADIR ESTAS LÍNEAS
    if "You try to access this video with Kodi" in data:
        url_reload = scrapertools.find_single_match(data, 'try to reload the page.*?href="([^"]+)"')
        try:
            data = httptools.downloadpage(url_reload).data
            data = httptools.downloadpage(playnow, post = flashx_post).data
        # LICENSE GPL3, de alfa-addon: https://github.com/alfa-addon/ ES OBLIGATORIO AÑADIR ESTAS LÍNEAS
        except:
            pass

    matches = scrapertools.find_multiple_matches(data, "(eval\(function\(p,a,c,k.*?)\s+</script>")
    video_urls = []
    for match in matches:
        try:
            match = jsunpack.unpack(match)
            match = match.replace("\\'", "'")
            media_urls = scrapertools.find_multiple_matches(match, "{src:'([^']+)'.*?,label:'([^']+)'")
            subtitle = ""
            for media_url, label in media_urls:
                if media_url.endswith(".srt") and label == "Spanish":
                    try:
                        from core import filetools
                        data = httptools.downloadpage(media_url)
                        subtitle = os.path.join(config.get_data_path(), 'sub_flashx.srt')
                        filetools.write(subtitle, data)
                    except:
                        import traceback
                        logger.debug("Error al descargar el subtítulo: " + traceback.format_exc())

            for media_url, label in media_urls:
                if not media_url.endswith("png") and not media_url.endswith(".srt"):
                    video_urls.append(["." + media_url.rsplit('.', 1)[1] + " [flashx]", media_url, 0, subtitle])

            for video_url in video_urls:
                logger.debug("%s - %s" % (video_url[0], video_url[1]))
        except:
            pass

    return video_urls

