import os
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QPolygonF
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtSvg import QSvgRenderer
import theme

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEATHER_DIR = os.path.join(BASE_DIR, "assets", "weather")

# Direct mapping to official KDE Breeze Weather SVGs
KDE_WEATHER_SVG_MAP = {
    "clear_sun": "weather-clear.svg",
    "clear_night": "weather-clear-night.svg",
    "partly_cloudy": "weather-few-clouds.svg",
    "partly_cloudy_night": "weather-few-clouds-night.svg",
    "cloudy": "weather-clouds.svg",
    "overcast": "weather-overcast.svg",
    "fog": "weather-fog.svg",
    "drizzle": "weather-showers-scattered-day.svg",
    "rain": "weather-showers-scattered-day.svg",
    "heavy_rain": "weather-showers.svg",
    "thunderstorm": "weather-storm.svg",
    "snow": "weather-snow.svg",
    "freezing_rain": "weather-freezing-rain.svg"
}

_WEATHER_ICON_CACHE = {}

# Breeze draws clouds / fog in very pale greys, which vanish on a light background
_LIGHT_THEME_SVG_COLORS = {
    "#eff1f1": "#c4ccd2",
    "#eff0f1": "#c4ccd2",
    "#b0b8b8": "#7d8a93",
    "#172525": "#3b4a50",
}


def clear_icon_cache():
    _WEATHER_ICON_CACHE.clear()


def _make_renderer(svg_path: str) -> QSvgRenderer:
    if not theme.LIGHT:
        return QSvgRenderer(svg_path)
    with open(svg_path, "r", encoding="utf-8") as fh:
        data = fh.read()
    for src, dst in _LIGHT_THEME_SVG_COLORS.items():
        data = data.replace(src, dst).replace(src.upper(), dst)
    return QSvgRenderer(data.encode("utf-8"))


def create_weather_icon(icon_type: str, size: int = 48) -> QPixmap:
    """Renders the official KDE Breeze weather vector SVG with in-memory caching."""
    cache_key = (icon_type, size, theme.LIGHT)
    if cache_key in _WEATHER_ICON_CACHE:
        return _WEATHER_ICON_CACHE[cache_key]

    svg_filename = KDE_WEATHER_SVG_MAP.get(icon_type, "weather-few-clouds.svg")
    svg_path = os.path.join(WEATHER_DIR, svg_filename)

    if os.path.exists(svg_path):
        renderer = _make_renderer(svg_path)
        if renderer.isValid():
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
            painter.end()
            _WEATHER_ICON_CACHE[cache_key] = pixmap
            return pixmap

    # Fallback if svg missing
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    _WEATHER_ICON_CACHE[cache_key] = pixmap
    return pixmap

def create_wind_arrow(degrees: float = 0, size: int = 24) -> QPixmap:
    """Renders the KDE wind dart arrow with rotation."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.translate(size / 2.0, size / 2.0)
    painter.rotate(degrees)

    scale = size / 24.0
    painter.scale(scale, scale)

    # Sleek downward arrowhead from KDE Breeze desktoptheme
    arrow = QPolygonF([
        QPointF(0, 8),      # Tip pointing down
        QPointF(-5, -7),    # Left wing
        QPointF(0, -3),     # Inner notch
        QPointF(5, -7)      # Right wing
    ])

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(theme.text_color())))
    painter.drawPolygon(arrow)

    painter.end()
    return pixmap
