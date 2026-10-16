"""Generates the small PNG glyphs (check mark and arrows) that the Qt style sheets
of the settings dialog refer to. Run once; the results live in assets/ui/."""
import os
import sys

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPolygonF

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "ui")
SIZE = 64  # drawn large, Qt scales it down smoothly


def _canvas():
    img = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return img, p


def _chevron(name, color, up):
    img, p = _canvas()
    pen = QPen(QColor(color), 7.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    if up:
        pts = [QPointF(16, 40), QPointF(32, 24), QPointF(48, 40)]
    else:
        pts = [QPointF(16, 24), QPointF(32, 40), QPointF(48, 24)]
    p.drawPolyline(QPolygonF(pts))
    p.end()
    img.save(os.path.join(OUT_DIR, name))


def _check(name, color):
    img, p = _canvas()
    pen = QPen(QColor(color), 8.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.drawPolyline(QPolygonF([QPointF(15, 33), QPointF(27, 45), QPointF(49, 20)]))
    p.end()
    img.save(os.path.join(OUT_DIR, name))


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    os.makedirs(OUT_DIR, exist_ok=True)
    _check("check.png", "#0B1220")
    _chevron("arrow_down.png", "#9CA3AF", up=False)
    _chevron("arrow_up.png", "#9CA3AF", up=True)
    _chevron("arrow_down_hover.png", "#38BDF8", up=False)
    _chevron("arrow_up_hover.png", "#38BDF8", up=True)

    # Light-theme variants (theme.py rewrites /ui/arrow_* to /ui/light/arrow_*)
    LIGHT_DIR = os.path.join(OUT_DIR, "light")
    os.makedirs(LIGHT_DIR, exist_ok=True)
    OUT_DIR = LIGHT_DIR
    _chevron("arrow_down.png", "#6B7280", up=False)
    _chevron("arrow_up.png", "#6B7280", up=True)
    _chevron("arrow_down_hover.png", "#0284C7", up=False)
    _chevron("arrow_up_hover.png", "#0284C7", up=True)
    _check("check.png", "#FFFFFF")
    print("icons written to", OUT_DIR)
