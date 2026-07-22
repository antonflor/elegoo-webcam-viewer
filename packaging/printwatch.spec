# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

project_root = Path.cwd()
src_root = project_root / "src"
entrypoint = src_root / "printwatch" / "__main__.py"

block_cipher = None

a = Analysis(
    [str(entrypoint)],
    pathex=[str(src_root)],
    binaries=[],
    datas=[],
    hiddenimports=["PyQt6.QtWebEngineCore", "PyQt6.QtWebEngineWidgets"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PrintWatch Desktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
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
    upx=False,
    name="PrintWatch Desktop",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="PrintWatch Desktop.app",
        icon=None,
        bundle_identifier="xyz.montylabs.printwatch",
        version="0.1.0",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "14.0",
        },
    )
