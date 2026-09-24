import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from agent.src.startup import install_startup, uninstall_startup, is_startup_enabled

def main():
    print("=== MouseLife Tracker — Startup Configuration ===")
    
    if len(sys.argv) > 1 and sys.argv[1] in ("--uninstall", "-u", "remove"):
        print("Removing MouseLife Tracker from Windows startup...")
        success = uninstall_startup()
        if success:
            print("[SUCCESS] Startup registration and legacy files removed.")
        else:
            print("[WARNING] Could not completely remove all startup items.")
        sys.exit(0 if success else 1)

    if len(sys.argv) > 1 and sys.argv[1] in ("--status", "-s", "check"):
        enabled = is_startup_enabled()
        print(f"Startup Active: {'Enabled' if enabled else 'Disabled'}")
        sys.exit(0)

    # Default action: Install/configure single startup entry idempotently
    print("Configuring strictly ONE idempotent Windows startup entry...")
    success = install_startup()
    if success:
        print("[SUCCESS] Windows startup configured successfully.")
        print(f"Startup Active: {is_startup_enabled()}")
    else:
        print("[ERROR] Failed to configure Windows startup.")
        sys.exit(1)

    # Verify Win32_StartupCommand via powershell
    try:
        ps_cmd = 'Get-CimInstance Win32_StartupCommand | Where-Object { $_.Command -like "*MouseLifeTracker*" -or $_.Name -like "*MouseLifeTracker*" } | Format-List Name, Command, Location'
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        print("\n--- Win32_StartupCommand Verification ---")
        print(res.stdout.strip() if res.stdout else "No matching entries found.")
    except Exception as e:
        print(f"Verification query error: {e}")

if __name__ == "__main__":
    main()
