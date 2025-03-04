from src.innertube.song import Queue, Song

'''
This is a wrapper around ytmusicapi and youtube-dl.

Current submodules:
search.py - search for a song
song.py - stores the class for a song
testing.py - internal file for testing future features (not unit tests)
'''
__all__ = ["queue", "Queue", "Song"]