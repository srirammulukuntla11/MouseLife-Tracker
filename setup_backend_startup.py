"""
MouseLife Tracker — Backend Automatic Startup Setup & Management

Provides idempotent configuration for the Node.js/Express backend auto-start on Windows.
Ensures:
1. Exactly ONE startup registration in HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run.
2. Removes any stray or legacy Startup folder entries.
3. Completely silent execution (no console window).
4. Crash detection and automatic restart via supervisor.
5. Idempotent: running --install multiple times creates NO duplicate entries.
"""

import os
import sys
import winreg
import shutil
import urllib.request
import json
import subprocess
from pathlib import Path

# Configure utf-8 encoding for console output with special characters (e.g. Japanese folder names)
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
SUPERVISOR_PY = BACKEND_DIR / "supervisor.py"
SUPERVISOR_EXE = BACKEND_DIR / "dist" / "MouseLifeBackend.exe"

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_ENTRY_NAME = "MouseLifeBackend"
HEALTH_URL = "http://127.0.0.1:5000/api/health"


def get_pythonw_path() -> str:
    """Finds pythonw.exe (windowless Python interpreter)."""
    # 1. Check directory of current sys.executable
    py_dir = Path(sys.executable).parent
    pythonw_candidate = py_dir / "pythonw.exe"
    if pythonw_candidate.exists():
        return str(pythonw_candidate)

    # 2. Check PATH
    which_pyw = shutil.which("pythonw")
    if which_pyw:
        return which_pyw

    # 3. Standard fallback locations
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    return sys.executable


def get_startup_command() -> str:
    """Returns the command line to register in the Windows Registry Run key."""
    if SUPERVISOR_EXE.exists():
        return f'"{SUPERVISOR_EXE}"'
    pythonw = get_pythonw_path()
    return f'"{pythonw}" "{SUPERVISOR_PY}"'


def clean_legacy_startup_folder():
    """Removes any rogue or duplicate backend files from Windows Startup folder."""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return
    startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    if not startup_dir.exists():
        return

    # Files that shouldn't be in the Startup folder
    legacy_patterns = [
        "MouseLifeBackend.vbs",
        "MouseLifeBackend.bat",
        "MouseLifeBackend.lnk",
        "start_backend.bat",
        "start_backend.vbs",
    ]
    for filename in legacy_patterns:
        target = startup_dir / filename
        if target.exists():
            try:
                target.unlink()
                print(f"[CLEANUP] Removed legacy file from Startup folder: {filename}")
            except Exception as e:
                print(f"[WARNING] Could not remove {filename}: {e}")


def install_backend_startup() -> bool:
    """Idempotently registers the backend supervisor in HKCU Run key."""
    clean_legacy_startup_folder()
    cmd = get_startup_command()

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, STARTUP_ENTRY_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print(f"[SUCCESS] Registered {STARTUP_ENTRY_NAME} in HKCU\\{REG_KEY_PATH}")
        print(f"          Command: {cmd}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to set registry key: {e}")
        return False


def uninstall_backend_startup() -> bool:
    """Removes backend supervisor from HKCU Run key and cleans startup folder."""
    clean_legacy_startup_folder()
    success = True

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, STARTUP_ENTRY_NAME)
        winreg.CloseKey(key)
        print(f"[SUCCESS] Removed {STARTUP_ENTRY_NAME} from HKCU\\{REG_KEY_PATH}")
    except FileNotFoundError:
        print(f"[INFO] {STARTUP_ENTRY_NAME} was not present in registry.")
    except Exception as e:
        print(f"[ERROR] Failed to remove registry key: {e}")
        success = False

    return success


