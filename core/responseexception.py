

class ResponseException(Exception):

    def __init__(self, response):
        self.code = response.status_code
        self.content = response.content
        self._response = response
        super().__init__(self.content)
    
    def __str__(self):
        return str(self.code)