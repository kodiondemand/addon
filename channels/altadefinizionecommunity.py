# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Altadefinizione Community

from core import support
from lib.fakeMail import Gmailnator
from platformcode import config, platformtools, logger
from core import scrapertools, httptools


def findhost(url):
    return support.match(url, patron=r'<a href="([^"]+)/\w+">Accedi').match


host = config.get_channel_url(findhost)
register_url = 'https://altaregistrazione.net'

if 'altadefinizionecommunity' not in host:
    config.get_channel_url(findhost, forceFindhost=True)

if host.endswith('/'):
    host = host[:-1]

headers = {'Referer': host}
order = ['', 'i_piu_visti', 'i_piu_votati', 'i_piu_votati_dellultimo_mese', 'titolo_az', 'voto_imdb_piu_alto'][config.get_setting('order', 'altadefinizionecommunity')]


@support.menu
def mainlist(item):
    logger.debug(item)

    film = ['/type/movie',
            ('Generi', ['/type/movie', 'genres', 'genres']),
            ('Anni', ['/type/movie', 'genres', 'year']),]

    tvshow = ['/serie-tv/tvshow',
              ('Generi', ['/serie-tv/tvshow', 'genres', 'genres']),
              ('Anni', ['/serie-tv/tvshow', 'genres', 'year'])]

    return locals()


def search(item, text):
    logger.debug("search ", text)
    # per evitare fastidi da ricerca globale
    if not item.globalsearch:
        registerOrLogin()

    item.args = 'search'
    item.url = host + "/search?s={}&f={}".format(text.replace(' ', '+'), item.contentType)
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
    registerOrLogin()
    logger.debug(item)
    data = support.httptools.downloadpage(item.url).data
    blacklist= ['Film', 'Serie TV']

    if item.args == 'genres':
        categories ={}
        res = support.match(host + '/cerca', patron=r'for="cat-(\d+)[^>]+>([^<]+)').matches
        for _id, name in res:
            categories[name] = _id

        patronBlock = r'{}<span></span>(?P<block>.*?)</ul>\s*</li'.format('Film' if item.contentType == 'movie' else 'Serie TV')
        patronMenu = r'<a href="[^"]+">(?P<title>[^<]+)'

        def itemHook(it):
            it.cat_id = categories[it.fulltitle]
            return it

    if item.args == 'year':
        patronMenu = r'value="(?P<year_id>[^"]+)"[^>]*>(?P<title>\d+)'
        patronBlock = r'Anno</option>(?P<block>.*?</select>)'

    elif item.args == 'quality':
        patronMenu = r'quality/(?P<quality_id>[^"]+)">(?P<title>[^<]+)'
        patronBlock = r'Risoluzione(?P<block>.*?)</ul>'

    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    item.quality = 'HD'
    json = {}
    if not item.page: item.page = 1
    params ={'type':item.contentType, 'anno':item.year_id, 'quality':item.quality_id, 'cat':item.cat_id, 'order':order, 'page':item.page}
    # debug = True

    action = 'findvideos' if item.contentType == 'movie' else 'episodios'

    try:
        # support.dbg()
        if item.args in ['search']:
            page = support.httptools.downloadpage(item.url, headers=headers)
            if page.json:
                data = "\n".join(page.json['data'])
            else:
                data = page.data
        else:
            params['page'] = item.page

            url = '{}/load-more-film?{}'.format(host, support.urlencode(params))
            json = support.httptools.downloadpage(url, headers=headers).json
            data = "\n".join(json['data'])
    except:
        data = ' '

    patron = r'wrapFilm"[^>]*>\s*<a href="(?P<url>[^"]+)">[^>]+>(?P<year>\d+)(?:[^>]+>){2}(?P<rating>[^<]+)(?:[^>]+>){4}\s*<img src="(?P<thumb>[^"]+)(?:[^>]+>){2,6}\s+<h3>(?P<title>[^<[]+)(?:\[(?P<lang>[sSuUbBiItTaA -]+))?'
    # patron = r'wrapFilm">\s*<a href="(?P<url>[^"]+)">[^>]+>(?P<year>\d+)(?:[^>]+>){2}(?P<rating>[^<]+)(?:[^>]+>){4}\s*<img src="(?P<thumb>[^"]+)(?:[^>]+>){3}(?P<title>[^<[]+)(?:\[(?P<lang>[sSuUbBiItTaA-]+))?'

    def itemHook(item):
        item.quality = item.quality.replace('2K', 'HD').replace('4K', 'HD')
        item.title = item.title.replace('2K', 'HD').replace('4K', 'HD')
        return item

    # paginazione
    if json.get('have_next') or support.match(data, patron=r'have_next_film\s*=\s*true').match:
        def fullItemlistHook(itemlist):
            cat_id = support.match(data, patron=r''''cat':"(\d+)"''').match
            if cat_id: item.cat_id = cat_id
            item.page += 1
            support.nextPage(itemlist, item, function_or_level='peliculas')
            return itemlist

    return locals()


@support.scrape
def episodios(item):
    registerOrLogin()
    logger.debug(item)
    # debug = True
    data = item.data
    patron = r'class="playtvshow "\s+data-href="(?P<url>[^"]+)'

    def itemHook(it):
        spl = it.url.split('/')[-2:]
        it.infoLabels['season'] = int(spl[0])+1
        it.infoLabels['episode'] = int(spl[1])+1
        it.url = it.url.replace('/watch-unsubscribed', '/watch-external')
        it.title = '{}x{:02d} - {}'.format(it.contentSeason, it.contentEpisodeNumber, it.fulltitle)
        return it

    return locals()


def findvideos(item):
    itemlist = []
    resolve_url(item)

    itemlist.append(item.clone(action='play', url=support.match(item.url, patron='allowfullscreen[^<]+src="([^"]+)"', cloudscraper=True).match, quality=''))

    return support.server(item, itemlist=itemlist)


def play(item):
    if host in item.url:  # intercetto il server proprietario
        # if registerOrLogin():
        return support.get_jwplayer_mediaurl(support.httptools.downloadpage(item.url, cloudscraper=True).data, 'Diretto')
        # else:
        #     platformtools.play_canceled = True
        #     return []
    else:
        return [item]


def resolve_url(item):
    registerOrLogin()
    if '/watch-unsubscribed' not in item.url and '/watch-external' not in item.url:
        playWindow = support.match(support.httptools.downloadpage(item.url, cloudscraper=True).data, patron='playWindow" href="([^"]+)')
        video_url = playWindow.match
        item.data = playWindow.data
        item.url = video_url.replace('/watch-unsubscribed', '/watch-external')
    return item


def login():
    r = support.httptools.downloadpage(host, cloudscraper=True)
    Token = support.match(r.data, patron=r'name=\s*"_token"\s*value=\s*"([^"]+)', cloudscraper=True).match
    if 'id="logged"' in r.data:
        logger.info('Già loggato')
    else:
        logger.info('Login in corso')
        post = {'_token': '',
                'form_action':'login',
                'email': config.get_setting('username', channel='altadefinizionecommunity'),
                'password':config.get_setting('password', channel='altadefinizionecommunity')}

        r = support.httptools.downloadpage(host + '/login', post=post, headers={'referer': host}, cloudscraper=True)
        if r.code not in [200, 302] or 'Email o Password non validi' in r.data:
            platformtools.dialog_ok('AltadefinizioneCommunity', 'Username/password non validi')
            return False

    return 'id="logged"' in r.data


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
