# -*- coding: utf-8 -*-
import io
import os
import shutil
from lib.six import BytesIO

from core import filetools
from platformcode import config, logger, platformtools
import json
import xbmc
import re
import xbmcaddon
from lib import githash
try:
    import urllib.request as urllib
except ImportError:
    import urllib
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
addon = xbmcaddon.Addon('plugin.video.kod')
addonname = addon.getAddonInfo('name')

_hdr_pat = re.compile("^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@.*")

branch = 'stable'
user = 'kodiondemand'
repo = 'addon'
addonDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
maxPage = 5  # le api restituiscono 30 commit per volta, quindi se si è rimasti troppo indietro c'è bisogno di andare avanti con le pagine
trackingFile = "last_commit.txt"
changelogFile = "special://profile/addon_data/plugin.video.kod/changelog.txt"


def loadCommits(page=1):
    apiLink = 'https://api.github.com/repos/' + user + '/' + repo + '/commits?sha=' + branch + "&page=" + str(page)
    logger.info(apiLink)
    # riprova ogni secondo finchè non riesce (ad esempio per mancanza di connessione)
    for n in range(10):
        try:
            commitsLink = urllib.urlopen(apiLink).read()
            ret = json.loads(commitsLink)
            break
        except:
            xbmc.sleep(1000)
    else:
        platformtools.dialog_notification(addonname, config.get_localized_string(70675))
        ret = None

    return ret


# ret -> aggiornato, necessita reload service
def check(background=False):
    if not addon.getSetting('addon_update_enabled'):
        return False, False
    logger.info('Cerco aggiornamenti..')
    commits = loadCommits()
    if not commits:
        return False, False

    try:
        localCommitFile = open(os.path.join(addonDir, trackingFile), 'r+')
    except:
        calcCurrHash()
        localCommitFile = open(os.path.join(addonDir, trackingFile), 'r+')
    localCommitSha = localCommitFile.read()
    localCommitSha = localCommitSha.replace('\n', '') # da testare
    logger.info('Commit locale: ' + localCommitSha)
    updated = False
    serviceChanged = False

    pos = None
    for n, c in enumerate(commits):
        if c['sha'] == localCommitSha:
            pos = n
            break
    else:
        # evitiamo che dia errore perchè il file è già in uso
        localCommitFile.close()
        calcCurrHash()
        return True, False

    if pos > 0:
        changelog = ''
        poFilesChanged = False
        try:
            for c in reversed(commits[:pos]):
                commit = urllib.urlopen(c['url']).read()
                commitJson = json.loads(commit)
                # evitiamo di applicare i merge commit
                if 'Merge' in commitJson['commit']['message']:
                    continue
                logger.info('aggiornando a ' + commitJson['sha'])
                alreadyApplied = True

                # major update
                if len(commitJson['files']) > 50:
                    localCommitFile.close()
                    c['sha'] = updateFromZip('Aggiornamento in corso...')
                    localCommitFile = open(os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.kod', trackingFile), 'w')  # il file di tracking viene eliminato, lo ricreo
                    changelog += commitJson['commit']['message'] + "\n"
                    poFilesChanged = True
                    serviceChanged = True
                    break

                for file in commitJson['files']:
                    if file["filename"] == trackingFile:  # il file di tracking non si modifica
                        continue
                    else:
                        logger.info(file["filename"])
                        if 'resources/language' in file["filename"]:
                            poFilesChanged = True
                        if 'service.py' in file["filename"]:
                            serviceChanged = True
                        if file['status'] == 'modified' or file['status'] == 'added':
                            if 'patch' in file:
                                text = ""
                                try:
                                    localFile = io.open(os.path.join(addonDir, file["filename"]), 'r+', encoding="utf8")
                                    text = localFile.read()
                                    if not PY3:
                                        text = text.decode('utf-8')
                                except IOError: # nuovo file
                                    # crea le cartelle se non esistono
                                    dirname = os.path.dirname(os.path.join(addonDir, file["filename"]))
                                    if not os.path.exists(dirname):
                                        os.makedirs(dirname)

                                    localFile = io.open(os.path.join(addonDir, file["filename"]), 'w', encoding="utf8")

                                patched = apply_patch(text, (file['patch']+'\n').encode('utf-8'))
                                if patched != text:  # non eseguo se già applicata (es. scaricato zip da github)
                                    alreadyApplied = False
                                    if getShaStr(patched) == file['sha']:
                                        localFile.seek(0)
                                        localFile.truncate()
                                        localFile.writelines(patched)
                                        localFile.close()
                                    else:  # nel caso ci siano stati problemi
                                        logger.info('lo sha non corrisponde, scarico il file')
                                        localFile.close()
                                        urllib.urlretrieve(file['raw_url'], os.path.join(addonDir, file['filename']))
                            else:  # è un file NON testuale, lo devo scaricare
                                # se non è già applicato
                                filename = os.path.join(addonDir, file['filename'])
                                dirname = os.path.dirname(filename)
                                if not (filetools.isfile(os.path.join(addonDir, file['filename'])) and getSha(filename) == file['sha']):
                                    if not os.path.exists(dirname):
                                        os.makedirs(dirname)
                                    urllib.urlretrieve(file['raw_url'], filename)
                                    alreadyApplied = False
                        elif file['status'] == 'removed':
                            remove(os.path.join(addonDir, file["filename"]))
                            alreadyApplied = False
                        elif file['status'] == 'renamed':
                            # se non è già applicato
                            if not (filetools.isfile(os.path.join(addonDir, file['filename'])) and getSha(os.path.join(addonDir, file['filename'])) == file['sha']):
                                dirs = file['filename'].split('/')
                                for d in dirs[:-1]:
                                    if not filetools.isdir(os.path.join(addonDir, d)):
                                        filetools.mkdir(os.path.join(addonDir, d))
                                filetools.move(os.path.join(addonDir, file['previous_filename']), os.path.join(addonDir, file['filename']))
                                alreadyApplied = False
                if not alreadyApplied:  # non mando notifica se già applicata (es. scaricato zip da github)
                    changelog += commitJson['commit']['message'] + "\n"
        except:
            import traceback
            logger.error(traceback.format_exc())
            # fallback
            localCommitFile.close()
            c['sha'] = updateFromZip('Aggiornamento in corso...')
            localCommitFile = open(
                os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.kod', trackingFile),
                'w')  # il file di tracking viene eliminato, lo ricreo

        localCommitFile.seek(0)
        localCommitFile.truncate()
        localCommitFile.writelines(c['sha'])
        localCommitFile.close()
        xbmc.executebuiltin("UpdateLocalAddons")
        if poFilesChanged:
            refreshLang()
        updated = True

        if addon.getSetting("addon_update_message"):
            if background:
                platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80040) % commits[0]['sha'][:7], time=3000, sound=False)
                with open(xbmc.translatePath(changelogFile), 'a+') as fileC:
                    fileC.write(changelog)
            elif changelog:
                platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80041) + changelog)
    else:
        logger.info('Nessun nuovo aggiornamento')

    return updated, serviceChanged


