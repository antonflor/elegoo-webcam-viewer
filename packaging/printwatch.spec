# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import sys

project_root = Path.cwd()
src_root = project_root / "src"
entrypoint = src_root / "printwatch" / "__main__.py"
sys.path.insert(0, str(src_root))

from printwatch import __version__

block_cipher = None

a = Analysis(
    [str(entrypoint)],
    pathex=[str(src_root)],
    binaries=[],
    datas=[(str(src_root / "printwatch" / "assets"), "printwatch/assets")],
    hiddenimports=["PySide6.QtNetwork", "PySide6.QtSvg"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PyQt6"],
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
    icon=str(project_root / "packaging" / "icons" / "printwatch.ico"),
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
        icon=str(project_root / "packaging" / "icons" / "printwatch.icns"),
        bundle_identifier="xyz.montylabs.printwatch",
        version=__version__,
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "14.0",
        },
    )
