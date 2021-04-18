import random
import string
import time
from ast import literal_eval

from core import httptools, support
from platformcode import platformtools, config, logger


class Mailbox:
    def __init__(self):
        self.address = self.new()
        if '@' in self.address:
            self.user, self.domain = self.address.split('@')
        else:
            self.user = None
            self.domain = None

    def new(self):
        return 'test@ciao.it'

    def inbox(self):
        pass

    def readLast(self):
        pass

    def waitForMail(self, timeout=50):
        info = 'verifica tramite mail richiesta dal sito, sono in attesa di nuove mail sulla casella ' + self.address
        # info += '\nTimeout tra ' + str(timeout) + ' secondi'
        dialog = platformtools.dialog_progress(config.get_localized_string(20000), info)
        secs = 0
        while secs < timeout:
            msg = self.readLast()
            logger.debug('Checked mail ' + self.address)
            if msg:
                dialog.close()
                logger.debug(msg)
                return msg
            else:
                time.sleep(1)
                secs += 1
                dialog.update(0, info + '\nTimeout tra ' + str(timeout-secs) + ' secondi')
            if dialog.iscanceled():
                break
        logger.debug('No mail found, timeout reached or dialog canceled')
        return None


class Email:
    def __init__(self, subject='', body='', sender='', date=''):
        self.subject = subject
        self.body = body
        self.sender = sender
        self.date = date

    def __repr__(self):
        r = "Date: " + self.date + '\n'
        r += "Subject: " + self.subject + '\n'
        r += "Sender: " + self.sender + '\n\n'
        r += self.body
        return r


class OneSecMailbox(Mailbox):
    def __init__(self):
        self.defDomain = '1secmail.com'
        self.baseUrl = 'https://www.1secmail.com/api/v1/'

        Mailbox.__init__(self)
        if not self.domain:
            self.domain = self.defDomain
            self.user = self.address

    def inbox(self):
        """
        :return: json containing inbox id and subjects
        """
        apiUrl = self.baseUrl + '?action=getMessages&login=' + self.user + '&domain=' + self.domain
        return httptools.downloadpage(apiUrl).json

    def readLast(self):
        try:
            id = self.inbox()[0]['id']
        except:
            return None
        apiUrl = self.baseUrl + '?action=readMessage&login=' + self.user + '&domain=' + self.domain + '&id=' + str(id)
        j = httptools.downloadpage(apiUrl).json

        return Email(j['subject'], j['htmlBody'], j['from'], j['date'])

    def new(self, len=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(len)) + '@' + self.defDomain


class Gmailnator(Mailbox):
    def __init__(self, domains=('.gmail', '+gmail')):
        self.baseUrl = 'https://www.gmailnator.com/'
        self.genDomains = {
            'gmailnator': 1,
            '+gmail': 2,
            '.gmail': 3
        }
        self.data = [self.genDomains[d] for d in domains]
        Mailbox.__init__(self)

    def new(self):
        self.csrf = support.match(self.baseUrl, patron='csrf-token" content="([a-z0-9]+)').match
        logger.debug(self.csrf)
        e = httptools.downloadpage(self.baseUrl + 'index/indexquery', post={'csrf_gmailnator_token': self.csrf, 'action': 'GenerateEmail', 'data[]': self.data},
                                   headers={'x-requested-with': 'XMLHttpRequest'})
        if e.success and e.data:
            return e.data
        else:
            platformtools.dialog_ok(config.get_localized_string(20000), 'Impossibile ottenere una mail temporanea')

    def inbox(self):
        #[{"content":"\n\t\t\t\t<a href=\"https:\/\/gmailnator.com\/jonathanmichaeltmp\/messageid\/#174f933a17b5f625\">\n\t\t\t\t\t<table class=\"message_container\">\n\t\t\t\t\t\t<tbody>\n\t\t\t\t\t\t\t<tr>\n\t\t\t\t\t\t\t\t<td>dsds<\/td>\n\t\t\t\t\t\t\t\t<td>body<\/td>\n\t\t\t\t\t\t\t\t<td class=\"text-right\">one minute ago<\/td>\n\t\t\t\t\t\t\t<\/tr>\n\t\t\t\t\t\t<\/tbody>\n\t\t\t\t\t<\/table>\n\t\t\t\t<\/a>"}]
        return httptools.downloadpage(self.baseUrl + 'mailbox/mailboxquery', post={'csrf_gmailnator_token': self.csrf, 'action': 'LoadMailList', 'Email_address': self.address}).json

    def readLast(self):
        inbox = self.inbox()
        if inbox:
            for m in inbox:
                email = support.match(m['content'], patron='([^\/]+)\/messageid\/#([a-z0-9]+)').match
                if email:
                    break
            else:
                return
            self.user, id = email
            #<b>subject<\/b><div>2 minutes ago</div><hr \/><div dir="ltr">body</div>
            html = httptools.downloadpage(self.baseUrl + 'mailbox/get_single_message/', post={'csrf_gmailnator_token': self.csrf, 'action': 'get_message', 'message_id': id, 'email': self.user}).data
            html = literal_eval('"""' + html + '"""')
            logger.debug(html)
            m = Email()
            # ritorna stringhe raw, devo convertirle per eliminare gli \ in piu
            m.subject, m.date, m.body = support.match(html, patron=r'Subject:\s?<\\/b>([^<]+)<\\/b><div><b>Time:\s?<\\/b>([^<]+).*?\"content\"\s?:\s?\"(.*?)\"}').match

            return m
        return inbox