def showSavedChangelog():
    try:
        with open(xbmc.translatePath(changelogFile), 'r') as fileC:
            changelog = fileC.read()
            platformtools.dialog_ok('Kodi on Demand', 'Aggiornamenti applicati:\n' + changelog)
        os.remove(xbmc.translatePath(changelogFile))
    except:
        pass

def calcCurrHash():
    treeHash = githash.tree_hash(addonDir).hexdigest()
    logger.info('tree hash: ' + treeHash)
    commits = loadCommits()
    lastCommitSha = commits[0]['sha']
    page = 1
    while commits and page <= maxPage:
        found = False
        for n, c in enumerate(commits):
             if c['commit']['tree']['sha'] == treeHash:
                localCommitFile = open(os.path.join(addonDir, trackingFile), 'w')
                localCommitFile.write(c['sha'])
                localCommitFile.close()
                found = True
                break
        else:
            page += 1
            commits = loadCommits(page)

        if found:
            break
    else:
        logger.info('Non sono riuscito a trovare il commit attuale, scarico lo zip')
        hash = updateFromZip()
        # se ha scaricato lo zip si trova di sicuro all'ultimo commit
        localCommitFile = open(os.path.join(xbmc.translatePath("special://home/addons/"), 'plugin.video.kod', trackingFile), 'w')
        localCommitFile.write(hash if hash else lastCommitSha)
        localCommitFile.close()


# https://gist.github.com/noporpoise/16e731849eb1231e86d78f9dfeca3abc  Grazie!

def apply_patch(s,patch,revert=False):
  """
  Apply unified diff patch to string s to recover newer string.
  If revert is True, treat s as the newer string, recover older string.
  """
  s = s.splitlines(True)
  p = patch.splitlines(True)
  t = ''
  i = sl = 0
  (midx,sign) = (1,'+') if not revert else (3,'-')
  while i < len(p) and p[i].startswith(("---","+++")): i += 1 # skip header lines
  while i < len(p):
    m = _hdr_pat.match(p[i])
    if not m: raise Exception("Cannot process diff")
    i += 1
    l = int(m.group(midx))-1 + (m.group(midx+1) == '0')
    t += ''.join(s[sl:l])
    sl = l
    while i < len(p) and p[i][0] != '@':
      if i+1 < len(p) and p[i+1][0] == '\\': line = p[i][:-1]; i += 2
      else: line = p[i]; i += 1
      if len(line) > 0:
        if line[0] == sign or line[0] == ' ': t += line[1:]
        sl += (line[0] != sign)
  t += ''.join(s[sl:])
  if not PY3:
      t = t.decode('utf-8')
  return t


