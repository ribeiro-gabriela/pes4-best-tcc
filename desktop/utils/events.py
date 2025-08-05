from custom_types.events import Event
from custom_types.screens import ScreenName


def build_navigate_to_screen_event(target_screen: ScreenName) -> Event:
    assert target_screen is not None

    return Event(Event.EventType.NAVIGATE, {"target": target_screen.value})
