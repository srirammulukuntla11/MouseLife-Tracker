# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

block_cipher = None
agent_dir = Path(SPECPATH).resolve()
src_dir = agent_dir / "src"

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(agent_dir.parent)],
    binaries=[],
    datas=[
        (str(agent_dir / "assets"), "assets"),
        (str(agent_dir / "src"), "agent/src"),
    ],
    hiddenimports=[
        "pynput",
        "pynput.mouse",
        "pynput.mouse._win32",
        "pystray",
        "pystray._win32",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "requests",
        "dotenv",
        "sqlite3",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MouseLifeTracker",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Windowless background GUI execution
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="MouseLifeTracker",
)
