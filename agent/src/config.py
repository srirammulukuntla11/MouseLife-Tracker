import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the agent (detects if running as compiled PyInstaller .exe or script)
if getattr(sys, 'frozen', False):
    AGENT_DIR = Path(sys.executable).resolve().parent
else:
    AGENT_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = AGENT_DIR / "data"
ASSETS_DIR = AGENT_DIR / "assets"
ENV_FILE = AGENT_DIR / ".env"

DATA_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv()

class Config:
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000").rstrip("/")
    MOUSE_ID = os.getenv("MOUSE_ID", "portronics-default-01")
    MOUSE_NAME = os.getenv("MOUSE_NAME", "Portronics Wireless Mouse")
    MOUSE_MANUFACTURER = os.getenv("MOUSE_MANUFACTURER", "Portronics")
    MOUSE_MODEL = os.getenv("MOUSE_MODEL", "Toad 23 / Wireless Optical")
    RATED_CLICKS = int(os.getenv("RATED_CLICKS", "3000000"))
    SYNC_INTERVAL_SECONDS = int(os.getenv("SYNC_INTERVAL_SECONDS", "5"))
    DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "mouselife_local.db"))
    LOG_FILE = os.getenv("LOG_FILE", str(DATA_DIR / "agent.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5173")

config = Config()
