import sys, traceback
from platformcode import logger
if sys.version_info[0] >= 3:
    from urllib.request import Request, urlopen
else:
    from urllib2 import Request, urlopen
    str = unicode


class Cursor(object):
    def __init__(self, file):
        self._file=file
        self.pos=0
        self.conn =None
        self.initial_value = file.initial_value
        self.k = file.k

    def mega_request(self,offset, retry=False):
        if not self._file.url or retry:
            if self._file.folder_id :
                file = self._file._client.api_req({"a":"g","g":1,"n":self._file.file_id},"&n="+self._file.folder_id)
                self._file.url= file["g"]
            else:
                file = self._file._client.api_req({'a': 'g', 'g': 1, 'p': self._file.file_id})
                self._file.url= file["g"]

        req = Request(self._file.url)
        req.headers['Range'] = 'bytes=%s-' % (offset)
        try:
            self.conn = urlopen(req)
            try:
                self.prepare_decoder(offset)
            except:
                logger.error(traceback.format_exc())
        except:
            self.mega_request(offset, True)

    def read(self,n=None):
        if not self.conn:
            return
        res=self.conn.read(n)
        if res:
            res = self.decode(res)
            self.pos+=len(res)
        return res

    def seek(self,n):
        if n>self._file.size:
            n=self._file.size
        elif n<0:
            raise ValueError('Seeking negative')
        self.mega_request(n)
        self.pos=n

    def tell(self):
        return self.pos

    def __enter__(self):
        return self

    def __exit__(self,exc_type, exc_val, exc_tb):
        self._file.cursors.remove(self)
        if len(self._file.cursors) == 0: self._file.cursor = False

    def decode(self, data):
        if type(data) == str: data = data.encode()
        return self.decryptor.decrypt(data)

    def prepare_decoder(self,offset):
        initial_value = self.initial_value + int(offset/16)
        try:
            from Cryptodome.Cipher import AES
            from Cryptodome.Util import Counter
        except:
            from Crypto.Cipher import AES
            from Crypto.Util import Counter
        self.decryptor = AES.new(self._file._client.a32_to_str(self.k), AES.MODE_CTR, counter = Counter.new(128, initial_value = initial_value))
        rest = offset - int(offset/16)*16
        if rest:
            self.decode(str(0)*rest)
