from ui.desktop_app import DesktopAppUi

from custom_types.events import Event
from services.event_emitter import register_callback

desktop_app = DesktopAppUi()

def print_event(event :Event) -> None:
    print(event)

def route_navigation_event(event :Event) -> None:
    if event.type != Event.EventType.NAVIGATE:
        return
    
    if not event.properties:
        raise Exception("Navigation error: missing target screen name on event properties")
    
    target = event.properties.get("target", "")

    try:
        desktop_app.navigate_to(target)
    except Exception as e:
        raise Exception("Navigation error") from e

register_callback(print_event)
register_callback(route_navigation_event)

if __name__ == '__main__':
    desktop_app.run()