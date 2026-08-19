from enum import Enum
import typing


class HandlerType(Enum):
    PLAY = "play"
    PAUSE = "pause"
    STOP = "stop"
    NEXT = "next"
    PREVIOUS = "previous"
    SEEK = "seek"
    REWIND = "rewind"
    FAST_FORWARD = "fast_forward"


class Handlers:
    def __init__(self):
        self.play: typing.Callable | None = None
        self.pause: typing.Callable | None = None
        self.stop: typing.Callable | None = None
        self.next: typing.Callable | None = None
        self.previous: typing.Callable | None = None
        self.seek: typing.Callable | None = None
        self.rewind: typing.Callable | None = None
        self.fast_forward: typing.Callable | None = None

    def setHandler(self, type: HandlerType, function: typing.Callable):
        if not function.__code__.co_argcount in (1, 2):
            raise ValueError("Handler function must accept 1 or 2 arguments.")
        if type == HandlerType.PLAY:
            self.play = function
        elif type == HandlerType.PAUSE:
            self.pause = function
        elif type == HandlerType.STOP:
            self.stop = function
        elif type == HandlerType.NEXT:
            self.next = function
        elif type == HandlerType.PREVIOUS:
            self.previous = function
        elif type == HandlerType.SEEK:
            self.seek = function
        elif type == HandlerType.FAST_FORWARD:
            self.fast_forward = function
        elif type == HandlerType.REWIND:
            self.rewind = function
