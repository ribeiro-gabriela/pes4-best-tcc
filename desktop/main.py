from pathlib import Path
import sys
from kivy.resources import resource_add_path, resource_find

# Aponta para .../desktop/ui (independente do CWD)
BASE = Path(__file__).resolve().parent
resource_add_path(str(BASE / "ui"))

# (opcional) checagem de sanidade para depuração
print("KV encontrado?", resource_find("styling.kv"))

from ui.ui_manager import UiManager

desktop_app = UiManager()

if __name__ == '__main__':
    desktop_app.run()