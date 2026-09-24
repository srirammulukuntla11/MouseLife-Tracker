import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configure utf-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def build():
    agent_dir = Path(__file__).resolve().parent
    spec_file = agent_dir / "mouselife_agent.spec"
    dist_dir = agent_dir / "dist"

    print(f"Building single-process MouseLifeTracker.exe using {spec_file.name}...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    result = subprocess.run(cmd, cwd=str(agent_dir), env=env)
    if result.returncode == 0:
        # Move onedir contents into dist_dir root so MouseLifeTracker.exe is directly at agent/dist/MouseLifeTracker.exe
        sub_dist = dist_dir / "MouseLifeTracker"
        if sub_dist.exists() and sub_dist.is_dir():
            for item in sub_dist.iterdir():
                dest = dist_dir / item.name
                if item.name == "data":
                    # Never overwrite persistent database directory
                    continue
                if dest.exists():
                    if dest.is_dir():
                        shutil.rmtree(dest)
                    else:
                        dest.unlink()
                shutil.move(str(item), str(dist_dir))
            try:
                sub_dist.rmdir()
            except Exception:
                pass

        dist_exe = dist_dir / "MouseLifeTracker.exe"
        print(f"\n[SUCCESS] Standalone single-process executable built successfully at: {dist_exe}")
    else:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    build()
