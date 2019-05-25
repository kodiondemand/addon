# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# MCT - Mini Cliente Torrent
# ------------------------------------------------------------

import os
import shutil
import tempfile
import urllib

import urllib2

try:
    from python_libtorrent import get_libtorrent, get_platform

    lt = get_libtorrent()
except Exception, e:
    import libtorrent as lt

import xbmc
import xbmcgui

from platformcode import config
from core import httptools
from core import scrapertools
from core import filetools


def play(url, xlistitem={}, is_view=None, subtitle="", item=None):
    allocate = True
    try:
        import platform
        xbmc.log("XXX KODI XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        xbmc.log("OS platform: %s %s" % (platform.system(), platform.release()))
        xbmc.log("xbmc/kodi version: %s" % xbmc.getInfoLabel("System.BuildVersion"))
        xbmc_version = int(xbmc.getInfoLabel("System.BuildVersion")[:2])
        xbmc.log("xbmc/kodi version number: %s" % xbmc_version)
        xbmc.log("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX KODI XXXX")

        _platform = get_platform()
        if str(_platform['system']) in ["android_armv7", "linux_armv6", "linux_armv7"]:
            allocate = False
        # -- log ------------------------------------------------
        xbmc.log("XXX platform XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
        xbmc.log("_platform['system']: %s" % _platform['system'])
        xbmc.log("allocate: %s" % allocate)
        xbmc.log("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX platform XXXX")
        # -- ----------------------------------------------------
    except:
        pass

    DOWNLOAD_PATH = config.get_setting("downloadpath")

    # -- adfly: ------------------------------------
    if url.startswith("http://adf.ly/"):
        try:
            data = httptools.downloadpage(url).data
            url = decode_adfly(data)
        except:
            ddd = xbmcgui.Dialog()
            ddd.ok("alfa-MCT: Sin soporte adf.ly",
                   "El script no tiene soporte para el acortador de urls adf.ly.", "", "url: " + url)
            return

    # -- Necesario para algunas webs ----------------------------
    if not url.endswith(".torrent") and not url.startswith("magnet"):
        t_file = scrapertools.get_header_from_response(url, header_to_get="location")
        if len(t_file) > 0:
            url = t_file
            t_file = scrapertools.get_header_from_response(url, header_to_get="location")
        if len(t_file) > 0:
            url = t_file

    # -- Crear dos carpetas en descargas para los archivos ------
    save_path_videos = os.path.join(DOWNLOAD_PATH, "torrent-videos")
    save_path_torrents = os.path.join(DOWNLOAD_PATH, "torrent-torrents")
    if not os.path.exists(save_path_torrents): os.mkdir(save_path_torrents)

    # -- Usar - archivo torrent desde web, magnet o HD ---------
    if not os.path.isfile(url) and not url.startswith("magnet"):
        # -- http - crear archivo torrent -----------------------
        data = url_get(url)
        # -- El nombre del torrent será el que contiene en los --
        # -- datos.                                             -
        re_name = urllib.unquote(scrapertools.scrapertools.find_single_match(data, ':name\d+:(.*?)\d+:'))
        torrent_file = filetools.join(save_path_torrents, filetools.encode(re_name + '.torrent'))

        f = open(torrent_file, 'wb')
        f.write(data)
        f.close()
    elif os.path.isfile(url):
        # -- file - para usar torrens desde el HD ---------------
        torrent_file = url
    else:
        # -- magnet ---------------------------------------------
        torrent_file = url
    # -----------------------------------------------------------

    # -- MCT - MiniClienteTorrent -------------------------------
    ses = lt.session()

    # -- log ----------------------------------------------------
    xbmc.log("### Init session ########")
    xbmc.log(lt.version)
    xbmc.log("#########################")
    # -- --------------------------------------------------------

    ses.add_dht_router("router.bittorrent.com", 6881)
    ses.add_dht_router("router.utorrent.com", 6881)
    ses.add_dht_router("dht.transmissionbt.com", 6881)

    trackers = [
        "udp://tracker.openbittorrent.com:80/announce",
        "http://tracker.torrentbay.to:6969/announce",
        "http://tracker.pow7.com/announce",
        "udp://tracker.ccc.de:80/announce",
        "udp://open.demonii.com:1337",

        "http://9.rarbg.com:2710/announce",
        "http://bt.careland.com.cn:6969/announce",
        "http://explodie.org:6969/announce",
        "http://mgtracker.org:2710/announce",
        "http://tracker.best-torrents.net:6969/announce",
        "http://tracker.tfile.me/announce",
        "http://tracker1.wasabii.com.tw:6969/announce",
        "udp://9.rarbg.com:2710/announce",
        "udp://9.rarbg.me:2710/announce",
        "udp://coppersurfer.tk:6969/announce",

        "http://www.spanishtracker.com:2710/announce",
        "http://www.todotorrents.com:2710/announce",
    ]

    video_file = ""
    # -- magnet2torrent -----------------------------------------
    if torrent_file.startswith("magnet"):
        try:
            import zlib
            btih = hex(zlib.crc32(
                scrapertools.scrapertools.find_single_match(torrent_file, 'magnet:\?xt=urn:(?:[A-z0-9:]+|)([A-z0-9]{32})')) & 0xffffffff)
            files = [f for f in os.listdir(save_path_torrents) if os.path.isfile(os.path.join(save_path_torrents, f))]
            for file in files:
                if btih in os.path.basename(file):
                    torrent_file = os.path.join(save_path_torrents, file)
        except:
            pass

    if torrent_file.startswith("magnet"):
        try:
            tempdir = tempfile.mkdtemp()
        except IOError:
            tempdir = os.path.join(save_path_torrents, "temp")
            if not os.path.exists(tempdir):
                os.mkdir(tempdir)
        params = {
            'save_path': tempdir,
            'trackers': trackers,
            'storage_mode': lt.storage_mode_t.storage_mode_allocate,
            'paused': False,
            'auto_managed': True,
            'duplicate_is_error': True
        }
        h = lt.add_magnet_uri(ses, torrent_file, params)
        dp = xbmcgui.DialogProgress()
        dp.create('alfa-MCT')
        while not h.has_metadata():
            message, porcent, msg_file, s, download = getProgress(h, "Creando torrent desde magnet")
            dp.update(porcent, message, msg_file)
            if s.state == 1: download = 1
            if dp.iscanceled():
                dp.close()
                remove_files(download, torrent_file, video_file, ses, h)
                return
            h.force_dht_announce()
            xbmc.sleep(1000)

        dp.close()
        info = h.get_torrent_info()
        data = lt.bencode(lt.create_torrent(info).generate())

        torrent_file = os.path.join(save_path_torrents,
                                    unicode(info.name() + "-" + btih, "'utf-8'", errors="replace") + ".torrent")
        f = open(torrent_file, 'wb')
        f.write(data)
        f.close()
        ses.remove_torrent(h)
        shutil.rmtree(tempdir)
    # -----------------------------------------------------------

    # -- Archivos torrent ---------------------------------------
    e = lt.bdecode(open(torrent_file, 'rb').read())
    info = lt.torrent_info(e)

    # -- El más gordo o uno de los más gordo se entiende que es -
    # -- el vídeo o es el vídeo que se usará como referencia    -
    # -- para el tipo de archivo                                -
    xbmc.log("##### Archivos ## %s ##" % len(info.files()))
    _index_file, _video_file, _size_file = get_video_file(info)

    # -- Prioritarizar/Seleccionar archivo-----------------------
    _index, video_file, video_size, len_files = get_video_files_sizes(info)
    if len_files == 0:
        dp = xbmcgui.Dialog().ok("No se puede reproducir", "El torrent no contiene ningún archivo de vídeo")

    if _index == -1:
        _index = _index_file
        video_file = _video_file
        video_size = _size_file

    _video_file_ext = os.path.splitext(_video_file)[1]
    xbmc.log("##### _video_file_ext ## %s ##" % _video_file_ext)
    if (_video_file_ext == ".avi" or _video_file_ext == ".mp4") and allocate:
        xbmc.log("##### storage_mode_t.storage_mode_allocate (" + _video_file_ext + ") #####")
        h = ses.add_torrent({'ti': info, 'save_path': save_path_videos, 'trackers': trackers,
                             'storage_mode': lt.storage_mode_t.storage_mode_allocate})
    else:
        xbmc.log("##### storage_mode_t.storage_mode_sparse (" + _video_file_ext + ") #####")
        h = ses.add_torrent({'ti': info, 'save_path': save_path_videos, 'trackers': trackers,
                             'storage_mode': lt.storage_mode_t.storage_mode_sparse})
        allocate = True
    # -----------------------------------------------------------

    # -- Descarga secuencial - trozo 1, trozo 2, ... ------------
    h.set_sequential_download(True)

    h.force_reannounce()
    h.force_dht_announce()

    # -- Inicio de variables para 'pause' automático cuando el  -
    # -- el vídeo se acerca a una pieza sin completar           -
    is_greater_num_pieces = False
    is_greater_num_pieces_plus = False
    is_greater_num_pieces_pause = False

    porcent4first_pieces = int(video_size * 0.000000005)
    if porcent4first_pieces < 10: porcent4first_pieces = 10
    if porcent4first_pieces > 100: porcent4first_pieces = 100
    porcent4last_pieces = int(porcent4first_pieces / 2)

    num_pieces_to_resume = int(video_size * 0.0000000025)
    if num_pieces_to_resume < 5: num_pieces_to_resume = 5
    if num_pieces_to_resume > 25: num_pieces_to_resume = 25

    xbmc.log("##### porcent4first_pieces ## %s ##" % porcent4first_pieces)
    xbmc.log("##### porcent4last_pieces ## %s ##" % porcent4last_pieces)
    xbmc.log("##### num_pieces_to_resume ## %s ##" % num_pieces_to_resume)

    # -- Prioritarizar o seleccionar las piezas del archivo que -
    # -- se desea reproducir con 'file_priorities'              -
    piece_set = set_priority_pieces(h, _index, video_file, video_size,
                                    porcent4first_pieces, porcent4last_pieces, allocate)

    # -- Crear diálogo de progreso para el primer bucle ---------
    dp = xbmcgui.DialogProgress()
    dp.create('alfa-MCT')

    _pieces_info = {}

    # -- Doble bucle anidado ------------------------------------
    # -- Descarga - Primer bucle                                -
    while not h.is_seed():
        s = h.status()

        xbmc.sleep(100)

        # -- Recuperar los datos del progreso -------------------
        message, porcent, msg_file, s, download = getProgress(h, video_file, _pf=_pieces_info)

        # -- Si hace 'checking' existe descarga -----------------
        # -- 'download' Se usará para saber si hay datos        -
        # -- descargados para el diálogo de 'remove_files'      -
        if s.state == 1: download = 1

        # -- Player - play --------------------------------------
        # -- Comprobar si se han completado las piezas para el  -
        # -- inicio del vídeo                                   -
        first_pieces = True

        _c = 0
        for i in range(piece_set[0], piece_set[porcent4first_pieces]):
            first_pieces &= h.have_piece(i)
            if h.have_piece(i): _c += 1
        _pieces_info = {'current': 0, 'continuous': "%s/%s" % (_c, porcent4first_pieces), 'continuous2': "",
                        'have': h.status().num_pieces, 'len': len(piece_set)}

        last_pieces = True
        if not allocate:
            _c = len(piece_set) - 1;
            _cc = 0
            for i in range(len(piece_set) - porcent4last_pieces, len(piece_set)):
                last_pieces &= h.have_piece(i)
                if h.have_piece(i): _c -= 1; _cc += 1
            _pieces_info['continuous2'] = "[%s/%s] " % (_cc, porcent4last_pieces)

        if is_view != "Ok" and first_pieces and last_pieces:
            _pieces_info['continuous2'] = ""
            xbmc.log("##### porcent [%.2f%%]" % (s.progress * 100))
            is_view = "Ok"
            dp.close()

            # -- Player - Ver el vídeo --------------------------
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()

            ren_video_file = os.path.join(save_path_videos, video_file)
            try:
                playlist.add(ren_video_file, xlistitem)
            except:
                playlist.add(ren_video_file)

            if xbmc_version < 17:
                player = play_video(xbmc.PLAYER_CORE_AUTO)
            else:
                player = play_video()
            player.play(playlist)

            # -- Contador de cancelaciones para la ventana de   -
            # -- 'pause' automático                             -
            is_greater_num_pieces_canceled = 0
            continuous_pieces = 0
            porcent_time = 0.00
            current_piece = 0
            set_next_continuous_pieces = porcent4first_pieces

            # -- Impedir que kodi haga 'resume' a un archivo ----
            # -- que se reprodujo con anterioridad y que se     -
            # -- eliminó para impedir que intente la reprucción -
            # -- en una pieza que aún no se ha completado y se  -
            # -- active 'pause' automático                      -
            not_resume = True

            # -- Bandera subTítulos
            _sub = False

            # -- Segundo bucle - Player - Control de eventos ----
            while player.isPlaying():
                xbmc.sleep(100)

                # -- Añadir subTítulos
                if subtitle != "" and not _sub:
                    _sub = True
                    player.setSubtitles(subtitle)

                # -- Impedir que kodi haga 'resume' al inicio ---
                # -- de la descarga de un archivo conocido      -
                if not_resume:
                    player.seekTime(0)
                    not_resume = False

                # -- Control 'pause' automático                 -
                continuous_pieces = count_completed_continuous_pieces(h, piece_set)

                if xbmc.Player().isPlaying():

                    # -- Porcentage del progreso del vídeo ------
                    player_getTime = player.getTime()
                    player_getTotalTime = player.getTotalTime()
                    porcent_time = player_getTime / player_getTotalTime * 100

                    # -- Pieza que se está reproduciendo --------
                    current_piece = int(porcent_time / 100 * len(piece_set))

                    # -- Banderas de control --------------------
                    is_greater_num_pieces = (current_piece > continuous_pieces - num_pieces_to_resume)
                    is_greater_num_pieces_plus = (current_piece + porcent4first_pieces > continuous_pieces)
                    is_greater_num_pieces_finished = (current_piece + porcent4first_pieces >= len(piece_set))

                    # -- Activa 'pause' automático --------------
                    if is_greater_num_pieces and not player.paused and not is_greater_num_pieces_finished:
                        is_greater_num_pieces_pause = True
                        player.pause()

                    if continuous_pieces >= set_next_continuous_pieces:
                        set_next_continuous_pieces = continuous_pieces + num_pieces_to_resume
                    next_continuous_pieces = str(continuous_pieces - current_piece) + "/" + str(
                        set_next_continuous_pieces - current_piece)
                    _pieces_info = {'current': current_piece, 'continuous': next_continuous_pieces,
                                    'continuous2': _pieces_info['continuous2'], 'have': h.status().num_pieces,
                                    'len': len(piece_set)}

                    # si es un archivo de la videoteca enviar a marcar como visto
                    if item.strm_path:
                        from platformcode import xbmc_videolibrary
                        xbmc_videolibrary.mark_auto_as_watched(item)

                # -- Cerrar el diálogo de progreso --------------
                if player.resumed:
                    dp.close()

                # -- Mostrar el diálogo de progreso -------------
                if player.paused:
                    # -- Crear diálogo si no existe -------------
                    if not player.statusDialogoProgress:
                        dp = xbmcgui.DialogProgress()
                        dp.create('alfa-MCT')
                        player.setDialogoProgress()

                    # -- Diálogos de estado en el visionado -----
                    if not h.is_seed():
                        # -- Recuperar los datos del progreso ---
                        message, porcent, msg_file, s, download = getProgress(h, video_file, _pf=_pieces_info)
                        dp.update(porcent, message, msg_file)
                    else:
                        dp.update(100, "Descarga completa: " + video_file)

                    # -- Se canceló el progreso en el visionado -
                    # -- Continuar                              -
                    if dp.iscanceled():
                        dp.close()
                        player.pause()

                    # -- Se canceló el progreso en el visionado -
                    # -- en la ventana de 'pause' automático.   -
                    # -- Parar si el contador llega a 3         -
                    if dp.iscanceled() and is_greater_num_pieces_pause:
                        is_greater_num_pieces_canceled += 1
                        if is_greater_num_pieces_canceled == 3:
                            player.stop()

                    # -- Desactiva 'pause' automático y ---------
                    # -- reinicia el contador de cancelaciones  -
                    if not dp.iscanceled() and not is_greater_num_pieces_plus and is_greater_num_pieces_pause:
                        dp.close()
                        player.pause()
                        is_greater_num_pieces_pause = False
                        is_greater_num_pieces_canceled = 0

                    # -- El usuario cancelo el visionado --------
                    # -- Terminar                               -
                    if player.ended:
                        # -- Diálogo eliminar archivos ----------
                        remove_files(download, torrent_file, video_file, ses, h)
                        return

        # -- Kodi - Se cerró el visionado -----------------------
        # -- Continuar | Terminar                               -
        if is_view == "Ok" and not xbmc.Player().isPlaying():

            if info.num_files() == 1:
                # -- Diálogo continuar o terminar ---------------
                d = xbmcgui.Dialog()
                ok = d.yesno('alfa-MCT', 'XBMC-Kodi Cerró el vídeo.', '¿Continuar con la sesión?')
            else:
                ok = False
            # -- SI ---------------------------------------------
            if ok:
                # -- Continuar: ---------------------------------
                is_view = None
            else:
                # -- Terminar: ----------------------------------
                # -- Comprobar si el vídeo pertenece a una ------
                # -- lista de archivos                          -
                _index, video_file, video_size, len_files = get_video_files_sizes(info)
                if _index == -1 or len_files == 1:
                    # -- Diálogo eliminar archivos --------------
                    remove_files(download, torrent_file, video_file, ses, h)
                    return
                else:
                    # -- Lista de archivos. Diálogo de opciones -
                    piece_set = set_priority_pieces(h, _index, video_file, video_size,
                                                    porcent4first_pieces, porcent4last_pieces, allocate)
                    is_view = None
                    dp = xbmcgui.DialogProgress()
                    dp.create('alfa-MCT')

        # -- Mostar progeso antes del visionado -----------------
        if is_view != "Ok":
            dp.update(porcent, message, msg_file)

        # -- Se canceló el progreso antes del visionado ---------
        # -- Terminar                                           -
        if dp.iscanceled():
            dp.close()
            # -- Comprobar si el vídeo pertenece a una lista de -
            # -- archivos                                       -
            _index, video_file, video_size, len_files = get_video_files_sizes(info)
            if _index == -1 or len_files == 1:
                # -- Diálogo eliminar archivos ------------------
                remove_files(download, torrent_file, video_file, ses, h)
                return
            else:
                # -- Lista de archivos. Diálogo de opciones -----
                piece_set = set_priority_pieces(h, _index, video_file, video_size,
                                                porcent4first_pieces, porcent4last_pieces, allocate)
                is_view = None
                dp = xbmcgui.DialogProgress()
                dp.create('alfa-MCT')

    # -- Kodi - Error? - No debería llegar aquí -----------------
    if is_view == "Ok" and not xbmc.Player().isPlaying():
        dp.close()
        # -- Diálogo eliminar archivos --------------------------
        remove_files(download, torrent_file, video_file, ses, h)

    return


# -- Progreso de la descarga ------------------------------------
def getProgress(h, video_file, _pf={}):
    if len(_pf) > 0:
        _pf_msg = "[%s] [%s] %s[%s] [%s]" % (
            _pf['current'], _pf['continuous'], _pf['continuous2'], _pf['have'], _pf['len'])
    else:
        _pf_msg = ""

    s = h.status()

    state_str = ['queued', 'checking', 'downloading metadata', \
                 'downloading', 'finished', 'seeding', 'allocating', 'checking fastresume']

    message = '%.2f%% d:%.1f kb/s u:%.1f kb/s p:%d s:%d %s' % \
              (s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
               s.num_peers, s.num_seeds, state_str[s.state])
    porcent = int(s.progress * 100)

    download = (s.progress * 100)

    if "/" in video_file: video_file = video_file.split("/")[1]
    msg_file = video_file

    if len(msg_file) > 50:
        msg_file = msg_file.replace(video_file,
                                    os.path.splitext(video_file)[0][:40] + "... " + os.path.splitext(video_file)[1])
    msg_file = msg_file + "[CR]" + "%.2f MB" % (s.total_wanted / 1048576.0) + " - " + _pf_msg

    return (message, porcent, msg_file, s, download)


# -- Clase play_video - Controlar eventos -----------------------
class play_video(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self.paused = False
        self.resumed = True
        self.statusDialogoProgress = False
        self.ended = False

    def onPlayBackPaused(self):
        self.paused = True
        self.resumed = False

    def onPlayBackResumed(self):
        self.paused = False
        self.resumed = True
        self.statusDialogoProgress = False

    def is_paused(self):
        return self.paused

    def setDialogoProgress(self):
        self.statusDialogoProgress = True

    def is_started(self):
        self.ended = False

    def is_ended(self):
        self.ended = True


# -- Conseguir el nombre un alchivo de vídeo del metadata -------
# -- El más gordo o uno de los más gordo se entiende que es el  -
# -- vídeo o es vídeo que se usará como referencia para el tipo -
# -- de archivo                                                 -
def get_video_file(info):
    size_file = 0
    for i, f in enumerate(info.files()):
        if f.size > size_file:
            video_file = f.path.replace("\\", "/")
            size_file = f.size
            index_file = i
    return index_file, video_file, size_file


# -- Listado de selección del vídeo a prioritarizar -------------
def get_video_files_sizes(info):
    opciones = {}
    vfile_name = {}
    vfile_size = {}

    # -- Eliminar errores con tíldes -----------------------------
    for i, f in enumerate(info.files()):
        _title = unicode(f.path, "iso-8859-1", errors="replace")
        _title = unicode(f.path, "'utf-8'", errors="replace")

    extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg',
                       '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg',
                       '.mpe', '.mp4', '.ogg', '.rar', '.wmv', '.zip']

    for i, f in enumerate(info.files()):
        _index = int(i)
        _title = f.path.replace("\\", "/")
        _size = f.size

        _file_name = os.path.splitext(_title)[0]
        if "/" in _file_name: _file_name = _file_name.split('/')[1]

        _file_ext = os.path.splitext(_title)[1]

        if _file_ext in extensions_list:
            index = len(opciones)
            _caption = str(index) + \
                       " - " + \
                       _file_name + _file_ext + \
                       " - %.2f MB" % (_size / 1048576.0)

            vfile_name[index] = _title
            vfile_size[index] = _size

            opciones[i] = _caption

    if len(opciones) > 1:
        d = xbmcgui.Dialog()
        seleccion = d.select("alfa-MCT: Lista de vídeos", opciones.values())
    else:
        seleccion = 0

    index = opciones.keys()[seleccion]
    if seleccion == -1:
        vfile_name[seleccion] = ""
        vfile_size[seleccion] = 0
        index = seleccion

    return index, vfile_name[seleccion], vfile_size[seleccion], len(opciones)


# -- Preguntar si se desea borrar lo descargado -----------------
def remove_files(download, torrent_file, video_file, ses, h):
    dialog_view = False
    torrent = False

    if os.path.isfile(torrent_file):
        dialog_view = True
        torrent = True

    if download > 0:
        dialog_view = True

    if "/" in video_file: video_file = video_file.split("/")[0]

    if dialog_view:
        d = xbmcgui.Dialog()
        ok = d.yesno('alfa-MCT', 'Borrar las descargas del video', video_file)

        # -- SI -------------------------------------------------
        if ok:
            # -- Borrar archivo - torrent -----------------------
            if torrent:
                os.remove(torrent_file)
            # -- Borrar carpeta/archivos y sesión - vídeo -------
            ses.remove_torrent(h, 1)
            xbmc.log("### End session #########")
        else:
            # -- Borrar sesión ----------------------------------
            ses.remove_torrent(h)
            xbmc.log("### End session #########")
    else:
        # -- Borrar sesión --------------------------------------
        ses.remove_torrent(h)
        xbmc.log("### End session #########")

    return


# -- Descargar de la web los datos para crear el torrent --------
# -- Si queremos aligerar el script mct.py se puede importar la -
# -- función del conentor torrent.py                            -
def url_get(url, params={}, headers={}):
    from contextlib import closing

    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:20.0) Gecko/20100101 Firefox/20.0"

    if params:
        import urllib
        url = "%s?%s" % (url, urllib.urlencode(params))

    req = urllib2.Request(url)
    req.add_header("User-Agent", USER_AGENT)

    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with closing(urllib2.urlopen(req)) as response:
            data = response.read()
            if response.headers.get("Content-Encoding", "") == "gzip":
                import zlib
                return zlib.decompressobj(16 + zlib.MAX_WBITS).decompress(data)
            return data
    except urllib2.HTTPError:
        return None


# -- Contar las piezas contiguas completas del vídeo ------------
def count_completed_continuous_pieces(h, piece_set):
    not_zero = 0
    for i, _set in enumerate(piece_set):
        if not h.have_piece(_set):
            break
        else:
            not_zero = 1
    return i + not_zero


# -- Prioritarizar o seleccionar las piezas del archivo que se  -
# -- desea reproducir con 'file_priorities' estableciendo a 1   -
# -- el archivo deseado y a 0 el resto de archivos almacenando  -
# -- en una lista los índices de de las piezas del archivo      -
def set_priority_pieces(h, _index, video_file, video_size,
                        porcent4first_pieces, porcent4last_pieces, allocate):
    for i, _set in enumerate(h.file_priorities()):
        if i != _index:
            h.file_priority(i, 0)
        else:
            h.file_priority(i, 1)

    piece_set = []
    for i, _set in enumerate(h.piece_priorities()):
        if _set == 1: piece_set.append(i)

    if not allocate:
        for i in range(0, porcent4first_pieces):
            h.set_piece_deadline(piece_set[i], 10000)

        for i in range(len(piece_set) - porcent4last_pieces, len(piece_set)):
            h.set_piece_deadline(piece_set[i], 10000)

    return piece_set


def decode_adfly(data):
    import base64
    ysmm = scrapertools.find_single_match(data, "var ysmm = '([^']+)'")
    left = ''
    right = ''
    for c in [ysmm[i:i + 2] for i in range(0, len(ysmm), 2)]:
        left += c[0]
        right = c[1] + right

    decoded_url = base64.b64decode(left.encode() + right.encode())[2:].decode()
    return decoded_url
