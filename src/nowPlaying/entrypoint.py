import src.misc.platform

if src.misc.platform.isMac:
    from src.nowPlaying.darwinHandler import darwinHandler as NowPlayingHandler
elif src.misc.platform.isWindows:
    from src.nowPlaying.windowsHandler import windowsHandler as NowPlayingHandler
elif src.misc.platform.isLinux:
    from src.nowPlaying.noOpHandler import noOpHandler as NowPlayingHandler
else:
    from src.nowPlaying.noOpHandler import noOpHandler as NowPlayingHandler
