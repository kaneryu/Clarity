from enum import Enum
import inspect
import typing


class HandlerType(Enum):
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    NEXT = "next"
    PREVIOUS = "previous"
    SEEK = "seek"
    REWIND = "rewind"
    FAST_FORWARD = "fastForward"

    # basically macos specific. doesn't matter if not implemented on other platforms
    LIKE = "like"
    DISLIKE = "dislike"
    BOOKMARK = "bookmark"
    SHUFFLE_MODE = "shuffleMode"
    REPEAT_MODE = "repeatMode"
    TOGGLE_PLAY_PAUSE = "togglePlayPause"


class Handlers:
    def __init__(self):
        self.play: typing.Callable | None = None
        self.pause: typing.Callable | None = None
        self.stop: typing.Callable | None = None
        self.next: typing.Callable | None = None
        self.previous: typing.Callable | None = None
        self.seek: typing.Callable | None = None
        self.rewind: typing.Callable | None = None
        self.fastForward: typing.Callable | None = None
        self.like: typing.Callable | None = None
        self.dislike: typing.Callable | None = None
        self.bookmark: typing.Callable | None = None
        self.shuffleMode: typing.Callable | None = None
        self.repeatMode: typing.Callable | None = None
        self.togglePlayPause: typing.Callable | None = None

    def setHandler(self, type: HandlerType, function: typing.Callable):
        try:
            argcount = len(inspect.signature(function).parameters)
        except (TypeError, ValueError):
            # Bound builtins, partials and C callables aren't introspectable --
            # trust the caller rather than rejecting a valid handler.
            argcount = None
        if argcount is not None and argcount not in (1, 2):
            raise ValueError("Handler function must accept 1 or 2 arguments.")
        if HandlerType._value2member_map_.get(type.value) is None:
            raise ValueError(f"Invalid handler type: {type}")
        setattr(self, type.value, function)