def is_backend_startup_enabled() -> tuple[bool, str]:
    """Checks if the backend startup key is present."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_QUERY_VALUE)
        val, _ = winreg.QueryValueEx(key, STARTUP_ENTRY_NAME)
        winreg.CloseKey(key)
        return True, val
    except FileNotFoundError:
        return False, ""
    except Exception:
        return False, ""


def check_health(timeout=3.0) -> tuple[bool, dict]:
    """Performs HTTP GET against http://127.0.0.1:5000/api/health."""
    try:
        req = urllib.request.Request(HEALTH_URL, headers={"User-Agent": "MouseLifeSetup/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return (resp.status == 200 and data.get("status") == "ok"), data
    except Exception as e:
        return False, {"error": str(e)}


def start_backend():
    """Starts the supervisor process immediately."""
    clean_legacy_startup_folder()
    is_ok, _ = check_health(1.0)
    if is_ok:
        print("[INFO] Backend is already running and healthy.")
        return

    cmd = get_startup_command()
    print(f"Starting backend via supervisor: {cmd}")
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS

    if SUPERVISOR_EXE.exists():
        subprocess.Popen([str(SUPERVISOR_EXE)], cwd=str(BACKEND_DIR), creationflags=creationflags)
    else:
        pythonw = get_pythonw_path()
        subprocess.Popen([pythonw, str(SUPERVISOR_PY)], cwd=str(BACKEND_DIR), creationflags=creationflags)

    print("Supervisor launched. Verifying health endpoint...")
    import time
    for _ in range(15):
        time.sleep(1)
        ok, res = check_health(1.0)
        if ok:
            print("[SUCCESS] Backend is up and healthy on http://127.0.0.1:5000/api/health")
            print(json.dumps(res, indent=2))
            return
    print("[WARNING] Backend did not respond within 15 seconds. Check backend/logs/supervisor.log for details.")


def stop_backend():
    """Stops the backend and supervisor processes."""
    print("Stopping MouseLife backend processes...")
    try:
        # Find node processes running server.js or listening on port 5000
        ps_find = """
        Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | 
        Select-Object -ExpandProperty OwningProcess -Unique | 
        ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_find], capture_output=True)

        # Also find any running python supervisor
        ps_sup = """
        Get-CimInstance Win32_Process | 
        Where-Object { $_.CommandLine -like "*supervisor.py*" -or $_.Name -like "*MouseLifeBackend*" } | 
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
        """
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_sup], capture_output=True)
        print("[SUCCESS] Backend processes stopped.")
    except Exception as e:
        print(f"[ERROR] Failed to stop backend: {e}")


def print_status():
    enabled, val = is_backend_startup_enabled()
    is_ok, data = check_health(2.0)

    print("\n=== MouseLife Tracker — Backend Auto-Start Status ===")
    print(f"Windows Auto-Startup: {'ENABLED' if enabled else 'DISABLED'}")
    if enabled:
        print(f"Startup Command:      {val}")

    print(f"API Health (Port 5000): {'HEALTHY (OK)' if is_ok else 'OFFLINE / UNREACHABLE'}")
    if is_ok:
        print(f"Service:              {data.get('service')}")
        print(f"Server Uptime:        {round(data.get('uptime', 0), 1)}s")
        print(f"Timestamp:            {data.get('timestamp')}")

    # Query Win32_StartupCommand
    try:
        ps_cmd = 'Get-CimInstance Win32_StartupCommand | Where-Object { $_.Name -eq "MouseLifeBackend" } | Format-List Name, Command, Location'
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        print("\n--- Win32_StartupCommand Registration ---")
        out = res.stdout.strip() if res.stdout else "No matching entry in Win32_StartupCommand"
        print(out)
    except Exception as e:
        print(f"Verification query error: {e}")


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--install", "-i", "install"):
            install_backend_startup()
            print_status()
            sys.exit(0)
        elif arg in ("--uninstall", "-u", "uninstall", "remove"):
            uninstall_backend_startup()
            print_status()
            sys.exit(0)
        elif arg in ("--status", "-s", "status"):
            print_status()
            sys.exit(0)
        elif arg in ("--start", "start"):
            start_backend()
            sys.exit(0)
        elif arg in ("--stop", "stop"):
            stop_backend()
            sys.exit(0)
        elif arg in ("--restart", "restart"):
            stop_backend()
            import time
            time.sleep(2)
            start_backend()
            sys.exit(0)
        elif arg in ("--health", "health"):
            ok, data = check_health(3.0)
            print(f"Status OK: {ok}")
            print(json.dumps(data, indent=2))
            sys.exit(0 if ok else 1)

    print("Usage: python setup_backend_startup.py [options]")
    print("Options:")
    print("  --install     Configure backend to start automatically on Windows login")
    print("  --uninstall   Remove backend automatic startup")
    print("  --status      Check current startup registration and backend health")
    print("  --start       Start the backend supervisor right now in the background")
    print("  --stop        Stop the backend and supervisor")
    print("  --restart     Restart the backend")
    print("  --health      Probe http://127.0.0.1:5000/api/health")


if __name__ == "__main__":
    main()
