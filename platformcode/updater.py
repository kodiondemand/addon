# -*- coding: utf-8 -*-
import hashlib
import os
import shutil
import zipfile

from core import httptools, filetools, downloadtools
from platformcode import logger, platformtools, config
import json
import xbmc
import re
import xbmcaddon

addon = xbmcaddon.Addon('plugin.video.kod')

_hdr_pat = re.compile("^@@ -(\d+),?(\d+)? \+(\d+),?(\d+)? @@.*")

branch = 'master'
user = 'kodiondemand'
repo = 'addon'
addonDir = xbmc.translatePath("special://home/addons/") + "plugin.video.kod/"
maxPage = 5  # le api restituiscono 30 commit per volta, quindi se si è rimasti troppo indietro c'è bisogno di andare avanti con le pagine
trackingFile = "last_commit.txt"


def loadCommits(page=1):
    apiLink = 'https://api.github.com/repos/' + user + '/' + repo + '/commits?sha=' + branch + "&page=" + str(page)
    commitsLink = httptools.downloadpage(apiLink).data
    logger.info(apiLink)
    return json.loads(commitsLink)


def check_addon_init():
    if not addon.getSetting('addon_update_enabled'):
        return False
    logger.info('Cerco aggiornamenti..')
    commits = loadCommits()

    try:
        localCommitFile = open(addonDir+trackingFile, 'r+')
    except:
        calcCurrHash()
        localCommitFile = open(addonDir + trackingFile, 'r+')
    localCommitSha = localCommitFile.read()
    localCommitSha = localCommitSha.replace('\n', '') # da testare
    logger.info('Commit locale: ' + localCommitSha)
    updated = False

    pos = None
    for n, c in enumerate(commits):
        if c['sha'] == localCommitSha:
            pos = n
            break
    else:
        # evitiamo che dia errore perchè il file è già in uso
        localCommitFile.close()
        updateFromZip()
        return True

    if pos > 0:
        changelog = ''
        nCommitApplied = 0
        for c in reversed(commits[:pos]):
            commit = httptools.downloadpage(c['url']).data
            commitJson = json.loads(commit)
            logger.info('aggiornando a' + commitJson['sha'])
            alreadyApplied = True

            for file in commitJson['files']:
                if file["filename"] == trackingFile:  # il file di tracking non si modifica
                    continue
                else:
                    logger.info(file["filename"])
                    if file['status'] == 'modified' or file['status'] == 'added':
                        if 'patch' in file:
                            text = ""
                            try:
                                localFile = open(addonDir + file["filename"], 'r+')
                                for line in localFile:
                                    text += line
                            except IOError: # nuovo file
                                localFile = open(addonDir + file["filename"], 'w')

                            patched = apply_patch(text, (file['patch']+'\n').encode('utf-8'))
                            if patched != text:  # non eseguo se già applicata (es. scaricato zip da github)
                                if getSha(patched) == file['sha']:
                                    localFile.seek(0)
                                    localFile.truncate()
                                    localFile.writelines(patched)
                                    localFile.close()
                                    alreadyApplied = False
                                else:  # nel caso ci siano stati problemi
                                    logger.info('lo sha non corrisponde, scarico il file')
                                    downloadtools.downloadfile(file['raw_url'], addonDir + file['filename'],
                                                               silent=True, continuar=True)
                        else:  # è un file NON testuale, lo devo scaricare
                            # se non è già applicato
                            if not (filetools.isfile(addonDir + file['filename']) and getSha(
                                    filetools.read(addonDir + file['filename']) == file['sha'])):
                                downloadtools.downloadfile(file['raw_url'], addonDir + file['filename'], silent=True, continuar=True)
                                alreadyApplied = False
                    elif file['status'] == 'removed':
                        try:
                            filetools.remove(addonDir+file["filename"])
                            alreadyApplied = False
                        except:
                            pass
                    elif file['status'] == 'renamed':
                        # se non è già applicato
                        if not (filetools.isfile(addonDir + file['filename']) and getSha(
                                filetools.read(addonDir + file['filename']) == file['sha'])):
                            dirs = file['filename'].split('/')
                            for d in dirs[:-1]:
                                if not filetools.isdir(addonDir + d):
                                    filetools.mkdir(addonDir + d)
                            filetools.move(addonDir + file['previous_filename'], addonDir + file['filename'])
                            alreadyApplied = False
            if not alreadyApplied:  # non mando notifica se già applicata (es. scaricato zip da github)
                changelog += commitJson['commit']['message'] + " | "
                nCommitApplied += 1
        if addon.getSetting("addon_update_message"):
            time = nCommitApplied * 2000 if nCommitApplied < 10 else 20000
            platformtools.dialog_notification('Kodi on Demand', changelog, time)

        localCommitFile.seek(0)
        localCommitFile.truncate()
        localCommitFile.writelines(c['sha'])
        localCommitFile.close()

    else:
        logger.info('Nessun nuovo aggiornamento')

    return updated


