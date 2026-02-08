from typing import Union

ydlOpts: dict[str, Union[list, bool]] = {
    "external_downloader_args": ["-loglevel", "panic"],
    "quiet": False,
    "concurrent-fragments": True,
}
FMT_DATA_HUMAN = {
    "sb0": "Storyboard (low quality)",
    "sb1": "Storyboard (low quality)",
    "sb2": "Storyboard (low quality)",
    "160": "144p (low quality)",
    "133": "240p (low quality)",
    "134": "360p (medium quality)",
    "135": "480p (medium quality)",
    "136": "720p (high quality)",
    "137": "1080p (high quality)",
    "242": "240p (low quality, WebM)",
    "243": "360p (medium quality, WebM)",
    "244": "480p (medium quality, WebM)",
    "247": "720p (high quality, WebM)",
    "248": "1080p (high quality, WebM)",
    "139": "Low quality audio (48.851 kbps)",
    "140": "Medium quality audio (129.562 kbps)",
    "251": "Medium quality audio (135.49 kbps, WebM)",
    "250": "Low quality audio (68.591 kbps, WebM)",
    "249": "Low quality audio (51.975 kbps, WebM)",
    "18": "360p video with audio (medium quality)",
}
FMT_DATA = {
    "sb0": -1,  # Storyboard (low quality)
    "sb1": -1,  # Storyboard (low quality)
    "sb2": -1,  # Storyboard (low quality)
    "160": 1,  # 144p (low quality)
    "133": 2,  # 240p (low quality)
    "134": 4,  # 360p (medium quality)
    "135": 5,  # 480p (medium quality)
    "136": 7,  # 720p (high quality)
    "137": 9,  # 1080p (high quality)
    "242": 2,  # 240p (low quality, WebM)
    "243": 4,  # 360p (medium quality, WebM)
    "244": 5,  # 480p (medium quality, WebM)
    "247": 7,  # 720p (high quality, WebM)
    "248": 9,  # 1080p (high quality, WebM)
    "139": 1,  # Low quality audio (48.851 kbps)
    "140": 4,  # Medium quality audio (129.562 kbps)
    "251": 5,  # Medium quality audio (135.49 kbps, WebM)
    "250": 3,  # Low quality audio (68.591 kbps, WebM)
    "249": 2,  # Low quality audio (51.975 kbps, WebM)
    "18": 4,  # 360p video with audio (medium quality)
}
