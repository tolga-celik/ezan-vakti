import os
import sys
import datetime

# Absolute window positioning (dragging + remembering the spot) is impossible for normal
# windows on a native Wayland session, so when XWayland is available we run through it.
# Set EZAN_NATIVE_WAYLAND=1 to opt out.
if (
    sys.platform.startswith("linux")
    and "QT_QPA_PLATFORM" not in os.environ
    and os.environ.get("EZAN_NATIVE_WAYLAND") != "1"
    and os.environ.get("WAYLAND_DISPLAY")
    and os.environ.get("DISPLAY")
):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

# Fewer glibc malloc arenas = less memory fragmentation for this small, mostly idle app
if sys.platform.startswith("linux"):
    try:
        import ctypes
        ctypes.CDLL("libc.so.6").mallopt(-8, 2)  # M_ARENA_MAX
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

import theme  # must come before the windows: it wraps setStyleSheet for light/dark support

from settings_manager import SettingsManager
from prayer_engine import PrayerEngine
from weather_engine import WeatherEngine
from sound_player import SoundPlayer
from combined_window import CombinedWindow
from tray_icon import TrayIcon
from settings_dialog import SettingsDialog

def _single_instance_name() -> str:
    uid = os.getuid() if hasattr(os, "getuid") else "user"
    return f"ezan-vakti-single-instance-{uid}"


def _notify_running_instance() -> bool:
    """If another instance is already running, ask it to show its popup. Returns True if so."""
    sock = QLocalSocket()
    sock.connectToServer(_single_instance_name())
    if not sock.waitForConnected(500):
        return False
    sock.write(b"show")
    sock.flush()
    sock.waitForBytesWritten(500)
    sock.disconnectFromServer()
    return True


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Hava Durumu & Ezan Vakti")
    app.setApplicationDisplayName("Hava Durumu & Ezan Vakti")
    app.setOrganizationName("LinuxKDE")
    app.setDesktopFileName("ezan-vakti")
    
    # Keep running in system tray
    app.setQuitOnLastWindowClosed(False)
    theme_manager = theme.ThemeManager(app)

    # Only one instance: a second launch behaves like clicking the tray icon of the first one
    if _notify_running_instance():
        sys.exit(0)
    QLocalServer.removeServer(_single_instance_name())
    instance_server = QLocalServer()
    instance_server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    instance_server.listen(_single_instance_name())

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "assets", "icon.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Core Engines
    settings = SettingsManager()
    engine = PrayerEngine(settings)
    weather_engine = WeatherEngine(settings)
    sound_player = SoundPlayer(settings)

    # Initial data fetch
    today = datetime.date.today()
    engine.get_day_timings(today)

    # UI Windows
    window = CombinedWindow(engine, weather_engine, settings, sound_player)
    tray = TrayIcon(engine, weather_engine, settings, sound_player, window)

    def reload_location_data(force_notify: bool = False):
        """Drops every cached value of the previous location and loads the new one."""
        engine.clear_mem_cache()
        weather_engine.clear_mem_cache()

        city = settings.get("city", "Darica")
        country = settings.get("country", "Turkey")
        today_now = datetime.date.today()
        p_ok = engine.fetch_monthly_calendar(city, country, today_now.year, today_now.month)
        # Month boundary: also have next month ready so the "next prayer" never falls back
        next_month = (today_now.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
        if (next_month - today_now).days <= 3:
            engine.fetch_monthly_calendar(city, country, next_month.year, next_month.month)
        weather_engine.get_weather(city, force_refresh=True)
        window.update_all()
        tray._tick()
        return p_ok

    def open_settings():
        old_city = settings.get("city", "Darica")
        dlg = SettingsDialog(settings, engine, sound_player, window)
        accepted = dlg.exec()
        if window.isVisible():
            window.activateWindow()
        if accepted:
            if settings.get("city", "Darica") != old_city:
                reload_location_data()
            else:
                window.update_all()
                tray._tick()

    def do_refresh():
        reload_location_data()
        tray.showMessage("Hava Durumu & Ezan Vakti", "Veriler başarıyla güncellendi.", tray.MessageIcon.Information, 3000)

    window.request_settings.connect(open_settings)
    window.request_refresh.connect(do_refresh)
    theme_manager.changed.connect(window.apply_theme)

    tray.show()

    def _on_second_launch():
        while instance_server.hasPendingConnections():
            conn = instance_server.nextPendingConnection()
            conn.readyRead.connect(conn.readAll)
            conn.disconnected.connect(conn.deleteLater)
        # Same as clicking the tray icon next to the clock, but never closes an open popup
        if window.isVisible():
            window.raise_()
            window.activateWindow()
        else:
            tray.position_and_show_popup()

    instance_server.newConnection.connect(_on_second_launch)
    if instance_server.hasPendingConnections():
        _on_second_launch()

    # Give freed heap memory back to the OS a moment after the popup is closed
    trim_timer = QTimer()
    trim_timer.setSingleShot(True)
    trim_timer.setInterval(3000)

    def _trim_heap():
        try:
            import ctypes
            ctypes.CDLL("libc.so.6").malloc_trim(0)
        except Exception:
            pass

    trim_timer.timeout.connect(_trim_heap)
    window.hidden.connect(trim_timer.start)

    # Show window if --show passed
    if "--show" in sys.argv:
        tray.show_with_tab(0)
    elif not settings.get("first_run_done", False):
        # Very first launch: open the popup once, docked next to the clock
        def _first_run():
            tray.show_with_tab(0)
            settings.set("first_run_done", True)
        QTimer.singleShot(1200, _first_run)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
