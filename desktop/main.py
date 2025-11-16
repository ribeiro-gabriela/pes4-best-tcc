from pathlib import Path
import sys
from kivy.resources import resource_add_path, resource_find

BASE = Path(__file__).resolve().parent
resource_add_path(str(BASE / "ui"))

print("KV encontrado?", resource_find("styling.kv"))

from ui.ui_manager import UiManager

desktop_app = UiManager()

if __name__ == '__main__':
    desktop_app.run()