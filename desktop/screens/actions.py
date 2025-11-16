from data.enums import ScreenName
from ui.event_router import emit_event
from utils.events import build_navigate_to_screen_event
from typing import Callable

def action_go_to_screen(screen: ScreenName) -> Callable[[], None]:
    assert screen is not None

    event = build_navigate_to_screen_event(screen)

    return lambda: emit_event(event)

# [BST-329]
def action_show_help() -> Callable[[], None]:
    return _show_help_callable

def _show_help_callable() -> None:
    print("Help button pressed")