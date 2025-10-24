from data.events import Event
from typing import Callable


class EventRouter:
    __callbacks: list[Callable[[Event], None]] = []

    def emit_event(self, event: Event) -> None:
        for callback in self.__callbacks:
            assert callback is not None
            
            callback(event)

    def register_callback(self, callback: Callable[[Event], None]):
        self.__callbacks.append(callback)

event_router = EventRouter()

def emit_event(event: Event)->None:
    event_router.emit_event(event)