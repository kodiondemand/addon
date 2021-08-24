# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Altadefinizione Community
from logging import debug
from core import jsontools, support
from lib.fakeMail import Gmailnator
from platformcode import config, platformtools, logger
from core import scrapertools, httptools


def findhost(url):
    return support.match(url, patron=r'<a href="([^"]+)/\w+">Accedi').match


host = config.get_channel_url(findhost)
register_url = 'https://altaregistrazione.com'
headers = {'Referer': host, 'x-requested-with': 'XMLHttpRequest'}


@support.menu
def mainlist(item):
    support.info(item)

    film = ['/load-more-film?anno=&order=&support_webp=1&type=movie&page=1',
        # Voce Menu,['url','action','args',contentType]
        ('Generi', ['', 'genres', 'genres']),
        ]

    tvshow = ['/load-more-film?type=tvshow&anno=&order=&support_webp=1&page=1',
        # Voce Menu,['url','action','args',contentType]
        ('Generi', ['', 'genres', 'genres']),
        ]

    altri = [
        # ('Per Lettera', ['/lista-film', 'genres', 'letters']),
        ('Qualità', ['', 'genres', 'quality']),
        # ('Anni', ['/anno', 'genres', 'years'])
    ]
    search = ''

    return locals()


def login():
    r = support.httptools.downloadpage(host, cloudscraper=True)
    Token = support.match(r.data, patron=r'name=\s*"_token"\s*value=\s*"([^"]+)', cloudscraper=True).match
    if 'id="logged"' in r.text:
        logger.info('Già loggato')
    else:
        logger.info('Login in corso')
        post = {'_token': '',
                'form_action':'login', 
                'email': config.get_setting('username', channel='altadefinizionecommunity'),
                'password':config.get_setting('password', channel='altadefinizionecommunity')}

        r = support.httptools.downloadpage(host + '/login', post=post, headers={'referer': host}, cloudscraper=True)
        if not r.status_code in [200, 302] or 'Email o Password non validi' in r.text:
            platformtools.dialog_ok('AltadefinizioneCommunity', 'Username/password non validi')
            return False

    return 'id="logged"' in r.text


def registerOrLogin():
    if config.get_setting('username', channel='altadefinizionecommunity') and config.get_setting('password', channel='altadefinizionecommunity'):
        if login():
            return True

    action = platformtools.dialog_yesno('AltadefinizioneCommunity',
                                  'Questo server necessita di un account, ne hai già uno oppure vuoi tentare una registrazione automatica?',
                                  yeslabel='Accedi', nolabel='Tenta registrazione', customlabel='Annulla')
    if action == 1:  # accedi
        from specials import setting
        from core.item import Item
        user_pre = config.get_setting('username', channel='altadefinizionecommunity')
        password_pre = config.get_setting('password', channel='altadefinizionecommunity')
        setting.channel_config(Item(config='altadefinizionecommunity'))
        user_post = config.get_setting('username', channel='altadefinizionecommunity')
        password_post = config.get_setting('password', channel='altadefinizionecommunity')

        if user_pre != user_post or password_pre != password_post:
            return registerOrLogin()
        else:
            return []
    elif action == 0:  # tenta registrazione
        import random
        import string
        logger.debug('Registrazione automatica in corso')
        mailbox = Gmailnator()
        randPsw = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(10))
        logger.debug('email: ' + mailbox.address)
        logger.debug('pass: ' + randPsw)
        reg = platformtools.dialog_register(register_url, email=True, password=True, email_default=mailbox.address, password_default=randPsw)
        if not reg:
            return False
        regPost = httptools.downloadpage(register_url, post={'email': reg['email'], 'password': reg['password']}, cloudscraper=True)

        if regPost.url == register_url:
            error = scrapertools.htmlclean(scrapertools.find_single_match(regPost.data, 'Impossibile proseguire.*?</div>'))
            error = scrapertools.unescape(scrapertools.re.sub('\n\s+', ' ', error))
            platformtools.dialog_ok('AltadefinizioneCommunity', error)
            return False
        if reg['email'] == mailbox.address:
            if "L'indirizzo email risulta già registrato" in regPost.data:
                # httptools.downloadpage(baseUrl + '/forgotPassword', post={'email': reg['email']})
                platformtools.dialog_ok('AltadefinizioneCommunity', 'Indirizzo mail già utilizzato')
                return False
            mail = mailbox.waitForMail()
            if mail:
                checkUrl = scrapertools.find_single_match(mail.body, '<a href="([^"]+)[^>]+>Verifica').replace(r'\/', '/')
                logger.debug('CheckURL: ' + checkUrl)
                httptools.downloadpage(checkUrl, cloudscraper=True)
                config.set_setting('username', mailbox.address, channel='altadefinizionecommunity')
                config.set_setting('password', randPsw, channel='altadefinizionecommunity')
                platformtools.dialog_ok('AltadefinizioneCommunity',
                                        'Registrato automaticamente con queste credenziali:\nemail:' + mailbox.address + '\npass: ' + randPsw)
            else:
                platformtools.dialog_ok('AltadefinizioneCommunity', 'Impossibile registrarsi automaticamente')
                return False
        else:
            platformtools.dialog_ok('AltadefinizioneCommunity', 'Hai modificato la mail quindi KoD non sarà in grado di effettuare la verifica in autonomia, apri la casella ' + reg['email']
                                    + ' e clicca sul link. Premi ok quando fatto')
        logger.debug('Registrazione completata')
    else:
        return False

    return True


