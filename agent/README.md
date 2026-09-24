# MouseLife Tracker — Windows Agent

The background agent responsible for:
- Detecting global mouse click events across all Windows applications (`pynput` with `WH_MOUSE_LL`).
- Counting Left, Right, and Middle clicks.
- Maintaining local ACID persistence in SQLite (`agent/data/mouselife_local.db`).
- Synchronizing in batches to the Express backend with duplicate detection.
- Windows Startup integration (`--install-startup`).
- System tray management (`pystray`).

## Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`

## Running
```powershell
# Interactive with System Tray:
python src\main.py

# Headless background daemon:
python src\main.py --headless

# Status check:
python src\main.py --status

# Install automatic Windows startup:
python src\main.py --install-startup
```

## Testing
```powershell
python -m unittest discover tests/
```
