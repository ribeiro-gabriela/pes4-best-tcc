from custom_types.events import Event
from typing import Callable

__callbacks: list[Callable[[Event], None]] = []

def emit_event(event: Event) -> None:
    for callback in __callbacks:
        assert callback is not None
        
        callback(event)

def register_callback(callback: Callable[[Event], None]):
    __callbacks.append(callback)