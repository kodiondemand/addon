# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector UP Stream By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
	logger.debug("(page_url='%s')" % page_url)
	global data
	data = httptools.downloadpage(page_url).data
	if "as it expired or has been deleted" in data:
		return False, config.get_localized_string(70449) % "UPstream"
	return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
	video_urls = []
	global data
	new_data = scrapertools.find_single_match(data, r"<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")
	if new_data != "":
		from lib import jsunpack
		data = jsunpack.unpack(new_data)
	media_url = scrapertools.find_single_match(data, r'file:"([^"]+)"')
	video_urls.append({'type':media_url.split('.')[-1], 'url':media_url + '|Referer=' + page_url})

	return video_urls
