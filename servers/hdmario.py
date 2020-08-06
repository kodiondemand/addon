# -*- coding: utf-8 -*-
import xbmc

from core import httptools, scrapertools, filetools
from platformcode import logger, config, platformtools

baseUrl = 'https://hdmario.live'

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global page, data

    page = httptools.downloadpage(page_url)
    data = page.data
    logger.info(page.url)

    if "the page you are looking for could not be found" in data:
        return False, config.get_localized_string(70449) % "HDmario"
    return True, ""


def login():
    httptools.downloadpage(page.url.replace('/unauthorized', '/login'),
                           post={'email': config.get_setting('username', server='hdmario'),
                                 'password': config.get_setting('password', server='hdmario')})


def registerOrLogin(page_url, forced=False):
    if not forced and config.get_setting('username', server='hdmario') and config.get_setting('password', server='hdmario'):
        login()
    else:
        if platformtools.dialog_yesno('HDmario',
                                      'Questo server necessita di un account, ne hai già uno oppure vuoi tentare una registrazione automatica?',
                                      yeslabel='Accedi', nolabel='Tenta registrazione'):
            from specials import setting
            from core.item import Item
            setting.server_config(Item(config='hdmario'))
            login()
        else:
            logger.info('Registrazione automatica in corso')
            import random
            import string
            randEmail = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(random.randint(9, 14))) + '@gmail.com'
            randPsw = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))
            logger.info('email: ' + randEmail)
            logger.info('pass: ' + randPsw)
            nTry = 0
            while nTry < 5:
                nTry += 1
                rq = 'loggedin' in httptools.downloadpage(baseUrl + '/register/',
                                                          post={'email': randEmail, 'email_confirmation': randEmail,
                                                                'password': randPsw,
                                                                'password_confirmation': randPsw}).url
                if rq:
                    config.set_setting('username', randEmail, server='hdmario')
                    config.set_setting('password', randPsw, server='hdmario')
                    platformtools.dialog_ok('HDmario',
                                            'Registrato automaticamente con queste credenziali:\nemail:' + randEmail + '\npass: ' + randPsw)
                    break
            else:
                platformtools.dialog_ok('HDmario', 'Impossibile registrarsi automaticamente')
            logger.info('Registrazione completata')
    global page, data
    page = httptools.downloadpage(page_url)
    data = page.data

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global page, data
    page_url = page_url.replace('?', '')
    logger.info("url=" + page_url)

    if 'unconfirmed' in page.url:
        from lib import onesecmail
        id = page_url.split('/')[-1]
        mail = onesecmail.getRandom()
        postData = {
            'email': mail,
            'hls_video_id': id
        }
        httptools.downloadpage(page.url, post=postData)
        jsonMail = onesecmail.waitForMail(mail)
        logger.info(jsonMail)
        if jsonMail:
            code = jsonMail['subject'].split(' - ')[0]
            page = httptools.downloadpage(page_url + '?code=' + code)
            data = page.data

    if '/unauthorized' in page.url:
        registerOrLogin(page_url)

    if 'Registrati' in data:
        platformtools.dialog_ok('HDmario', 'Username/password non validi')
        registerOrLogin(page_url, True)
    logger.info(data)
    from lib import jsunpack_js2py
    unpacked = jsunpack_js2py.unpack(scrapertools.find_single_match(data, '<script type="text/javascript">\n*\s*\n*(eval.*)'))
    # p,a,c,k,e,d data -> xhr.setRequestHeader
    secureProof = scrapertools.find_single_match(unpacked, """X-Secure-Proof['"]\s*,\s*['"]([^"']+)""")
    logger.info('X-Secure-Proof=' + secureProof)

    data = httptools.downloadpage(baseUrl + '/pl/' + page_url.split('/')[-1].replace('?', '') + '.m3u8', headers=[['X-Secure-Proof', secureProof]]).data
    filetools.write(xbmc.translatePath('special://temp/hdmario.m3u8'), data, 'w')

    video_urls = [['.m3u8 [HDmario]', 'special://temp/hdmario.m3u8']]

    return video_urls
