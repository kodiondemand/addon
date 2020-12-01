# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Logger (kodi)
# --------------------------------------------------------------------------------
from __future__ import unicode_literals
import inspect,os, xbmc, sys
from platformcode import config

# for test suite
try:
    xbmc.KodiStub()
    testMode = True
    record = False
    recordedLog = ''
    import html
except:
    testMode = False
LOG_FORMAT = '{addname}[{filename}.{function}:{line}]{sep} {message}'
DEBUG_ENABLED = config.get_setting("debug")
DEF_LEVEL = xbmc.LOGINFO if sys.version_info[0] >= 3 else xbmc.LOGNOTICE


def info(*args):
    log(*args)


def debug(*args):
    if DEBUG_ENABLED:
        log(*args)


def error(*args):
    log("######## ERROR #########", level=xbmc.LOGERROR)
    log(*args, level=xbmc.LOGERROR)


def log(*args, **kwargs):
    msg = ''
    for arg in args: msg += ' ' + str(arg)
    if testMode and record:
        global recordedLog
        recordedLog += msg + '\n'
        return
    frame = inspect.currentframe().f_back.f_back
    filename = frame.f_code.co_filename
    filename = os.path.basename(filename).split('.')[0]
    xbmc.log(LOG_FORMAT.format(addname=config.PLUGIN_NAME,
                              filename=filename,
                              line=frame.f_lineno,
                              sep=':' if msg else '',
                              function=frame.f_code.co_name,
                              message=msg), kwargs.get('level', DEF_LEVEL))


class WebErrorException(Exception):
    def __init__(self, url, channel, *args, **kwargs):
        self.url = url
        self.channel = channel
        Exception.__init__(self, *args, **kwargs)


class ChannelScraperException(Exception):
    pass