@support.scrape
def peliculas(item):
    json = {}
    action = 'check'
    if '/load-more-film' not in item.url and '/search' not in item.url:  # generi o altri menu, converto
        import ast
        ajax = support.match(item.url, patron='ajax_data\s*=\s*"?\s*([^;]+)', cloudscraper=True).match
        item.url = host + '/load-more-film?' + support.urlencode(ast.literal_eval(ajax)) + '&page=1'
    if not '/search' in item.url:
        json = support.httptools.downloadpage(item.url, headers=headers, cloudscraper=True).json
        data = "\n".join(json['data'])
    else:
        disabletmdb = True
        data = support.httptools.downloadpage(item.url, headers=headers, cloudscraper=True).data
    patron = r'wrapFilm">\s*<a href="(?P<url>[^"]+)">\s*<span class="year">(?P<year>[0-9]{4})</span>\s*<span[^>]+>[^<]+</span>\s*<span class="qual">(?P<quality>[^<]+).*?<img src="(?P<thumbnail>[^"]+)[^>]+>\s*<h3>(?P<title>[^<[]+)(?:\[(?P<lang>[sSuUbBiItTaA-]+))?'

    # paginazione
    if json.get('have_next'):
        def fullItemlistHook(itemlist):
            spl = item.url.split('=')
            url = '='.join(spl[:-1])
            page = str(int(spl[-1])+1)
            support.nextPage(itemlist, item, next_page='='.join((url, page)), function_or_level='peliculas')
            return itemlist

    return locals()


def search(item, texto):
    support.info("search ", texto)

    item.args = 'search'
    item.url = host + "/search?s={}&page=1".format(texto)
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genres(item):
    support.info(item)
    data = support.httptools.downloadpage(item.url, cloudscraper=True).data

    patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)'
    if item.args == 'quality':
        patronBlock = 'Risoluzione(?P<block>.*?)</ul>'
    else:
        patronBlock = ('Film' if item.contentType == 'movie' else 'Serie TV') + r'<span></span></a>\s+<ul class="dropdown-menu(?P<block>.*?)active-parent-menu'
    action = 'peliculas'

    return locals()


@support.scrape
def episodios(item):
    support.info(item)
    data = item.data
    patron = r'class="playtvshow " data-href="(?P<url>[^"]+)'

    def itemHook(it):
        spl = it.url.split('/')[-2:]
        it.infoLabels['season'] = int(spl[0])+1
        it.infoLabels['episode'] = int(spl[1])+1
        return it

    return locals()

def check(item):
    if '/watch-unsubscribed' not in item.url:
        playWindow = support.match(support.httptools.downloadpage(item.url, cloudscraper=True).data, patron='playWindow" href="([^"]+)')
        video_url = playWindow.match
        if '/tvshow' in video_url:
            item.data = playWindow.data
            item.contentType = 'tvshow'
            return episodios(item)
        else:
            item.video_url = video_url.replace('/watch-unsubscribed', '/watch-external')
            return findvideos(item)

def findvideos(item):
    itemlist = []

    itemlist.append(item.clone(action='play', url=support.match(item.video_url, patron='allowfullscreen[^<]+src="([^"]+)"', cloudscraper=True).match, quality=''))

    return support.server(item, itemlist=itemlist)


def play(item):
    if host in item.url:  # intercetto il server proprietario
        if registerOrLogin():
            return support.get_jwplayer_mediaurl(support.httptools.downloadpage(item.url, cloudscraper=True).data, 'Diretto')
        else:
            platformtools.play_canceled = True
            return []
    else:
        return [item]
