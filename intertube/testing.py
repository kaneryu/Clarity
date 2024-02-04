"""
Internal file for testing future libary features.
"""

import ytmusicapi as ytm
import json

api = ytm.YTMusic()


file = open("song_info_example.json", "w")
file.write(json.dumps(api.get_song("nQaXsgmnQUE")))
file.close()
