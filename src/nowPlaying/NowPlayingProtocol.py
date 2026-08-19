from typing import runtime_checkable, Protocol, Any, Optional, Callable

from src.nowPlaying.HandlerEnum import HandlerType


@runtime_checkable
class NowPlaying(Protocol):
    def set_now_playing(
        self, title: str, artist: str, album: str, artwork: Optional[Any] = None
    ) -> None:
        """This function should set the currently playing song.

        Args:
            title (str): Title
            artist (str): Artist
            album (str): Album
            artwork (Optional[Any], optional): _description_. Defaults to None.
        """
        ...

    def update_timeline(
        self,
        duration: float,
        position: float,
        *,
        min_seek=0.0,
        max_seek: Optional[float] = None,
    ) -> None:
        """Update the song's position on the timeline. Call every second.

        Args:
            duration (float): Of the song, seconds
            position (float): Where you are, seconds
            min_seek (float, optional): _description_. Defaults to 0.0.
            max_seek (Optional[float], optional): _description_. Defaults to None.
        """
        ...

    def playback_play(self) -> None:
        """This will be called whenever the song's state changes to playing. Update the OS accordingly."""
        ...

    def playback_pause(self) -> None:
        """This will be called whenever the song's state changes to paused. Update the OS accordingly."""
        ...

    def playback_stop(self) -> None:
        """This will be called whenever the song's state changed to stopped. Update the OS accordingly."""
        ...

    def set_next_enabled(self, enabled: bool) -> None: ...

    def set_previous_enabled(self, enabled: bool) -> None: ...

    def set_handler(self, handler_type: HandlerType, handler: Callable) -> None: ...
