from core import httptools, scrapertools
from platformcode import config
import base64


def test_video_exists(page_url):
    global data
    data = httptools.downloadpage(page_url).data

    if 'File Not Found' in data:
        return False, config.get_localized_string(70449) % "HexUpload"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = []
    global data
    source = scrapertools.find_single_match(data, r'b4aa\.buy\("([^"]+)')
    if source:
        media_url = base64.b64decode(source).decode()
        video_urls.append(["mp4", media_url])
    else:  # download only
        post = {
            "op": "download2",
            "id": page_url.split('/')[-1],
            "method_free": "Free + Download",
            "method_premium": "",
            "adblock_detected": "0"
        }
        data = httptools.downloadpage(page_url, post=post).data
        media_url, filename = scrapertools.find_single_match(data, "ldl\.ld\('([^']+)','([^']+)")
        media_url = base64.b64decode(media_url).decode()
        filename = base64.b64decode(filename).decode()
        video_urls.append([filename.split('.')[-1], media_url])
    return video_urls


def get_filename(page_url):
    # from core.support import dbg;dbg()
    title = httptools.downloadpage(page_url).data.split('<h2 style="word-break: break-all;">')[1].split('</h2>')[0]
    return title
