"""Serve simulated printer cameras over MJPEG for development, demos, and screenshots.

Usage:
    python scripts/demo_camera.py            # serves on http://127.0.0.1:3031
    python scripts/demo_camera.py --port 8080

Endpoints:
    /video      ELEGOO-style FDM printer MJPEG stream
    /resin      resin printer MJPEG stream
    /snapshot   single JPEG frame (FDM view)

The frames are drawn locally with Qt; no real camera or network access is involved.
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

if sys.platform.startswith("linux") and not (
    os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
    QRadialGradient,
)

WIDTH, HEIGHT = 1280, 720
BOUNDARY = b"printwatchframe"
_render_lock = threading.Lock()


def _overlay(painter: QPainter, label: str) -> None:
    painter.setPen(QColor(255, 255, 255, 230))
    font = QFont("Consolas", 18)
    font.setStyleHint(QFont.StyleHint.Monospace)
    painter.setFont(font)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    painter.drawText(24, 40, f"{label}   {stamp}")


def _grain(painter: QPainter, seed: float) -> None:
    painter.setPen(Qt.PenStyle.NoPen)
    for i in range(220):
        x = (math.sin(i * 12.9898 + seed) * 43758.5453) % 1 * WIDTH
        y = (math.sin(i * 78.233 + seed) * 12345.6789) % 1 * HEIGHT
        painter.setBrush(QColor(255, 255, 255, 10))
        painter.drawEllipse(QPointF(abs(x), abs(y)), 1.2, 1.2)


def render_fdm(t: float) -> QImage:
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB32)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Enclosure background with a warm LED wash.
    bg = QLinearGradient(0, 0, 0, HEIGHT)
    bg.setColorAt(0, QColor(38, 40, 46))
    bg.setColorAt(1, QColor(18, 19, 22))
    p.fillRect(image.rect(), bg)
    glow = QRadialGradient(WIDTH * 0.5, 40, WIDTH * 0.6)
    glow.setColorAt(0, QColor(255, 236, 200, 70))
    glow.setColorAt(1, QColor(255, 236, 200, 0))
    p.fillRect(image.rect(), glow)

    # Textured PEI build plate in perspective.
    plate = QPolygonF([QPointF(230, 470), QPointF(1050, 470), QPointF(1210, 690), QPointF(70, 690)])
    plate_grad = QLinearGradient(0, 470, 0, 690)
    plate_grad.setColorAt(0, QColor(70, 66, 58))
    plate_grad.setColorAt(1, QColor(112, 102, 84))
    p.setPen(QPen(QColor(30, 30, 30), 3))
    p.setBrush(plate_grad)
    p.drawPolygon(plate)
    p.setPen(QPen(QColor(255, 255, 255, 18), 1))
    for i in range(1, 12):
        f = i / 12
        p.drawLine(QPointF(230 + 820 * f, 470), QPointF(70 + 1140 * f, 690))

    # Partially printed vase: stacked layers that grow over time.
    progress = 0.55 + 0.25 * ((t / 90) % 1)
    cx, base_y, max_h = 640, 600, 300
    layers = int(90 * progress)
    for layer in range(layers):
        y = base_y - layer * (max_h / 90)
        radius = 120 + 45 * math.sin(layer / 90 * math.pi * 1.4)
        shade = 150 + int(40 * math.sin(layer * 0.9))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(min(255, shade + 60), int(shade * 0.55), 40))
        p.drawEllipse(QRectF(cx - radius, y - radius * 0.18, radius * 2, radius * 0.36))
    top_y = base_y - layers * (max_h / 90)
    top_r = 120 + 45 * math.sin(layers / 90 * math.pi * 1.4)

    # Gantry rail and toolhead that sweeps around the current layer.
    angle = t * 2.4
    head_x = cx + math.cos(angle) * top_r
    head_y = top_y + math.sin(angle) * top_r * 0.18
    p.setBrush(QColor(52, 54, 60))
    p.setPen(QPen(QColor(20, 20, 20), 2))
    p.drawRect(QRectF(0, head_y - 175, WIDTH, 34))
    p.setBrush(QColor(28, 29, 33))
    p.drawRoundedRect(QRectF(head_x - 70, head_y - 165, 140, 120), 14, 14)
    p.setBrush(QColor(230, 120, 30))
    p.drawRoundedRect(QRectF(head_x - 60, head_y - 150, 46, 10), 4, 4)
    nozzle = QPainterPath()
    nozzle.moveTo(head_x - 16, head_y - 45)
    nozzle.lineTo(head_x + 16, head_y - 45)
    nozzle.lineTo(head_x + 4, head_y - 8)
    nozzle.lineTo(head_x - 4, head_y - 8)
    nozzle.closeSubpath()
    p.setBrush(QColor(200, 160, 70))
    p.drawPath(nozzle)

    _grain(p, t)
    _overlay(p, "FDM · Bed cam")
    p.end()
    return image


def render_resin(t: float) -> QImage:
    image = QImage(WIDTH, HEIGHT, QImage.Format.Format_RGB32)
    p = QPainter(image)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = QLinearGradient(0, 0, 0, HEIGHT)
    bg.setColorAt(0, QColor(24, 20, 14))
    bg.setColorAt(1, QColor(10, 9, 8))
    p.fillRect(image.rect(), bg)

    # Amber UV-blocking lid tint.
    tint = QRadialGradient(WIDTH * 0.5, HEIGHT * 0.55, WIDTH * 0.55)
    tint.setColorAt(0, QColor(255, 150, 20, 60))
    tint.setColorAt(1, QColor(255, 120, 0, 0))
    p.fillRect(image.rect(), tint)

    # Z-axis rail.
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(90, 92, 98))
    p.drawRect(QRectF(1000, 60, 46, 600))

    # Build plate moving up and down in a peel cycle.
    lift = (math.sin(t * 1.3) + 1) / 2
    plate_y = 230 + 150 * (1 - lift)
    p.setBrush(QColor(170, 172, 178))
    p.drawRect(QRectF(380, plate_y - 30, 520, 36))
    p.setBrush(QColor(130, 132, 138))
    p.drawRect(QRectF(900, plate_y - 24, 110, 24))

    # Miniatures hanging from the plate.
    p.setBrush(QColor(110, 150, 160, 235))
    for i, x in enumerate((470, 600, 730)):
        height = 70 + 25 * i
        body = QPainterPath()
        body.moveTo(x - 30, plate_y + 6)
        body.lineTo(x + 30, plate_y + 6)
        body.lineTo(x + 18, plate_y + 6 + height)
        body.lineTo(x - 18, plate_y + 6 + height)
        body.closeSubpath()
        p.drawPath(body)
        p.drawEllipse(QPointF(x, plate_y + 6 + height + 14), 18, 18)

    # Resin vat.
    vat = QRectF(330, 520, 620, 120)
    p.setBrush(QColor(40, 42, 46))
    p.drawRoundedRect(vat.adjusted(-14, -10, 14, 14), 10, 10)
    resin = QLinearGradient(0, vat.top(), 0, vat.bottom())
    resin.setColorAt(0, QColor(95, 130, 140, 240))
    resin.setColorAt(1, QColor(50, 75, 85, 255))
    p.setBrush(resin)
    p.drawRect(vat)

    _grain(p, t * 1.7)
    _overlay(p, "Resin · Vat cam")
    p.end()
    return image


RENDERERS = {"/video": render_fdm, "/resin": render_resin, "/snapshot": render_fdm}


def encode_jpeg(image: QImage) -> bytes:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "JPG", 82)
    return bytes(buffer.data())


def frame(path: str) -> bytes:
    with _render_lock:
        return encode_jpeg(RENDERERS[path](time.monotonic()))


class Handler(BaseHTTPRequestHandler):
    fps = 10

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write(f"[demo-camera] {self.address_string()} {format % args}\n")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path not in RENDERERS:
            self.send_error(404, "Use /video, /resin, or /snapshot")
            return
        if path == "/snapshot":
            data = frame(path)
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(200)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY.decode()}")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        try:
            while True:
                data = frame(path)
                self.wfile.write(b"--" + BOUNDARY + b"\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                self.wfile.write(data + b"\r\n")
                time.sleep(1 / self.fps)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            return


def make_server(host: str, port: int) -> ThreadingHTTPServer:
    """Create (but do not start) a demo camera server. Requires a QGuiApplication."""
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    return server


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=3031)
    parser.add_argument("--fps", type=int, default=10)
    args = parser.parse_args()

    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
    Handler.fps = max(1, args.fps)
    server = make_server(args.host, args.port)
    base = f"http://{args.host}:{server.server_port}"
    print(f"Demo cameras running:\n  FDM    {base}/video\n  Resin  {base}/resin")
    print(f"  JPEG   {base}/snapshot\nPress Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