def calcCurrHash():
    from lib import githash
    treeHash = githash.tree_hash(addonDir).hexdigest()
    logger.info('tree hash: ' + treeHash)
    commits = loadCommits()
    lastCommitSha = commits[0]['sha']
    page = 1
    while commits and page <= maxPage:
        found = False
        for n, c in enumerate(commits):
             if c['commit']['tree']['sha'] == treeHash:
                localCommitFile = open(addonDir + trackingFile, 'w')
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
        updateFromZip()
        # se ha scaricato lo zip si trova di sicuro all'ultimo commit
        localCommitFile = open(addonDir + trackingFile, 'w')
        localCommitFile.write(lastCommitSha)
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
  return t


def getSha(fileText):
    return hashlib.sha1("blob " + str(len(fileText)) + "\0" + fileText).hexdigest()


def updateFromZip():
    platformtools.dialog_notification('Kodi on Demand', 'Aggiornamento in corso...')

    remotefilename = 'https://github.com/' + user + "/" + repo + "/archive/" + branch + ".zip"
    localfilename = xbmc.translatePath("special://home/addons/") + "plugin.video.kod.update.zip"
    logger.info("kodiondemand.core.updater remotefilename=%s" % remotefilename)
    logger.info("kodiondemand.core.updater localfilename=%s" % localfilename)
    logger.info("kodiondemand.core.updater descarga fichero...")

    import urllib
    urllib.urlretrieve(remotefilename, localfilename)

    # Lo descomprime
    logger.info("kodiondemand.core.updater descomprime fichero...")
    destpathname = xbmc.translatePath("special://home/addons/")
    logger.info("kodiondemand.core.updater destpathname=%s" % destpathname)
    unzipper = ziptools()
    unzipper.extract(localfilename, destpathname)

    # puliamo tutto
    shutil.rmtree(addonDir)

    filetools.rename(destpathname + "addon-" + branch, addonDir)

    # Borra el zip descargado
    logger.info("kodiondemand.core.updater borra fichero...")
    os.remove(localfilename)
    # os.remove(temp_dir)
    platformtools.dialog_notification('Kodi on Demand', 'Aggiornamento completato!')


class ziptools:
    def extract(self, file, dir, folder_to_extract="", overwrite_question=False, backup=False):
        logger.info("file=%s" % file)
        logger.info("dir=%s" % dir)

        if not dir.endswith(':') and not os.path.exists(dir):
            os.mkdir(dir)

        zf = zipfile.ZipFile(file)
        if not folder_to_extract:
            self._createstructure(file, dir)
        num_files = len(zf.namelist())

        for nameo in zf.namelist():
            name = nameo.replace(':', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace('"', '_').replace('?', '_').replace('*', '_')
            logger.info("name=%s" % nameo)
            if not name.endswith('/'):
                logger.info("no es un directorio")
                try:
                    (path, filename) = os.path.split(os.path.join(dir, name))
                    logger.info("path=%s" % path)
                    logger.info("name=%s" % name)
                    if folder_to_extract:
                        if path != os.path.join(dir, folder_to_extract):
                            break
                    else:
                        os.makedirs(path)
                except:
                    pass
                if folder_to_extract:
                    outfilename = os.path.join(dir, filename)

                else:
                    outfilename = os.path.join(dir, name)
                logger.info("outfilename=%s" % outfilename)
                try:
                    if os.path.exists(outfilename) and overwrite_question:
                        from platformcode import platformtools
                        dyesno = platformtools.dialog_yesno("El archivo ya existe",
                                                            "El archivo %s a descomprimir ya existe" \
                                                            ", ¿desea sobrescribirlo?" \
                                                            % os.path.basename(outfilename))
                        if not dyesno:
                            break
                        if backup:
                            import time
                            import shutil
                            hora_folder = "Copia seguridad [%s]" % time.strftime("%d-%m_%H-%M", time.localtime())
                            backup = os.path.join(config.get_data_path(), 'backups', hora_folder, folder_to_extract)
                            if not os.path.exists(backup):
                                os.makedirs(backup)
                            shutil.copy2(outfilename, os.path.join(backup, os.path.basename(outfilename)))

                    outfile = open(outfilename, 'wb')
                    outfile.write(zf.read(nameo))
                except:
                    logger.error("Error en fichero " + nameo)

    def _createstructure(self, file, dir):
        self._makedirs(self._listdirs(file), dir)

    def create_necessary_paths(filename):
        try:
            (path, name) = os.path.split(filename)
            os.makedirs(path)
        except:
            pass

    def _makedirs(self, directories, basedir):
        for dir in directories:
            curdir = os.path.join(basedir, dir)
            if not os.path.exists(curdir):
                os.mkdir(curdir)

    def _listdirs(self, file):
        zf = zipfile.ZipFile(file)
        dirs = []
        for name in zf.namelist():
            if name.endswith('/'):
                dirs.append(name)

        dirs.sort()
        return dirs