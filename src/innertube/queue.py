import yt_dlp.YoutubeDL as yt_dlp
import yt_dlp as yt_dlp_module
import vlc

from PySide6.QtCore import QObject, Slot, Signal, Property as QProperty

import io
import enum
import requests

from src import universal as g
from src import cacheManager
from src.app import baseModels
import time
import asyncio

ytdl: yt_dlp_module.YoutubeDL
ytdl = yt_dlp()

class LoopType(enum.Enum):
    """Loop Types"""
    NONE = 0 # Halt after playing all songs
    SINGLE = 1 # Repeat the current song
    ALL = 2 # Repeat all songs in the queue
    

class QueueModel():
    pass

queue = None
    
class Queue(QObject):
    """Combined Queue and Player"""

    queueChanged = Signal()
    songChanged = Signal()
    
    @staticmethod
    def getInstance():
        global queue
        if queue:
            return queue
        else:
            queue = Queue()
            return queue
        
    def __init__(self):
        super().__init__()
        self._queue = []
        self.queueData = {}
        self.pointer = 0
        self.player: vlc.MediaPlayer = vlc.MediaPlayer()
        self.eventMgr = self.player.event_manager()
        self.eventMgr.event_attach(vlc.EventType.MediaPlayerEndReached, self.songFinished)
        self.player.set_hwnd(0)
        self.loop: LoopType = LoopType.NONE
        
        
        if not cacheManager.cacheExists("queueCache"):
            cache = cacheManager.CacheManager(name="queueCache")
        else:
            cache = cacheManager.getCache("queueCache")
        
        self.cache = cache
    
    
    @QProperty(list, notify=queueChanged)
    def queue(self):
        return self._queue
    
    @queue.setter
    def queue(self, value):
        self.queueChanged.emit()
        self.setQueue(value, skipSetData = True)
        
    @QProperty(str, notify=songChanged)
    def currentSongTitle(self):
        return self.info(self.pointer)["title"]

    @QProperty(str, notify=songChanged)
    def currentSongUploader(self):
        return self.info(self.pointer)["uploader"]
    
    @QProperty(str, notify=songChanged)
    def currentSongDescription(self):
        return self.info(self.pointer)["description"]
    
    def checkError(self, url: str):
        # we will check if accessing the url will result in an error
        
        r = requests.get(url)
        if r.status_code == 200:
            return False
        else:
            return True
    
    
    def getPlaybackUrl(self, data: dict):
        for i in data:
            if i["resolution"] == "audio only" or i["format_id"] == "233":
                return i["url"]
    
    
    def getSongData(self, id: str):
        def getNewDataAndCache(id: str):
            data = ytdl.extract_info(id, download=False)
            self.cache.sput(id + "_playbackData", data, byte = False, expiration = int(time.time()) + 18000) # Expires in 5 hours
            return data
        
        print("Getting Song Data")
        print("ID: " + id)
        
        data = self.cache.sget(id + "_playbackData")
        if data == False:
            print("No Cached Data")
            data = getNewDataAndCache(id)
        else:
            print("Using Cached Data")
        
        url = self.getPlaybackUrl(data["formats"])
        if self.checkError(url):
            print("Error in URL")
            data = getNewDataAndCache(id)
            
        return {
            "title": data["title"],
            "uploader": data["uploader"],
            "description": data["description"],
            "playbackUrl": url
        }
    
    def setSongData(self, id: str, data: dict):
        self.queueData[id] = data
        self.cache.sput(id + "_playbackData", data, byte = False, expiration = int(time.time()) + 18000) # Expires in 5 hours
    
    async def test(self):
        await asyncio.sleep(2)
        print("wow")
        
    def getCurrentSongData(self):
        return self.queueData[self.queue[self.pointer]]
    
    @Slot(result=dict)
    def getCurrentInfo(self) -> dict:
        return self.info(self.pointer)
    
    @Slot(str, bool)
    def setQueue(self, queue: list, skipSetData: bool = False):
        self._queue = queue
        if not skipSetData:
            for i in self._queue:
                self.queueData[i] = self.getSongData(i) 
    
    def songFinished(self, event):
        print("Song Finished")
        if self.loop == LoopType.SINGLE:
            self.playSong(self.queue[self.pointer])
        elif self.loop == LoopType.ALL or self.loop == LoopType.NONE:
            self.next()
        else:
            print("LoopType Invalid")
            print("Treating as LoopType.NONE")
            self.next()
        self.songChanged.emit()
            
    @Slot(str)
    def playSong(self, id: str):
        self.player.set_mrl(self.getSongData(id)["playbackUrl"])
        print("Playing: " + id)
        self.player.play()
        
    @Slot()
    def pause(self):
        self.player.pause()
        
    @Slot()
    def play(self):
        self.player.play()
    
    @Slot()
    def stop(self):
        self.player.stop()
    
    @Slot()
    def reload(self):
        self.playSong(self.queue[self.pointer])
    
    @Slot(int)
    def setPointer(self, index: int):
        self.pointer = index
        self.reload()
    
    @Slot()
    def next(self):
        print("Next")
        print("Pointer: " + str(self.pointer), "Length: " + str(len(self.queue)))
        if self.pointer == len(self.queue) - 1:
            print("Queue Finished")
            if self.loop == LoopType.SINGLE:
                self.playSong(self.queue[self.pointer])
                return
            elif self.loop == LoopType.ALL:
                self.pointer = 0
                self.playSong(self.queue[self.pointer])
                return
            else:
                print("Queue Exhaused")
                self.stop()
                return
        
        self.pointer += 1
        self.playSong(self.queue[self.pointer])
    
    @Slot()
    def prev(self):
        self.pointer = self.pointer - 1 if self.pointer > 0 else 0
        self.playSong(self.queue[self.pointer])
    
    def info(self, pointer: int):
        if not self.queue[pointer] in self.queueData:
            self.queueData[self.queue[pointer]] = self.getSongData(self.queue[pointer])
            
        data = self.queueData[self.queue[pointer]]
        return {
            "title": data["title"],
            "uploader": data["uploader"],
            "description": data["description"]
        }
    
    def add(self, link: str, index: int):
        self.queueData[link] = self.getSongData(link)
        self.queue.insert(index, link)
    
    def _seek(self, time: int):
        if time < 0 or time > self.player.get_length() / 1000:
            raise ValueError("Time must be between 0 and video length")
        
        if not self.player.get_media() == None:
            self.player.set_time(time * 1000)
        else:
            raise ValueError("No Media Loaded")
    
    @Slot(int)
    def seek(self, time: int):
        self.player.set_time(time * 1000)
    
    @Slot(int)
    def aseek(self, time: int):
        self.player.set_time(self.player.get_time() + time * 1000)
    
    @Slot(int)
    def pseek(self, percentage: int):
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        len = self.player.get_length()
        self.player.set_time(len * percentage // 100)
    


        
        
def main():
    print("Queue Player")
    player = Queue()
    player.setQueue(["F_mq88Lw2Lo", "DyTBxPyEG_M", "I8O-BFLzRF0", "UNQTvQGVjao", "IAW0oehOi24"])
    
    print("Commands: pause play stop reload next prev info add seek aseek pseek exit")

    while True:
        cmd = input("Enter Command: ")
        if cmd == "pause":
            player.pause()
        elif cmd == "play":
            player.play()
        elif cmd == "stop":
            player.stop()
        elif cmd == "exit":
            player.stop()
            break
        elif cmd == "reload":
            player.reload()
        elif cmd == "next":
            player.next()
        elif cmd == "prev":
            player.prev()
        elif cmd == "info":
            info = player.info(player.pointer)
            print(f"Title: {info['title']}")
            print(f"Uploader: {info['uploader']}")
            print(f"Description: {info['description']}")
        elif cmd == "add":
            link = input("Enter watchID: ")
            index = int(input("Enter index: "))
            player.add(link, index)
        elif cmd == "volume":
            volume = int(input("Enter volume (0 - 100): "))
            player.player.audio_set_volume(volume)
        elif cmd == "loop":
            loop = input("Enter loop type (none, single, all): ")
            if loop == "none":
                player.loop = LoopType.NONE
            elif loop == "single":
                player.loop = LoopType.SINGLE
            elif loop == "all":
                player.loop = LoopType.ALL
            else:
                print("Invalid Loop Type")

        elif cmd == "seek":
            time = int(input(f"Enter time (0 - {player.player.get_length() / 1000}): "))
            player.seek(time)
        elif cmd == "aseek":
            time = int(input("Enter change in time: "))
            player.aseek(time)
        elif cmd == "pseek":
            percentage = int(input("Enter percentage (0 - 100): "))
            player.pseek(percentage)
        else:
            print("Invalid Command")

if __name__ == "__main__":
    main()