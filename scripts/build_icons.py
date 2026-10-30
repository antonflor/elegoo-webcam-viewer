"""Render packaging icons (PNG, Windows ICO, macOS ICNS) from the app's SVG logo.

Usage:
    python scripts/build_icons.py

Writes to packaging/icons/. Both ICO and ICNS embed PNG images, which every supported
Windows and macOS version reads, so no extra imaging dependency is needed.
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / "src" / "printwatch" / "assets" / "printwatch.svg"
OUT = ROOT / "packaging" / "icons"


def render_png(renderer: QSvgRenderer, size: int) -> bytes:
    image = QImage(size, size, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return bytes(buffer.data())


def build_ico(images: dict[int, bytes]) -> bytes:
    sizes = sorted(images)
    header = struct.pack("<HHH", 0, 1, len(sizes))
    offset = len(header) + 16 * len(sizes)
    entries, payload = b"", b""
    for size in sizes:
        data = images[size]
        dimension = 0 if size >= 256 else size
        entries += struct.pack(
            "<BBBBHHII", dimension, dimension, 0, 0, 1, 32, len(data), offset + len(payload)
        )
        payload += data
    return header + entries + payload


def build_icns(images: dict[int, bytes]) -> bytes:
    types = {32: b"ic11", 64: b"ic12", 128: b"ic07", 256: b"ic08", 512: b"ic09", 1024: b"ic10"}
    body = b"".join(
        types[size] + struct.pack(">I", len(images[size]) + 8) + images[size]
        for size in sorted(types)
    )
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def main() -> int:
    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    renderer = QSvgRenderer(str(SVG))
    if not renderer.isValid():
        raise SystemExit(f"Could not read {SVG}")
    sizes = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
    images = {size: render_png(renderer, size) for size in sizes}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "printwatch.png").write_bytes(images[512])
    (OUT / "printwatch.ico").write_bytes(
        build_ico({size: images[size] for size in (16, 24, 32, 48, 64, 128, 256)})
    )
    (OUT / "printwatch.icns").write_bytes(build_icns(images))
    print(f"Icons written to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
