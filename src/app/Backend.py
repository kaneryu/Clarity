# stdlib imports
import json
import os
import pathlib
import random
import sys
import asyncio
import time
import typing
import urllib.parse

# library imports
from PySide6.QtCore import (
    QObject,
    Qt,
    QTimer,
    QThread,
)

from PySide6.QtCore import Signal as QSignal
from PySide6.QtCore import Slot as Slot
from PySide6.QtQml import (
    QmlElement,
    QmlSingleton,
    QQmlApplicationEngine,
    qmlRegisterSingletonInstance,
    qmlRegisterSingletonType,
)
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
from PySide6.QtNetwork import QNetworkCookie

from PySide6.QtCore import Property


import src.universal as universal
import src.paths as paths

import ytmusicapi

QML_IMPORT_NAME = "CreateTheSun"
QML_IMPORT_MAJOR_VERSION = 1
QML_IMPORT_MINOR_VERSION = 0

@QmlElement
class Backend(QObject):
    loadComplete = QSignal(name="loadComplete")
    activeTabChanged = QSignal(name="activeTabChanged")
    # tabModelChanged = QSignal(name="tabModelChanged")
    queueVisibleChanged = QSignal(name="queueVisibleChanged")
    urlChanged = QSignal(name="urlChanged")
    loginRedirect = QSignal(name="loginRedirect")
    loginComplete = QSignal(name="loginComplete")
    _instance: "Backend"
    
    def __new__(cls) -> "Backend":
        if (hasattr(cls, "_instance") and cls._instance is not None) or not hasattr(cls, "_instance"): # if instance var exists and is not None, or if it does not exist
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            super().__init__()
            self.initialized = True
            self._value = 0                
            self._queueModel = universal.queueInstance.queueModel
            self._queueVisible = False
        
    @Property(str, notify=urlChanged)
    def url(self):
        return universal.appUrl.getUrl()
    
    @url.setter
    def url(self, value: str):
        try:
            urllib.parse.urlparse(value)
        except:
            print("Set URL failed, invalid URL", value)
            return
        universal.appUrl.setUrl(value)
        self.urlChanged.emit()
    
    @Slot(str)
    def setUrl(self, value):
        self.url = "clarity:///" + value
    
    @Property(dict, notify=urlChanged)
    def currentQuery(self):
        return universal.appUrl.getQuery()
    
    @Property(str, notify=urlChanged)
    def getCurrentPageFilePath(self):
        path = universal.appUrl.getPath()
        if path[0] == "page":
            if path == "/":
                ret = os.path.join(universal.Paths.qmlPath, "pages", "home.qml")
            else:
                first = path[1]
                first.replace("/", "")
                ret = os.path.join(universal.Paths.qmlPath, "pages", first + ".qml")
                
            if not os.path.exists(ret):
                print("Path does not exist", ret)
                return ""
            return "file:///" + ret
    
    @Slot(str)
    def setSearchURL(self, query):
        self.url = "clarity:///page/search?query=" + query
        
    @Slot(result=QObject)
    def getqueueModel(self):
        return universal.queueInstance.queueModel
    
    @Property(QObject, constant=True)
    def queueModel(self):
        return self._queueModel
    
    @Property(QObject, constant=True)
    def searchModel(self):
        return universal.searchModel
    
    @Slot(str, result=bool)
    def search(self, query: str) -> bool:
        universal.asyncBgworker.add_job_sync(func = universal.search_shorthand, usestar = False, a = [], kw = {"query": query})
        return True
    
    @Property(QObject, constant=True)
    def queue(self):
        return universal.queueInstance
    
    @Property(bool, notify=queueVisibleChanged)
    def queueVisible(self):
        return self._queueVisible
    
    @queueVisible.setter
    def queueVisible(self, value):
        self._queueVisible = value
        self.queueVisibleChanged.emit()
    
    @Slot(str, result=str)
    def getPage(self, url: str) -> str:
        
        # parse the url
        # possible roots as of now:
        # page
        # then we have the page name after, so like page/home
        
        # pages are stored locally in the html folder (src/app/html)
        
        url: list[str] = url.split("/")
        print(url)
        print("file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/"))
        return "file:///" + os.path.join(os.path.dirname(__file__), "html", url[0], url[1], "index.html").replace("\\","/")
        
    @Slot(result=str)
    def ping(self) -> str:
        return "pong"

    # @Slot()
    # def oauth(self) -> None:
    #     ytmusicapi.setup_oauth()

def castUb(input: typing.Any) -> typing.Union[bytes, bytearray]:
    return typing.cast(typing.Union[bytes, bytearray], input)
    

class ProfileInterfaceManager:
    def __init__(self, profile: QWebEngineProfile | QQuickWebEngineProfile):
        self.profile = profile
        urlInterceptor = UrlInterceptor()
        self.profile.setUrlRequestInterceptor(urlInterceptor)
    
        cookiestore = self.profile.cookieStore()
        cookiestore.cookieAdded.connect(self.newCookie)
        cookiestore.cookieRemoved.connect(self.remCookie)
    
    def newCookie(self, cookie: QNetworkCookie):
        
        prep = f"""
        New cookie:
        Name: {castUb(cookie.name().data()).decode("utf-8")}
        Value: {castUb(cookie.value().data()).decode("utf-8")}
        Domain: {cookie.domain()}
        Path: {cookie.path()}
        """
        print(prep)
    
    def remCookie(self, cookie: QNetworkCookie):
        prep = f"""
        Removed cookie:
        Name: {castUb(cookie.name().data()).decode("utf-8")}
        Value: {castUb(cookie.value().data()).decode("utf-8")}
        Domain: {cookie.domain()}
        Path: {cookie.path()}
        """
        print(prep)

class UrlInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        url = info.requestUrl().toString()
        headers = info.httpHeaders()
        
        if "Cookie" in headers.keys():
            print("url", url)
            print("headers", headers)
        
        if url == "https://music.youtube.com":
            bend = Backend()
            bend.loginRedirect.emit()

        
        if url.startswith("https://music.youtube.com/youtubei/v1/browse"):
            bend = Backend()
            print("url", url)
            # Iterate through headers and convert QByteArray to strings
            headers_dict = {}
            for key, value in headers.items():
                headers_dict[castUb(key.data()).decode("utf-8")] = castUb(value.data()).decode("utf-8")
            print(headers_dict)
            
            if not "Cookie" in headers_dict.keys() or not "X-Goog-Authuser" in headers_dict.keys():
                print("bad request")
                return
            
            with open("ytheaders.json", "w") as f:
                json.dump(headers_dict, f)
                
            bend.loginComplete.emit()
            
        