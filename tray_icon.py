import os
import time
import datetime
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication
)
from PyQt6.QtGui import QIcon, QAction, QCursor, QPixmap, QPainter, QPainterPath, QPolygonF, QTransform, QColor, QFont, QFontMetrics
from PyQt6.QtCore import QTimer, QPoint, QPointF, QRect, QRectF, Qt
from PyQt6.QtSvg import QSvgRenderer
import theme

class TrayIcon(QSystemTrayIcon):
    def __init__(self, prayer_engine, weather_engine, settings_manager, sound_player, popup_window, parent=None):
        super().__init__(parent)
        self.engine = prayer_engine
        self.weather_engine = weather_engine
        self.settings = settings_manager
        self.sound_player = sound_player
        self.popup = popup_window

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tray_icon_path = os.path.join(self.base_dir, "assets", "tray_icon.svg")
        self.app_icon_path = os.path.join(self.base_dir, "assets", "icon.svg")

        # Set Icon
        self.icon = QIcon(self.tray_icon_path if os.path.exists(self.tray_icon_path) else self.app_icon_path)
        self.setIcon(self.icon)

        # Alerted records
        self.alerted_events = set()
        self._last_tooltip = ""
        self._last_badge = None

        self._init_menu()
        self.activated.connect(self._on_activated)

        # Connect menu open to populate items on demand
        self.menu.aboutToShow.connect(self._update_menu_info)

        # Ticker
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

        # Initial tick
        self._tick()

    def _init_menu(self):
        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1F2429;
                color: #F8FAFC;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #38BDF8;
                color: #0F172A;
                font-weight: bold;
            }
            QMenu::item:disabled {
                color: #9CA3AF;
            }
            QMenu::separator {
                height: 1px;
                background: #30363D;
                margin: 4px 8px;
            }
        """)

        # Visible only while an adhan / alert is playing
        self.stop_adhan_action = QAction("■ Ezanı Durdur", self.menu)
        self.stop_adhan_action.triggered.connect(self.sound_player.stop_alert)
        self.stop_adhan_action.setVisible(self.sound_player.is_playing())
        self.sound_player.playing_changed.connect(self.stop_adhan_action.setVisible)
        self.menu.addAction(self.stop_adhan_action)
        self.stop_separator = self.menu.addSeparator()
        self.stop_separator.setVisible(self.sound_player.is_playing())
        self.sound_player.playing_changed.connect(self.stop_separator.setVisible)

        # Title Items
        self.weather_action = QAction("⛅ Hava Durumu: Yükleniyor...", self.menu)
        self.weather_action.setEnabled(False)
        self.menu.addAction(self.weather_action)

        self.next_info_action = QAction("🕌 Ezan Vakti: Yükleniyor...", self.menu)
        self.next_info_action.setEnabled(False)
        self.menu.addAction(self.next_info_action)

        self.menu.addSeparator()

        # Show Weather Tab
        self.show_weather_act = QAction("⛅ Hava Durumu (7 Gün)", self.menu)
        self.show_weather_act.triggered.connect(lambda: self.show_with_tab(0))
        self.menu.addAction(self.show_weather_act)

        # Show Ezan Tab
        self.show_ezan_act = QAction("🕌 Ezan Vakitleri", self.menu)
        self.show_ezan_act.triggered.connect(lambda: self.show_with_tab(1))
        self.menu.addAction(self.show_ezan_act)

        # Settings
        self.settings_action = QAction("⚙️ Ayarlar", self.menu)
        self.settings_action.triggered.connect(self.popup.request_settings.emit)
        self.menu.addAction(self.settings_action)

        # Refresh
        self.refresh_action = QAction("🔄 Verileri Yenile", self.menu)
        self.refresh_action.triggered.connect(self.popup.request_refresh.emit)
        self.menu.addAction(self.refresh_action)

        # Reset remembered window position
        self.reset_pos_action = QAction("📍 Pencere Konumunu Sıfırla", self.menu)
        self.reset_pos_action.triggered.connect(self.popup.reset_saved_position)
        self.menu.addAction(self.reset_pos_action)

        self.menu.addSeparator()

        # Audio Toggle Checkbox
        self.audio_action = QAction("🔊 Sesli Bildirimler", self.menu, checkable=True)
        self.audio_action.setChecked(self.settings.get("sound_enabled", True))
        self.audio_action.triggered.connect(self._toggle_sound_from_menu)
        self.menu.addAction(self.audio_action)

        # Autostart Toggle
        self.autostart_action = QAction("🚀 Başlangıçta Çalıştır", self.menu, checkable=True)
        self.autostart_action.setChecked(self.settings.get("autostart", False))
        self.autostart_action.triggered.connect(self._toggle_autostart_from_menu)
        self.menu.addAction(self.autostart_action)

        self.menu.addSeparator()

        # Quit
        self.quit_action = QAction("✕ Çıkış", self.menu)
        self.quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)

    def _toggle_sound_from_menu(self):
        val = self.audio_action.isChecked()
        self.settings.set("sound_enabled", val)

    def _toggle_autostart_from_menu(self):
        val = self.autostart_action.isChecked()
        self.settings.set("autostart", val)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_popup()
        elif reason == QSystemTrayIcon.ActivationReason.MiddleClick:
            # Quick way to silence a running adhan
            self.sound_player.stop_alert()

    def show_with_tab(self, tab_idx: int):
        self.popup.switch_tab(tab_idx)
        if not self.popup.isVisible():
            self.position_and_show_popup()
        else:
            self.popup.raise_()
            self.popup.activateWindow()

    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide()
        else:
            # The same click that moved focus away (click-outside close) also hits the tray icon:
            # treat it as 'close' instead of reopening the popup
            if time.monotonic() - self.popup.last_autohide < 0.4:
                return
            # Opened by clicking the tray icon -> the cursor is right next to the clock
            self.position_and_show_popup(prefer_cursor=True)

    def position_and_show_popup(self, prefer_cursor: bool = False):
        # Remembered (dragged) position wins; otherwise dock next to the clock / system tray
        self.popup.place_window(prefer_cursor=prefer_cursor)
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    def _update_menu_info(self):
        """Called on-demand only when the right-click tray menu is opened."""
        now = datetime.datetime.now()
        p_data = self.engine.get_current_and_next_prayer(now)
        city = self.settings.get("city", "Darica").capitalize()
        next_p = p_data["next_prayer_name"]
        next_time = p_data["next_prayer_time"]
        countdown = p_data["countdown_str"]

        w_data = self.weather_engine.get_weather(city)
        temp_str = w_data.get("current_temp", "14 °C")
        cond_str = w_data.get("condition_name", "Bulutlu")

        self.weather_action.setText(f"⛅ {city}: {temp_str} ({cond_str})")
        self.next_info_action.setText(f"🕌 {next_p}: {next_time} (Kalan: {countdown})")
        self.audio_action.setChecked(self.settings.get("sound_enabled", True))
        self.autostart_action.setChecked(self.settings.get("autostart", False))

    @staticmethod
    def _badge_text(rem_sec: int) -> str:
        """Minutes left until the next prayer; whole hours ("2s") once it is an hour or more."""
        if rem_sec >= 3600:
            return f"{rem_sec // 3600}s"
        return str(max(1, -(-rem_sec // 60)))   # ceil to whole minutes

    def _render_badge_icon(self, label: str, soon: bool) -> QIcon:
        """Anatolian (classical Ottoman) mosque whose body doubles as the display for `label`.

        Drawn in a 64x64 design grid: a wide central dome with cascading semi-domes (Sinan-style
        profile), two pencil-thin minarets with two balconies and long conical caps, and a body that
        carries the remaining time as plain text (no badge). Near prayer time (`soon`) the green
        parts switch to the amber family of the icon's gold accents."""
        icon = QIcon()
        if soon:
            body_c, dome_c, semi_c, text_c = QColor("#92400E"), QColor("#D97706"), QColor("#B45309"), QColor("#FFFFFF")
        else:
            body_c, dome_c, semi_c, text_c = QColor("#064E3B"), QColor("#059669"), QColor("#047857"), QColor("#FFFFFF")
        # white minarets would vanish on a light panel
        gold, gold_dark, minaret = QColor("#FDE68A"), QColor("#F59E0B"), QColor("#94A3B8" if theme.LIGHT else "#F8FAFC")

        for size in (16, 22, 24, 32, 48, 64, 96, 128):
            pm = QPixmap(size, size)
            pm.fill(Qt.GlobalColor.transparent)
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.scale(size / 64.0, size / 64.0)
            p.setPen(Qt.PenStyle.NoPen)

            # Pencil minarets (kalem minare): slender shaft, two balconies, long conical cap, gold alem
            for cx in (5.5, 58.5):
                p.setBrush(minaret)
                p.drawRect(QRectF(cx - 1.25, 20, 2.5, 42))
                p.drawPolygon(QPolygonF([QPointF(cx - 1.25, 20), QPointF(cx, 4.5), QPointF(cx + 1.25, 20)]))
                p.setBrush(gold_dark)
                p.drawRoundedRect(QRectF(cx - 2.8, 33, 5.6, 1.8), 0.6, 0.6)   # lower balcony
                p.drawRoundedRect(QRectF(cx - 2.3, 24, 4.6, 1.6), 0.6, 0.6)   # upper balcony
                p.setBrush(gold)
                p.drawEllipse(QPointF(cx, 3.6), 1.2, 1.2)

            # Cascading semi-domes (yarım kubbeler) leaning against the central dome
            p.setBrush(semi_c)
            for mirror in (False, True):
                semi = QPainterPath()
                semi.moveTo(9, 34)
                semi.cubicTo(9, 27, 15, 25, 23, 27)
                semi.lineTo(23, 34)
                semi.closeSubpath()
                if mirror:
                    semi = QTransform(-1, 0, 0, 1, 64, 0).map(semi)
                p.drawPath(semi)

            # Wide central dome (ana kubbe) with a gold crescent alem
            p.setBrush(dome_c)
            dome = QPainterPath()
            dome.moveTo(15.5, 31)
            dome.cubicTo(15.5, 7, 48.5, 7, 48.5, 31)
            dome.closeSubpath()
            p.drawPath(dome)
            p.setBrush(gold)
            p.drawRect(QRectF(31.5, 8.5, 1, 4))
            crescent = QPainterPath()
            crescent.addEllipse(QPointF(32, 5.4), 3.2, 3.2)
            cut = QPainterPath()
            cut.addEllipse(QPointF(33.3, 4.7), 2.7, 2.7)
            p.drawPath(crescent.subtracted(cut))

            # Body (the "display") with a thin gold cornice
            p.setBrush(body_c)
            p.drawRoundedRect(QRectF(9, 31, 46, 31), 2.5, 2.5)
            p.setBrush(gold)
            p.drawRect(QRectF(9, 31, 46, 1.6))

            # Remaining time as plain text inside the body
            text_rect = QRectF(9, 33, 46, 29)
            font = QFont()
            font.setWeight(QFont.Weight.Black)
            px = 30.0 * (1.0 if len(label) <= 2 else 0.8)        # design-grid pixels
            font.setPixelSize(max(1, int(round(px * size / 64.0))))
            fm = QFontMetrics(font)
            max_w = text_rect.width() * size / 64.0 * 0.94
            while fm.horizontalAdvance(label) > max_w and font.pixelSize() > 6:
                font.setPixelSize(font.pixelSize() - 1)
                fm = QFontMetrics(font)
            p.resetTransform()
            p.setFont(font)
            p.setPen(text_c)
            scaled = QRectF(text_rect.x() * size / 64.0, text_rect.y() * size / 64.0,
                            text_rect.width() * size / 64.0, text_rect.height() * size / 64.0)
            p.drawText(scaled, Qt.AlignmentFlag.AlignCenter, label)
            p.end()
            icon.addPixmap(pm)
        return icon

    def _update_badge(self, rem_sec: int):
        label = self._badge_text(rem_sec)
        soon = rem_sec <= self.settings.get("early_notification_minutes", 15) * 60
        key = (label, soon, theme.LIGHT)
        if key != self._last_badge:   # redraw only when it changes (about once a minute)
            self._last_badge = key
            self.setIcon(self._render_badge_icon(label, soon))

    def _tick(self):
        now = datetime.datetime.now()
        p_data = self.engine.get_current_and_next_prayer(now)

        city = self.settings.get("city", "Darica").capitalize()
        next_p = p_data["next_prayer_name"]
        next_time = p_data["next_prayer_time"]
        rem_sec = p_data["remaining_seconds"]
        date_str = now.strftime("%Y-%m-%d")
        self._update_badge(rem_sec)

        # Format remaining time cleanly
        if rem_sec >= 3600:
            h = rem_sec // 3600
            m = (rem_sec % 3600) // 60
            cd_display = f"{h} sa {m} dk"
        elif rem_sec >= 60:
            m = rem_sec // 60
            cd_display = f"{m} dk"
        else:
            cd_display = f"{rem_sec} sn"

        # Weather snapshot (instant RAM cache lookup)
        w_data = self.weather_engine.get_weather(city)
        temp_str = w_data.get("current_temp", "14 °C")
        cond_str = w_data.get("condition_name", "Bulutlu")

        # Tooltip - Only send DBus update when string actually changes (once per minute)
        tooltip = (
            f"📍 {city} | {temp_str} ({cond_str})\n"
            f"🕌 Sonraki Vakit: {next_p} ({next_time})\n"
            f"⏱️ Kalan Süre: {cd_display}"
        )
        if p_data.get("kerahat_status"):
            tooltip += f"\n⚠️ {p_data['kerahat_status']}"

        if tooltip != self._last_tooltip:
            self._last_tooltip = tooltip
            self.setToolTip(tooltip)

        # Check Notifications and Sound Alerts
        next_key = p_data.get("next_prayer_key", "dhuhr").lower()
        if self.settings.get("early_notification_enabled", True):
            early_min = self.settings.get("early_notification_minutes", 15)
            early_target_sec = early_min * 60
            if 0 < rem_sec <= early_target_sec:
                event_key = (date_str, next_p, "early")
                if event_key not in self.alerted_events:
                    self.alerted_events.add(event_key)
                    if self.settings.get("notifications_enabled", True):
                        self.showMessage(
                            f"Ezan Vakti Yaklaşıyor ({city})",
                            f"{next_p} vaktine {early_min} dakika kaldı. ({next_time})",
                            QSystemTrayIcon.MessageIcon.Information,
                            7000
                        )
                    # Play gentle chime for early reminder
                    self.sound_player.play_alert("chime")

        if rem_sec <= 2:
            event_key = (date_str, next_p, "exact")
            if event_key not in self.alerted_events:
                self.alerted_events.add(event_key)
                if self.settings.get("notifications_enabled", True):
                    self.showMessage(
                        f"Vakit Girdi ({city})",
                        f"{next_p} vakti girdi. ({next_time})",
                        QSystemTrayIcon.MessageIcon.Information,
                        10000
                    )
                # Play specific Makam Ezan for this prayer
                self.sound_player.play_alert(next_key)
