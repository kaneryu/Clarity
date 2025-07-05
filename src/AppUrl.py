import urllib.parse
import typing

class AppUrl:
    _instance: typing.Union["AppUrl", None] = None 

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppUrl, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.history = ["clarity:///page/home?firstlauch=true"]
            
            self.pointer = 0
            self.initialized = True
    
    def getParsedUrl(self):
        return urllib.parse.urlparse(self.history[self.pointer])

    def getUrl(self):
        return self.history[self.pointer]
    
    def getPath(self) -> list:
        p = self.getParsedUrl().path
        if p == "":
            return []
        return p.lstrip("/").split("/")
    
    def goToHistory(self, index: int):
        self.pointer = index if not index == -1 else len(self.history) - 1 # -1 is a special case for going to the end of the history
        if self.pointer < 0:
            self.pointer = 0
    
    def getQuery(self) -> dict:
        return urllib.parse.parse_qs(self.getParsedUrl().query)
    
    def goBack(self):
        self.pointer -= 1
    
    def goForward(self):
        self.pointer += 1
    
    def setUrl(self, url: str):
        if self.pointer < len(self.history) - 1:
            self.history = self.history[:self.pointer + 1] # remove all history after the current pointer
        self.history.append(url)
        self.pointer += 1

appUrl = AppUrl()