def getSha(path):
    try:
        f = io.open(path, 'rb', encoding="utf8")
    except:
        return ''
    size = len(f.read())
    f.seek(0)
    return githash.blob_hash(f, size).hexdigest()


def getShaStr(str):
    if PY3:
        return githash.blob_hash(BytesIO(str.encode('utf-8')), len(str.encode('utf-8'))).hexdigest()
    else:
        return githash.blob_hash(BytesIO(str), len(str)).hexdigest()



def updateFromZip(message=config.get_localized_string(80050)):
    dp = platformtools.dialog_progress_bg(config.get_localized_string(20000), message)
    dp.update(0)

    remotefilename = 'https://github.com/' + user + "/" + repo + "/archive/" + branch + ".zip"
    localfilename = filetools.join(xbmc.translatePath("special://home/addons/"), "plugin.video.kod.update.zip")
    destpathname = xbmc.translatePath("special://home/addons/")
    extractedDir = filetools.join(destpathname, "addon-" + branch)

    logger.info("remotefilename=%s" % remotefilename)
    logger.info("localfilename=%s" % localfilename)
    logger.info('extract dir: ' + extractedDir)

    # pulizia preliminare
    remove(localfilename)
    removeTree(extractedDir)

    try:
        urllib.urlretrieve(remotefilename, localfilename,
                           lambda nb, bs, fs, url=remotefilename: _pbhook(nb, bs, fs, url, dp))
    except Exception as e:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(80031))
        logger.info('Non sono riuscito a scaricare il file zip')
        logger.info(e)
        dp.close()
        return False

    # Lo descomprime
    logger.info("decompressione...")
    logger.info("destpathname=%s" % destpathname)

    if os.path.isfile(localfilename):
        logger.info('il file esiste')

    dp.update(80, config.get_localized_string(20000), config.get_localized_string(80032))

    import zipfile
    try:
        hash = fixZipGetHash(localfilename)
        logger.info(hash)

        with zipfile.ZipFile(filetools.file_open(localfilename, 'rb', vfs=False)) as zip:
            size = sum([zinfo.file_size for zinfo in zip.filelist])
            cur_size = 0
            for member in zip.infolist():
                zip.extract(member, destpathname)
                cur_size += member.file_size
                dp.update(int(80 + cur_size * 15 / size))

    except Exception as e:
        logger.info('Non sono riuscito ad estrarre il file zip')
        logger.error(e)
        import traceback
        logger.error(traceback.print_exc())
        dp.close()
        remove(localfilename)

        return False

    dp.update(95)

    # puliamo tutto
    global addonDir
    if extractedDir != addonDir:
        removeTree(addonDir)
    xbmc.sleep(1000)

    rename(extractedDir, 'plugin.video.kod')
    addonDir = filetools.join(destpathname, 'plugin.video.kod')

    logger.info("Cancellando il file zip...")
    remove(localfilename)

    dp.update(100)
    xbmc.sleep(1000)
    dp.close()
    if message != config.get_localized_string(80050):
        xbmc.executebuiltin("UpdateLocalAddons")
        refreshLang()

    return hash


def refreshLang():
    from platformcode import config
    language = config.get_localized_string(20001)
    if language == 'eng':
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
    else:
        xbmc.executebuiltin("SetGUILanguage(resource.language.en_en)")
        xbmc.executebuiltin("SetGUILanguage(resource.language.it_it)")


def remove(file):
    if os.path.isfile(file):
        try:
            os.remove(file)
        except:
            logger.info('File ' + file + ' NON eliminato')


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    if not os.access(path, os.W_OK):
        # Is the error an access error ?
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def removeTree(dir):
    if os.path.isdir(dir):
        try:
            shutil.rmtree(dir, ignore_errors=False, onerror=onerror)
        except Exception as e:
            logger.info('Cartella ' + dir + ' NON eliminata')
            logger.error(e)


def rename(dir1, dir2):
    try:
        filetools.rename(dir1, dir2, silent=True, vfs=False)
    except:
        logger.info('cartella ' + dir1 + ' NON rinominata')


# https://stackoverflow.com/questions/3083235/unzipping-file-results-in-badzipfile-file-is-not-a-zip-file
def fixZipGetHash(zipFile):
    hash = ''
    with filetools.file_open(zipFile, 'r+b', vfs=False) as f:
        data = f.read()
        pos = data.find(b'\x50\x4b\x05\x06')  # End of central directory signature
        if pos > 0:
            f.seek(pos + 20)  # +20: see secion V.I in 'ZIP format' link above.
            hash = f.read()[2:]
            f.seek(pos + 20)
            f.truncate()
            f.write(
                b'\x00\x00')  # Zip file comment length: 0 byte length; tell zip applications to stop reading.

    return str(hash)


def _pbhook(numblocks, blocksize, filesize, url, dp):
    try:
        percent = min((numblocks*blocksize*80)/filesize, 80)
        dp.update(int(percent))
    except Exception as e:
        logger.error(e)
        percent = 80
        dp.update(percent)
