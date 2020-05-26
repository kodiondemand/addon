import random
import string
import time

from core import httptools
from platformcode import platformtools, config

baseUrl = 'https://www.1secmail.com/api/v1/'
defDomain = '1secmail.com'

def splitMail(mail):
    if '@' in mail:
        user, domain = mail.split('@')
    else:
        user = mail
        domain = defDomain
    return user, domain

def getMessages(mail):
    """
    :param user: user@1secmail.com
    :return: json containing inbox id and subjects
    """
    user, domain = splitMail(mail)
    apiUrl = baseUrl + '?action=getMessages&login=' + user + '&domain=' + domain
    return httptools.downloadpage(apiUrl).json


def readLastMessage(mail):
    user, domain = splitMail(mail)
    try:
        id = getMessages(mail)[0]['id']
    except:
        return None
    apiUrl = baseUrl + '?action=readMessage&login=' + user + '&domain=' + domain + '&id=' + str(id)
    return httptools.downloadpage(apiUrl).json


def waitForMail(mail, timeout=50):
    dialog = platformtools.dialog_progress(config.get_localized_string(20000),
                                           'verifica tramite mail richiesta dal sito, sono in attesa di nuove mail sulla casella ' + mail)
    secs = 0
    while secs < timeout:
        msg = readLastMessage(mail)
        if msg:
            dialog.close()
            return msg
        else:
            time.sleep(1)
            secs += 1
        if dialog.iscanceled():
            break
    return None

def getRandom(len=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(len)) + '@' + defDomain