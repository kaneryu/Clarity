# Song Queue
import baseModels as baseModels
from innertube import song
import dataclasses


class SongQueue(baseModels.BaseModel):
    def __init__(self):
        super().__init__(song.Song)


queue = None
def getQueue() -> SongQueue:
    if queue is None:
        queue = SongQueue()
    return queue
    
    
    