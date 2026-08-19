from typing import runtime_checkable, Protocol, Any, Optional, Callable

from src.nowPlaying.HandlerEnum import HandlerType
from src.nowPlaying.NowPlayingProtocol import NowPlaying


class noOpHandler(NowPlaying):
    def set_now_playing(
        self, title: str, artist: str, album: str, artwork: Optional[Any] = None
    ) -> None:
        pass

    def update_timeline(
        self,
        duration: float,
        position: float,
        *,
        min_seek=0.0,
        max_seek: Optional[float] = None,
    ) -> None:
        pass

    def playback_play(self) -> None:
        pass

    def playback_pause(self) -> None:
        pass

    def playback_stop(self) -> None:
        pass

    def set_next_enabled(self, enabled: bool) -> None:
        pass

    def set_previous_enabled(self, enabled: bool) -> None:
        pass

    def set_handler(self, handler_type: HandlerType, handler: Callable) -> None:
        pass
