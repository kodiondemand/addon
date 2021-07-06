# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import json
import random
from core import httptools, support, scrapertools
from platformcode import platformtools, logger
import base64
from lib import js2py

files = None

def test_video_exists(page_url):

  global htmldata
  htmldata = httptools.downloadpage(page_url).data
  
  if htmldata:
    return True, ""
  else:
    return False

def exec_Js(str):
  return js2py.eval_js(str)

def get_video_url(page_url, premium=False, user="", password="", video_password=""):

  support.dbg()

  first_decoder_js = scrapertools.find_single_match(htmldata, '<script\s+?type=[\'|"].*?[\'|"]>\s?(var.*?)<\/script>')

  first_decoder_js = first_decoder_js.replace('eval', '')

  first_decoder_fn = exec_Js(first_decoder_js)


  tabber_js = httptools.downloadpage('https://streamon.to/assets/js/tabber.js').data
  tabber_js = tabber_js.replace('eval', '')
  tabber_js_fn = exec_Js(tabber_js)

  groups = scrapertools.find_multiple_matches( tabber_js_fn, 'var res\s+?=\s+?(.*?)\.replace\("(.*?)"\).*\.replace\("(.*?)"\).*atob\(res2\)' )
  
  variable = None
  key1 = None
  key2 = None
  if len(groups) > 0:
    groups = groups[0]
    variable = groups[0]
    key1 = groups[1][ :-4]
    key2 = groups[2][ :-4]

  variable_value = scrapertools.find_single_match(first_decoder_fn, 'var {}="(.*?)"'.format(variable) )

  res = variable_value.replace(key1, "")
  res2 = res.replace(key2, "")
  media_url = base64.b64decode( res2 ).decode('ascii')
  
  video_urls = []

  video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [Streamon]", media_url])

  return video_urls
