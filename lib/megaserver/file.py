from lib.megaserver.cursor import Cursor


class File(object):
    def __init__(self, info, file_id, key, file ,client, folder_id=None):
        self._client = client
        self.folder_id = folder_id
        self.file_id = file_id
        self.cursor = False
        self.cursors = []
        self.key = key
        self.file = file
        self.info= info
        self.name =  info["n"]
        self.size = file["s"]
        self.request=None
        self.k = self.key[0] ^ self.key[4] , self.key[1] ^ self.key[5] , self.key[2] ^ self.key[6], self.key[3] ^ self.key[7]
        self.iv = self.key[4:6] + (0, 0)
        self.initial_value = (((self.iv[0] << 32) + self.iv[1]) << 64)
        if not self.folder_id:
            self.url= self.file["g"]
        else:
            self.url = None

    def create_cursor(self,offset):
        c =  Cursor(self)
        c.seek(offset)
        self.cursor = True
        self.cursors.append(c)
        return c
