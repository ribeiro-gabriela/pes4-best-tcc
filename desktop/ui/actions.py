from custom_types.screens import ScreenName
from services.event_emitter import emit_event
from utils.events import build_navigate_to_screen_event
from typing import Callable

def action_go_to_screen(screen: ScreenName) -> Callable[[], None]:
    assert screen is not None

    event = build_navigate_to_screen_event(screen)

    return lambda: emit_event(event)

def action_show_help() -> Callable[[], None]:
    return _show_help_callable

def _show_help_callable() -> None:
    print("Help button pressed")