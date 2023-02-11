from core import httptools
from platformcode import config, logger
import random, string
import codecs


def get_sources(page_url):
    code = page_url.split('/')[-1].split('.html')[0]
    rand1 = "".join([random.choice(string.ascii_letters) for y in range(12)])
    rand2 = "".join([random.choice(string.ascii_letters) for y in range(12)])
    _0x470d0b = '{}||{}||{}||streamsb'.format(rand1, code, rand2)
    sources = 'https://streamas.cloud/sources50/' + codecs.getencoder('hex')(_0x470d0b.encode())[0].decode()
    # does not lite other headers different than watchsb and useragent
    ret = httptools.downloadpage(sources, headers={'watchsb': 'sbstream', 'User-Agent': httptools.get_user_agent()}, replace_headers=True).json
    logger.debug(ret)
    return ret


def test_video_exists(page_url):
    global sources
    sources = get_sources(page_url)

    if 'error' in sources:
        return False, config.get_localized_string(70449) % "StreamSB"
    else:
        return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global sources
    file = sources['stream_data']['file']
    backup = sources['stream_data']['backup']
    return [["m3u8 [StreamSB]", file], ["m3u8-altern [StreamSB]", backup]]


def get_filename(page_url):
    return get_sources(page_url)['stream_data']['title']
