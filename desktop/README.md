# GSE Desktop App

## Dependencies

Listed on `requirements.txt`. Main dependencies are kivy and pywifi

## Getting Started

### Prerequisites

* Python 3.11+
* `pip` and `venv`

### Installation

1.  **Create and activate a virtual environment:**

* On Windows:

```
python -m venv .venv
.\.venv\Scripts\activate
```

* On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2.  **Install the required packages:**

```bash
pip install -r requirements.txt
```

3. **Exit venv after use**
```bash
deactivate
```

---

## Usage

To run the application, execute the main Python script:

```bash
python main.py
```

Important: On many operating systems, scanning and connecting to Wi-Fi networks requires administrative or root privileges. You may need to run the script accordingly:

* Windows

Open Command Prompt or PowerShell as an Administrator.

* Linux

: Use sudo:

```bash
sudo python main.py
```

---

## Building an Executable

Build scripts are provided for convenience. These scripts use PyInstaller to package the application.

IMPORTANT: scripts must be run from the same directory as `main.py`

* Build on Windows:

```
.\build.bat
```

* Build on Linux:

```
chmod +x build.sh
./build.sh
```