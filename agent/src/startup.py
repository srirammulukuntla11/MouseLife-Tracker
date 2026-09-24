import os
import sys
from pathlib import Path
import winreg
from .logger import agent_logger

STARTUP_NAME = "MouseLifeTracker"
STARTUP_DIR = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_launcher_paths():
    """Returns absolute paths for the executable, python interpreter, and startup locations."""
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        exe_path = Path(sys.executable).resolve()
        agent_dir = exe_path.parent
    else:
        # Development mode
        agent_dir = Path(__file__).resolve().parent.parent
        dist_exe = agent_dir / "dist" / "MouseLifeTracker.exe"
        if dist_exe.exists():
            exe_path = dist_exe.resolve()
            is_frozen = True
        else:
            exe_path = None

    main_script = agent_dir / "src" / "main.py"
    venv_python = agent_dir / "venv" / "Scripts" / "pythonw.exe"
    if not venv_python.exists():
        venv_python = Path(sys.executable)

    return {
        "agent_dir": agent_dir,
        "main_script": main_script,
        "pythonw": venv_python,
        "is_frozen": is_frozen,
        "exe_path": exe_path
    }

def clean_legacy_startup_folder() -> int:
    """
    Scans the Windows Startup folder and removes any legacy or duplicate
    MouseLifeTracker files (.vbs, .bat, .lnk, .exe).
    Returns the number of files cleaned up.
    """
    cleaned = 0
    if not STARTUP_DIR.exists():
        return 0

    patterns = ["*MouseLifeTracker*.vbs", "*MouseLifeTracker*.bat", "*MouseLifeTracker*.lnk"]
    for pattern in patterns:
        for file_path in STARTUP_DIR.glob(pattern):
            try:
                file_path.unlink()
                agent_logger.info(f"Cleaned legacy file from Startup folder: {file_path.name}")
                cleaned += 1
            except Exception as e:
                agent_logger.warning(f"Could not remove legacy startup file {file_path}: {e}")

    return cleaned

def install_startup(use_registry: bool = True) -> bool:
    """
    Configures MouseLife Tracker to start automatically with Windows.
    Enforces strictly ONE startup registration using the Windows Registry Run key
    (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run).

    Guarantees:
    - Exactly ONE entry in Win32_StartupCommand.
    - Cleans up and deletes any duplicate VBS/BAT/LNK files in the Startup folder.
    - Idempotent: Can be run repeatedly without creating duplicates.
    - Launches MouseLifeTracker.exe directly without terminal window.
    """
    paths = get_launcher_paths()

    try:
        # 1. First, purge any duplicate files from the Windows Startup folder
        clean_legacy_startup_folder()

        # 2. Determine command to register
        if paths.get("is_frozen") and paths.get("exe_path"):
            # Standalone executable: launch directly with quotes
            command = f'"{paths["exe_path"]}"'
        else:
            # Script mode: launch via pythonw (windowless)
            command = f'"{paths["pythonw"]}" "{paths["main_script"]}"'

        # 3. Register strictly in HKCU Registry Run key (idempotent replacement)
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, STARTUP_NAME, 0, winreg.REG_SZ, command)

        agent_logger.info(f"Windows startup configured in HKCU\\{REG_KEY_PATH} -> {command}")
        return True

    except Exception as e:
        agent_logger.error(f"Failed to configure Windows startup: {e}")
        return False

def uninstall_startup() -> bool:
    """
    Removes MouseLife Tracker completely from Windows startup.
    Cleans up both the Registry Run key and any legacy files in the Startup folder.
    """
    success = True

    # 1. Clean up any files in Startup folder
    clean_legacy_startup_folder()

    # 2. Remove Registry Run key
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, STARTUP_NAME)
            agent_logger.info(f"Removed Registry Run entry '{STARTUP_NAME}'")
    except FileNotFoundError:
        pass
    except Exception as e:
        agent_logger.warning(f"Failed to remove Registry Run value: {e}")
        success = False

    return success

def is_startup_enabled() -> bool:
    """
    Checks whether MouseLife Tracker is configured in Windows startup.
    Cleans up any legacy rogue files in the Startup folder during check.
    """
    # Clean up rogue startup files if found
    clean_legacy_startup_folder()

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
            value, reg_type = winreg.QueryValueEx(key, STARTUP_NAME)
            return bool(value and str(value).strip())
    except FileNotFoundError:
        return False
    except Exception:
        return False
