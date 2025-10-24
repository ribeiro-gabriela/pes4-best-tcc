from data.events import Event
from data.enums import ScreenName


def build_navigate_to_screen_event(target_screen: ScreenName) -> Event:
    assert target_screen is not None

    return Event(Event.EventType.NAVIGATE, None, {"target": target_screen})
