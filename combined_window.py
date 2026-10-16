import os
import time
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QGridLayout, QFrame,
    QStackedWidget, QGraphicsDropShadowEffect, QSizePolicy, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect, QEvent
from PyQt6.QtGui import QColor, QFont, QIcon, QCursor, QGuiApplication

from weather_icons import create_weather_icon, create_wind_arrow
import theme

# ========================================================
# 1. 7-DAY WEATHER COLUMN COMPONENT
# ========================================================
class WeatherDayColumn(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("weatherDayCol")
        self.setStyleSheet("""
            QFrame#weatherDayCol { background: transparent; border: none; }
            QLabel { background: transparent; border: none; }
        """)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1. Day Name (e.g. Cum)
        self.day_label = QLabel("---")
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.day_label.setStyleSheet("color: #E5E7EB; font-size: 13px; font-weight: bold;")

        # 2. Weather Icon
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(36, 36)

        # 3. Rain / Precip Prob (e.g. ☂ %88 or -)
        self.rain_label = QLabel("-")
        self.rain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.rain_label.setStyleSheet("color: #E5E7EB; font-size: 11px;")

        # 4. Max Temp (e.g. 15 °C)
        self.max_temp_label = QLabel("-- °C")
        self.max_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.max_temp_label.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: bold;")

        # 5. Min Temp (e.g. 10 °C)
        self.min_temp_label = QLabel("-- °C")
        self.min_temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.min_temp_label.setStyleSheet("color: #9CA3AF; font-size: 12px;")

        layout.addWidget(self.day_label)
        layout.addWidget(self.icon_label)
        layout.addWidget(self.rain_label)
        layout.addWidget(self.max_temp_label)
        layout.addWidget(self.min_temp_label)

    def set_data(self, day_abbr: str, icon_type: str, precip: str, max_t: str, min_t: str):
        self.day_label.setText(day_abbr)
        self.icon_label.setPixmap(create_weather_icon(icon_type, 36))
        
        if precip and precip != "-":
            self.rain_label.setText(f"☂ {precip}")
        else:
            self.rain_label.setText("-")

        self.max_temp_label.setText(max_t)
        self.min_temp_label.setText(min_t)


# ========================================================
# 2. SLEEK, MINIMALIST PRAYER CARD (SON DERECE SADE VE ŞIK)
# ========================================================
class SleekPrayerCard(QFrame):
    def __init__(self, key, label, icon_sym, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label
        self.icon_sym = icon_sym
        self.is_current = False
        self.is_next = False
        self.setObjectName("sleekPrayerCard")
        self._init_ui()

    def _init_ui(self):
        self.setFixedHeight(98)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # Header: Name and Status Badge (Clean, unboxed)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        
        self.name_lbl = QLabel(f"{self.icon_sym}  {self.label_text}")
        self.name_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600; background: transparent; border: none;")
        
        self.badge_lbl = QLabel("")
        self.badge_lbl.setStyleSheet("font-size: 10px; font-weight: bold; background: transparent; border: none;")
        
        header.addWidget(self.name_lbl)
        header.addStretch()
        header.addWidget(self.badge_lbl)

        # Time: Crisp, large, uncluttered
        self.time_lbl = QLabel("--:--")
        self.time_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_lbl.setStyleSheet("color: #F8FAFC; font-size: 22px; font-weight: 700; letter-spacing: 1px; background: transparent; border: none;")

        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(self.time_lbl)
        layout.addStretch()

        self.update_style()

    def set_time(self, time_str):
        if self.time_lbl.text() != time_str:
            self.time_lbl.setText(time_str)

    def set_state(self, is_current: bool, is_next: bool):
        if self.is_current == is_current and self.is_next == is_next:
            return
        self.is_current = is_current
        self.is_next = is_next
        self.update_style()

    def update_style(self):
        if self.is_current:
            self.setStyleSheet("""
                QFrame#sleekPrayerCard {
                    background-color: rgba(56, 189, 248, 0.12);
                    border: 1.5px solid #38BDF8;
                    border-radius: 10px;
                }
                QLabel { background: transparent; border: none; }
            """)
            self.name_lbl.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: bold; background: transparent;")
            self.time_lbl.setStyleSheet("color: #FFFFFF; font-size: 23px; font-weight: 800; letter-spacing: 1px; background: transparent;")
            self.badge_lbl.setText("● ŞU AN")
            self.badge_lbl.setStyleSheet("color: #38BDF8; font-size: 10px; font-weight: bold; background: transparent;")
        elif self.is_next:
            self.setStyleSheet("""
                QFrame#sleekPrayerCard {
                    background-color: rgba(245, 158, 11, 0.10);
                    border: 1.5px solid #F59E0B;
                    border-radius: 10px;
                }
                QLabel { background: transparent; border: none; }
            """)
            self.name_lbl.setStyleSheet("color: #FCD34D; font-size: 12px; font-weight: bold; background: transparent;")
            self.time_lbl.setStyleSheet("color: #FFFFFF; font-size: 23px; font-weight: 800; letter-spacing: 1px; background: transparent;")
            self.badge_lbl.setText("▼ SIRADAKİ")
            self.badge_lbl.setStyleSheet("color: #F59E0B; font-size: 10px; font-weight: bold; background: transparent;")
        else:
            self.setStyleSheet("""
                QFrame#sleekPrayerCard {
                    background-color: #252B32;
                    border: 1px solid #313740;
                    border-radius: 10px;
                }
                QFrame#sleekPrayerCard:hover {
                    background-color: #2B313A;
                    border-color: #434B57;
                }
                QLabel { background: transparent; border: none; }
            """)
            self.name_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600; background: transparent;")
            self.time_lbl.setStyleSheet("color: #E2E8F0; font-size: 22px; font-weight: 700; letter-spacing: 1px; background: transparent;")
            self.badge_lbl.setText("")


# ========================================================
# 3. SLEEK METRIC DETAIL CARD (AYRINTILAR SEKMESİ İÇİN)
# ========================================================
class MetricDetailCard(QFrame):
    def __init__(self, icon_str, title_str, default_val, parent=None):
        super().__init__(parent)
        self.setObjectName("metricDetailCard")
        self.setStyleSheet("""
            QFrame#metricDetailCard {
                background-color: #252B32;
                border: 1px solid #313740;
                border-radius: 10px;
            }
            QFrame#metricDetailCard:hover {
                background-color: #2B313A;
                border-color: #38BDF8;
            }
            QLabel { background: transparent; border: none; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(2)
        self.setFixedHeight(58)

        # Title Row
        title_box = QHBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        
        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 14px; background: transparent;")
        
        self.title_lbl = QLabel(title_str)
        self.title_lbl.setStyleSheet("color: #9CA3AF; font-size: 12px; font-weight: 600; background: transparent;")
        
        title_box.addWidget(icon_lbl)
        title_box.addWidget(self.title_lbl)
        title_box.addStretch()

        # Value
        self.value_lbl = QLabel(default_val)
        self.value_lbl.setStyleSheet("color: #FFFFFF; font-size: 16px; font-weight: bold; background: transparent;")

        layout.addLayout(title_box)
        layout.addWidget(self.value_lbl)

    def set_value(self, val_str: str):
        if self.value_lbl.text() != val_str:
            self.value_lbl.setText(val_str)


# ========================================================
# 4. MAIN COMBINED WINDOW
# ========================================================
class CombinedWindow(QWidget):
    request_settings = pyqtSignal()
    request_refresh = pyqtSignal()
    hidden = pyqtSignal()

    def __init__(self, prayer_engine, weather_engine, settings_manager, sound_player, parent=None):
        super().__init__(parent)
        self.engine = prayer_engine
        self.weather_engine = weather_engine
        self.settings = settings_manager
        self.sound_player = sound_player

        self.is_pinned = False
        self._drag_pos = QPoint()
        self._suppress_save_until = 0.0
        self._was_active = False       # becomes True once the popup really had keyboard focus
        self.last_autohide = 0.0       # monotonic time of the last click-outside close

        # Debounced saver: remembers where the user dropped the window
        self._save_pos_timer = QTimer(self)
        self._save_pos_timer.setSingleShot(True)
        self._save_pos_timer.setInterval(500)
        self._save_pos_timer.timeout.connect(self._persist_position)

        # Frameless popup style
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(460)

        self._init_ui()
        self._apply_fitted_height()
        self._ui_ready = True

        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(1000)

        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.update_weather)
        self.weather_timer.start(15 * 60 * 1000)

        # Initial data update
        self.update_all()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Background Container (exact dark color #1F2429 from screenshot)
        self.container = QFrame()
        self.container.setObjectName("mainContainer")
        self.container.setStyleSheet("""
            QFrame#mainContainer {
                background-color: #1F2429;
                border: 1px solid #30363D;
                border-radius: 14px;
            }
            QLabel { background: transparent; }
        """)

        # Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 70 if theme.LIGHT else 180))
        shadow.setOffset(0, 6)
        self._shadow = shadow
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(18, 14, 18, 16)
        container_layout.setSpacing(8)

        # ========================================================
        # 1. TOP HEADER (Back arrow, Title, Settings, Pin)
        # ========================================================
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 2)

        self.btn_back = QPushButton("〈")
        self.btn_back.setToolTip("Geri")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #9CA3AF;
                font-size: 18px;
                font-weight: bold;
                padding: 0 4px;
            }
            QPushButton:hover { color: #FFFFFF; }
        """)
        self.btn_back.clicked.connect(self._on_back_clicked)

        self.title_label = QLabel("Hava Durumu Raporu")
        self.title_label.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 500;")

        top_bar.addWidget(self.btn_back)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch()

        def _header_button(text, tooltip, font_px, hover_fg, hover_bg):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    border-radius: 15px;
                    color: #9CA3AF;
                    font-size: {font_px}px;
                    font-weight: bold;
                    padding: 0;
                }}
                QPushButton:hover {{ color: {hover_fg}; background: {hover_bg}; }}
                QPushButton:pressed {{ background: {hover_bg}; }}
            """)
            return btn

        self.btn_settings = _header_button("⊶", "Ayarlar", 17, "#FFFFFF", "rgba(255,255,255,0.08)")
        self.btn_settings.clicked.connect(self.request_settings.emit)

        self.btn_pin = _header_button("📌", "Masaüstünde Sabitle", 14, "#38BDF8", "rgba(56,189,248,0.14)")
        self.btn_pin.clicked.connect(self._toggle_pin)
        self._apply_pin_style()

        self.btn_close = _header_button("✕", "Kapat", 13, "#FFFFFE", "#EF4444")  # #FFFFFE: stays white in the light theme
        self.btn_close.clicked.connect(self._close_popup)

        top_bar.addWidget(self.btn_settings)
        top_bar.addWidget(self.btn_pin)
        top_bar.addWidget(self.btn_close)
        container_layout.addLayout(top_bar)

        # Shown only while an adhan / alert is playing: one click stops it
        self.adhan_banner = QFrame()
        self.adhan_banner.setObjectName("adhanBanner")
        self.adhan_banner.setFixedHeight(38)
        self.adhan_banner.setStyleSheet("""
            QFrame#adhanBanner {
                background-color: rgba(239, 68, 68, 0.14);
                border: 1px solid rgba(239, 68, 68, 0.55);
                border-radius: 8px;
            }
            QLabel { background: transparent; border: none; color: #FCA5A5; font-size: 12px; font-weight: bold; }
            QPushButton {
                background-color: #EF4444;
                border: none;
                border-radius: 6px;
                color: #FFFFFE;
                font-size: 12px;
                font-weight: bold;
                padding: 0 12px;
            }
            QPushButton:hover { background-color: #F87171; }
            QPushButton:pressed { background-color: #DC2626; }
        """)
        banner_lay = QHBoxLayout(self.adhan_banner)
        banner_lay.setContentsMargins(12, 4, 6, 4)
        banner_lay.addWidget(QLabel("🔊  Ezan okunuyor"))
        banner_lay.addStretch()
        self.btn_stop_adhan = QPushButton("■  Ezanı Durdur")
        self.btn_stop_adhan.setFixedHeight(28)
        self.btn_stop_adhan.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop_adhan.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_stop_adhan.clicked.connect(self.sound_player.stop_alert)
        banner_lay.addWidget(self.btn_stop_adhan)
        self.adhan_banner.setVisible(self.sound_player.is_playing())
        self.sound_player.playing_changed.connect(self._on_playing_changed)
        container_layout.addWidget(self.adhan_banner)

        # ========================================================
        # 2. LOCATION (Darıca, Turkey, TR)
        # ========================================================
        self.loc_label = QLabel("Darıca, Turkey, TR")
        self.loc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loc_label.setStyleSheet("color: #F3F4F6; font-size: 17px; font-weight: 400; letter-spacing: 0.3px;")
        container_layout.addWidget(self.loc_label)

        # ========================================================
        # 3. CURRENT HERO ROW (14 °C | Weather Icon | Wind Arrow + 3,5 m/sn)
        # ========================================================
        hero_row = QHBoxLayout()
        hero_row.setContentsMargins(14, 2, 14, 4)

        self.temp_label = QLabel("14 °C")
        self.temp_label.setStyleSheet("color: #FFFFFF; font-size: 34px; font-weight: bold;")
        hero_row.addWidget(self.temp_label)
        hero_row.addStretch()

        self.hero_weather_icon = QLabel()
        self.hero_weather_icon.setFixedSize(54, 54)
        self.hero_weather_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_row.addWidget(self.hero_weather_icon)
        hero_row.addStretch()

        wind_layout = QVBoxLayout()
        wind_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wind_layout.setSpacing(2)

        self.wind_arrow_lbl = QLabel()
        self.wind_arrow_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wind_arrow_lbl.setPixmap(create_wind_arrow(0, 20))

        self.wind_speed_lbl = QLabel("3,5 m/sn")
        self.wind_speed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.wind_speed_lbl.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 500;")

        wind_layout.addWidget(self.wind_arrow_lbl)
        wind_layout.addWidget(self.wind_speed_lbl)
        hero_row.addLayout(wind_layout)

        container_layout.addLayout(hero_row)

        # ========================================================
        # 4. QUICK EZAN BANNER (Shown only on Weather 7-Day Tab)
        # ========================================================
        self.ezan_quick_card = QFrame()
        self.ezan_quick_card.setObjectName("ezanQuickCard")
        self.ezan_quick_card.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ezan_quick_card.setStyleSheet("""
            QFrame#ezanQuickCard {
                background-color: #252B32;
                border: 1px solid #333A44;
                border-radius: 8px;
            }
            QFrame#ezanQuickCard:hover {
                border-color: #38BDF8;
                background-color: #2B313A;
            }
            QLabel { background: transparent; border: none; }
        """)
        ezan_quick_layout = QHBoxLayout(self.ezan_quick_card)
        ezan_quick_layout.setContentsMargins(10, 6, 10, 6)

        self.quick_mosque_icon = QLabel("🕌")
        self.quick_mosque_icon.setStyleSheet("font-size: 14px;")
        
        self.quick_prayer_text = QLabel("Sonraki Vakit: İkindi (15:57)")
        self.quick_prayer_text.setStyleSheet("color: #E5E7EB; font-size: 12px; font-weight: bold;")
        
        self.quick_countdown_text = QLabel("00:40:00 kaldı")
        self.quick_countdown_text.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: 800; font-family: monospace;")

        ezan_quick_layout.addWidget(self.quick_mosque_icon)
        ezan_quick_layout.addWidget(self.quick_prayer_text)
        ezan_quick_layout.addStretch()
        ezan_quick_layout.addWidget(self.quick_countdown_text)
        
        self.ezan_quick_card.mousePressEvent = lambda e: self.switch_tab(1)
        container_layout.addWidget(self.ezan_quick_card)

        # ========================================================
        # 5. TAB BAR (7 Gün | Ezan Vakti | Ayrıntılar)
        # ========================================================
        self.tab_bar_layout = QHBoxLayout()
        self.tab_bar_layout.setContentsMargins(0, 4, 0, 0)
        self.tab_bar_layout.setSpacing(0)

        self.btn_tab_7days = QPushButton("7 Gün")
        self.btn_tab_ezan = QPushButton("Ezan Vakti")
        self.btn_tab_details = QPushButton("Ayrıntılar")

        for idx, btn in enumerate([self.btn_tab_7days, self.btn_tab_ezan, self.btn_tab_details]):
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.clicked.connect(lambda checked, i=idx: self.switch_tab(i))
            self.tab_bar_layout.addWidget(btn)

        container_layout.addLayout(self.tab_bar_layout)

        # Cyan Underline Track Indicator
        self.tab_indicator_frame = QFrame()
        self.tab_indicator_frame.setFixedHeight(3)
        self.tab_indicator_frame.setStyleSheet("background-color: #2B3138; border: none;")
        self.tab_indicator_line = QFrame(self.tab_indicator_frame)
        self.tab_indicator_line.setFixedHeight(3)
        self.tab_indicator_line.setStyleSheet("background-color: #38BDF8; border: none;")
        container_layout.addWidget(self.tab_indicator_frame)

        # ========================================================
        # 6. STACKED PAGES
        # ========================================================
        self.stack = QStackedWidget()

        # ----------------------------------------------------
        # PAGE 0: 7-Day Weather Grid (Exact Screenshot Match)
        # ----------------------------------------------------
        self.page_7days = QWidget()
        page_7days_layout = QHBoxLayout(self.page_7days)
        page_7days_layout.setContentsMargins(0, 8, 0, 0)
        page_7days_layout.setSpacing(4)

        self.day_columns = []
        for _ in range(7):
            col = WeatherDayColumn(self.page_7days)
            self.day_columns.append(col)
            page_7days_layout.addWidget(col)

        self.stack.addWidget(self.page_7days)

        # ----------------------------------------------------
        # PAGE 1: Ezan Vakitleri Page (SON DERECE SADE VE ŞIK)
        # ----------------------------------------------------
        self.page_ezan = QWidget()
        page_ezan_layout = QVBoxLayout(self.page_ezan)
        page_ezan_layout.setContentsMargins(0, 10, 0, 0)
        page_ezan_layout.setSpacing(10)

        # Header banner inside Ezan tab: Hijri date & Kerahat alert
        ezan_header_box = QHBoxLayout()
        ezan_header_box.setContentsMargins(4, 0, 4, 0)

        self.hijri_lbl = QLabel("🌙 5 Cemaziyelevvel 1448")
        self.hijri_lbl.setStyleSheet("color: #FCD34D; font-size: 13px; font-weight: 600;")

        self.kerahat_lbl = QLabel("")
        self.kerahat_lbl.setStyleSheet("""
            color: #F59E0B;
            font-size: 11px;
            font-weight: 600;
            background: transparent;
            border: none;
            padding: 0 6px 0 0;
        """)
        self.kerahat_lbl.setVisible(False)

        self.ezan_tab_countdown_lbl = QLabel("İkindi vaktine 00:40:00 kaldı")
        self.ezan_tab_countdown_lbl.setStyleSheet("color: #38BDF8; font-size: 12px; font-weight: bold;")

        ezan_header_box.addWidget(self.hijri_lbl)
        ezan_header_box.addStretch()
        ezan_header_box.addWidget(self.kerahat_lbl)
        ezan_header_box.addWidget(self.ezan_tab_countdown_lbl)
        page_ezan_layout.addLayout(ezan_header_box)

        # Slim Progress Bar
        self.ezan_progress = QProgressBar()
        self.ezan_progress.setFixedHeight(4)
        self.ezan_progress.setTextVisible(False)
        self.ezan_progress.setStyleSheet("""
            QProgressBar {
                background-color: #262B32;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38BDF8, stop:1 #10B981);
                border-radius: 2px;
            }
        """)
        page_ezan_layout.addWidget(self.ezan_progress)

        # 6 Clean Prayer Cards (2 rows x 3 columns)
        ezan_grid = QGridLayout()
        ezan_grid.setHorizontalSpacing(10)
        ezan_grid.setVerticalSpacing(10)

        self.prayer_cards = {}
        prayers_def = [
            ("fajr", "İmsak", "🌙"),
            ("sunrise", "Güneş", "🌅"),
            ("dhuhr", "Öğle", "☀️"),
            ("asr", "İkindi", "🌤️"),
            ("maghrib", "Akşam", "🌇"),
            ("isha", "Yatsı", "🌌")
        ]

        for i, (k, name, sym) in enumerate(prayers_def):
            row = i // 3
            col = i % 3
            card = SleekPrayerCard(k, name, sym, self.page_ezan)
            self.prayer_cards[k] = card
            ezan_grid.addWidget(card, row, col)

        page_ezan_layout.addLayout(ezan_grid)
        page_ezan_layout.addStretch()
        self.stack.addWidget(self.page_ezan)

        # ----------------------------------------------------
        # PAGE 2: Ayrıntılar (Details) - Full Rich Metrics Grid
        # ----------------------------------------------------
        self.page_details = QWidget()
        page_details_layout = QGridLayout(self.page_details)
        page_details_layout.setContentsMargins(2, 8, 2, 0)
        page_details_layout.setHorizontalSpacing(10)
        page_details_layout.setVerticalSpacing(10)

        self.metric_cards = {}
        details_defs = [
            ("apparent", "🌡️", "Hissedilen Sıcaklık", "13 °C"),
            ("humidity", "💧", "Bağıl Nem", "%75"),
            ("wind_full", "💨", "Rüzgar Hızı & Yönü", "3,6 m/sn"),
            ("pressure", "🧭", "Hava Basıncı", "1010 hPa"),
            ("uv_index", "☀️", "UV İndeksi", "1,5 (Düşük)"),
            ("sun_times", "🌅", "Güneş Doğuş & Batış", "07:14 / 18:21"),
            ("qibla", "🕋", "Kıble Açısı", "152° Güneydoğu"),
            ("hijri", "🌙", "Hicri Takvim", "5 Cemaziyelevvel 1448")
        ]

        for idx, (m_id, m_icon, m_title, m_default) in enumerate(details_defs):
            row = idx // 2
            col = idx % 2
            card = MetricDetailCard(m_icon, m_title, m_default, self.page_details)
            self.metric_cards[m_id] = card
            page_details_layout.addWidget(card, row, col)

        self.stack.addWidget(self.page_details)
        container_layout.addWidget(self.stack)

        main_layout.addWidget(self.container)

        # Default tab: 7 Gün
        self.switch_tab(0)

    def switch_tab(self, index: int, refit: bool = True):
        self.stack.setCurrentIndex(index)

        # The stack takes exactly the height of the visible page; otherwise the shortest tab
        # (7 Gün) would be stretched to the height of the tallest one, leaving empty bands.
        page = self.stack.widget(index)
        if page.layout() is not None:
            page.layout().activate()
            self.stack.setFixedHeight(page.layout().totalMinimumSize().height())

        # The "Sonraki Vakit" quick card stays visible on every tab
        self.ezan_quick_card.setVisible(True)
        if index == 0:
            self.title_label.setText("Hava Durumu Raporu")
        elif index == 1:
            self.title_label.setText("Ezan Vakti Raporu")
        else:
            self.title_label.setText("Ayrıntılar & Rapor")

        tab_buttons = [self.btn_tab_7days, self.btn_tab_ezan, self.btn_tab_details]
        for i, btn in enumerate(tab_buttons):
            if i == index:
                btn.setChecked(True)
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        color: #FFFFFF;
                        font-size: 13px;
                        font-weight: bold;
                        padding: 6px 0;
                    }
                """)
            else:
                btn.setChecked(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        border: none;
                        color: #9CA3AF;
                        font-size: 13px;
                        font-weight: 500;
                        padding: 6px 0;
                    }
                    QPushButton:hover { color: #D1D5DB; }
                """)

        total_w = self.container.width() - 36
        tab_w = total_w / 3.0
        self.tab_indicator_line.setGeometry(int(index * tab_w), 0, int(tab_w), 3)

        if refit and getattr(self, "_ui_ready", False):
            self._refit_keep_edge()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.switch_tab(self.stack.currentIndex(), refit=False)

    def _on_back_clicked(self):
        cur = self.stack.currentIndex()
        if cur > 0:
            self.switch_tab(0)
        else:
            self.hide()

    def _apply_pin_style(self):
        if self.is_pinned:
            self.btn_pin.setToolTip("Sabitlendi – dışarı tıklayınca kapanmaz (kaldırmak için tekrar tıklayın)")
            self.btn_pin.setStyleSheet("""
                QPushButton {
                    background: rgba(56, 189, 248, 0.22);
                    border: 1px solid #38BDF8;
                    border-radius: 15px;
                    color: #FFFFFF;
                    font-size: 14px;
                    padding: 0;
                }
                QPushButton:hover { background: rgba(56, 189, 248, 0.34); }
            """)
        else:
            self.btn_pin.setToolTip("Sabitle – açık kalsın, dışarı tıklayınca kapanmasın")
            self.btn_pin.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: 1px solid transparent;
                    border-radius: 15px;
                    color: #9CA3AF;
                    font-size: 14px;
                    padding: 0;
                }
                QPushButton:hover { background: rgba(56, 189, 248, 0.14); }
                QPushButton:pressed { background: rgba(56, 189, 248, 0.14); }
            """)

    def _toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self._apply_pin_style()

    # ----------------------------------------------------
    # Close when the user clicks outside (unless pinned)
    # ----------------------------------------------------
    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self._was_active = True
            elif self._was_active and self.isVisible() and not self.is_pinned:
                # Let the window system finish switching focus before deciding
                QTimer.singleShot(120, self._maybe_autohide)

    def _maybe_autohide(self):
        if not self.isVisible() or self.is_pinned or self.isActiveWindow():
            return
        # Our own dialogs (settings, file chooser, ...) and menus must not close the popup
        if QApplication.activeModalWidget() is not None:
            return
        active = QApplication.activeWindow()
        if active is not None and (active is self or active.window() is self or self.isAncestorOf(active)
                                   or active.parent() is self):
            return
        self.last_autohide = time.monotonic()
        self._save_pos_timer.stop()
        self.hide()

    def update_all(self):
        self.update_weather()
        self.update_prayer()

    def update_weather(self):
        city = self.settings.get("city", "Darica")
        data = self.weather_engine.get_weather(city)

        self.loc_label.setText(data.get("location", f"{city}, Turkey, TR"))
        self.temp_label.setText(data.get("current_temp", "14 °C"))
        
        # Weather Icon from official KDE Breeze.
        # Same icon as today's column in the 7-day row, so both always show the same thing.
        daily_list = data.get("daily", [])
        icon_type = data.get("icon_type", "thunderstorm")
        if daily_list:
            icon_type = daily_list[0].get("icon_type", icon_type)
        self.hero_weather_icon.setPixmap(create_weather_icon(icon_type, 54))

        # Wind
        self.wind_speed_lbl.setText(data.get("wind_speed", "3,5 m/sn"))
        wind_deg = data.get("wind_direction", 0)
        self.wind_arrow_lbl.setPixmap(create_wind_arrow(wind_deg, 20))

        # 7-day columns
        daily = data.get("daily", [])
        for i in range(min(7, len(daily))):
            d = daily[i]
            self.day_columns[i].set_data(
                day_abbr=d.get("day_abbr", ""),
                icon_type=d.get("icon_type", "clear_sun"),
                precip=d.get("precip_prob", "-"),
                max_t=d.get("max_temp", "--"),
                min_t=d.get("min_temp", "--")
            )

        # Update Metrics in Ayrıntılar tab
        if "apparent" in self.metric_cards:
            self.metric_cards["apparent"].set_value(data.get("apparent_temp", "13 °C"))
        if "humidity" in self.metric_cards:
            self.metric_cards["humidity"].set_value(data.get("humidity", "%75"))
        if "wind_full" in self.metric_cards:
            self.metric_cards["wind_full"].set_value(data.get("wind_full", "3,6 m/sn"))
        if "pressure" in self.metric_cards:
            self.metric_cards["pressure"].set_value(data.get("pressure", "1010 hPa"))
        if "uv_index" in self.metric_cards:
            self.metric_cards["uv_index"].set_value(data.get("uv_index", "1,5"))
        if "sun_times" in self.metric_cards:
            s_rise = data.get("sunrise", "07:14")
            s_set = data.get("sunset", "18:21")
            self.metric_cards["sun_times"].set_value(f"{s_rise} / {s_set}")

    def update_prayer(self):
        now = datetime.datetime.now()
        p_data = self.engine.get_current_and_next_prayer(now)

        next_p = p_data["next_prayer_name"]
        next_time = p_data["next_prayer_time"]
        countdown = p_data["countdown_str"]

        # Quick Banner on Weather Page
        quick_p_text = f"Sonraki Vakit: {next_p} ({next_time})"
        if self.quick_prayer_text.text() != quick_p_text:
            self.quick_prayer_text.setText(quick_p_text)

        quick_cd_text = f"{countdown} kaldı"
        if self.quick_countdown_text.text() != quick_cd_text:
            self.quick_countdown_text.setText(quick_cd_text)

        # In Ezan tab
        ezan_cd_text = f"{next_p} vaktine {countdown} kaldı"
        if self.ezan_tab_countdown_lbl.text() != ezan_cd_text:
            self.ezan_tab_countdown_lbl.setText(ezan_cd_text)

        hijri_formatted = p_data["today_timings"].get("hijri_formatted", "")
        hijri_text = f"🌙 {hijri_formatted}"
        if self.hijri_lbl.text() != hijri_text:
            self.hijri_lbl.setText(hijri_text)

        # Kerahat Warning
        if p_data.get("kerahat_status"):
            k_txt = "<span style='font-size:7px;'>●</span>&nbsp; Kerahat vakti"
            if self.kerahat_lbl.text() != k_txt:
                self.kerahat_lbl.setText(k_txt)
            if self.kerahat_lbl.toolTip() != p_data['kerahat_status']:
                self.kerahat_lbl.setToolTip(p_data['kerahat_status'])
            if not self.kerahat_lbl.isVisible():
                self.kerahat_lbl.setVisible(True)
                self.ezan_tab_countdown_lbl.setVisible(False)
        else:
            if self.kerahat_lbl.isVisible():
                self.kerahat_lbl.setVisible(False)
                self.ezan_tab_countdown_lbl.setVisible(True)

        # Progress bar
        prog_val = int(p_data["progress"] * 100)
        if self.ezan_progress.value() != prog_val:
            self.ezan_progress.setValue(prog_val)

        # 6 Sleek Prayer Cards
        today_t = p_data["today_timings"]
        current_k = p_data["current_prayer_key"].lower()
        next_k = p_data["next_prayer_key"].lower()

        for key, card in self.prayer_cards.items():
            card.set_time(today_t.get(key, "--:--"))
            card.set_state(is_current=(key == current_k), is_next=(key == next_k))

        # Update Hijri and Qibla in Ayrıntılar tab
        if "hijri" in self.metric_cards:
            self.metric_cards["hijri"].set_value(hijri_formatted or "5 Cemaziyelevvel 1448")
        if "qibla" in self.metric_cards:
            self.metric_cards["qibla"].set_value("152° Güneydoğu")

    def _on_tick(self):
        # High-performance guard: completely skip UI calculation when window is closed
        if not self.isVisible():
            return
        self.update_prayer()

    def apply_theme(self, light: bool):
        """Style sheets are re-applied by theme.retheme(); refresh what is drawn in code."""
        self._shadow.setColor(QColor(0, 0, 0, 70 if light else 180))
        self.update_weather()
        self.update_prayer()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.hidden.emit()

    def showEvent(self, event):
        super().showEvent(event)
        # Moves made by the window manager while mapping must not be saved as a user choice
        self._suppress_save_until = time.monotonic() + 1.0
        self._was_active = False
        self.update_all()

    def _fit_height(self) -> int:
        """Minimum height that shows the current tab without clipping (tabs differ in height)."""
        lay = self.layout()
        # setFixedHeight() on the stack only posts a LayoutRequest; deliver it so the outer
        # layout measures the up-to-date stack height
        QApplication.sendPostedEvents(None, QEvent.Type.LayoutRequest)
        for i in range(self.stack.count()):
            self.stack.widget(i).updateGeometry()
        self.stack.updateGeometry()
        self.stack.layout().invalidate()
        lay.invalidate()
        lay.activate()
        return lay.totalMinimumSize().height()

    def _apply_fitted_height(self):
        self.setFixedHeight(self._fit_height() + 4)

    def _refit_keep_edge(self):
        """Re-fits the height and, if the popup sits near the bottom (panel), keeps the bottom edge put."""
        old_h = self.height()
        self._apply_fitted_height()
        delta = self.height() - old_h
        if self.isVisible() and delta:
            # Grow / shrink away from the panel: keep the edge nearest to it where it is
            screen = QGuiApplication.screenAt(self.geometry().center()) or QGuiApplication.primaryScreen()
            if self.geometry().center().y() > screen.availableGeometry().center().y():
                self._suppress_save_until = time.monotonic() + 1.0
                self.move(self.x(), self.y() - delta)

    def _on_playing_changed(self, playing: bool):
        if self.adhan_banner.isHidden() != playing:
            return  # banner already in the right state
        self.adhan_banner.setVisible(playing)
        self._refit_keep_edge()

    def _close_popup(self):
        self._save_pos_timer.stop()
        self.hide()

    # ----------------------------------------------------
    # Dragging & remembered position
    # ----------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            # Preferred: let the compositor / window manager move the window (works on X11 and Wayland)
            if handle is not None and handle.startSystemMove():
                self._drag_pos = QPoint()
                event.accept()
                return
            # Fallback: manual move
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint()
        super().mouseReleaseEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        # Only a real drag (left button held) counts as the user's choice; moves made by the
        # window manager, by re-fitting the height or by placing the window are ignored
        dragging = bool(QGuiApplication.mouseButtons() & Qt.MouseButton.LeftButton)
        if self.isVisible() and dragging and time.monotonic() >= self._suppress_save_until:
            self._save_pos_timer.start()  # restarts on every move -> saves once the drag settles

    def _persist_position(self):
        if self.isVisible():
            self.settings.set_window_pos(self.x(), self.y())

    def reset_saved_position(self):
        """Forgets the dragged position; the next show opens next to the clock again."""
        self._save_pos_timer.stop()
        self.settings.set_window_pos(None, None)
        if self.isVisible():
            self.place_window()

    def _valid_saved_position(self):
        pos = self.settings.get("window_pos")
        if not (isinstance(pos, (list, tuple)) and len(pos) == 2):
            return None
        try:
            pt = QPoint(int(pos[0]), int(pos[1]))
        except (TypeError, ValueError):
            return None
        rect = QRect(pt, self.size())
        for screen in QGuiApplication.screens():
            avail = screen.availableGeometry()
            inter = avail.intersected(rect)
            # Only trust it if enough of the window is on a currently connected screen
            if inter.width() >= 100 and inter.height() >= 60:
                x = max(avail.left(), min(pt.x(), avail.right() - self.width() + 1))
                y = max(avail.top(), min(pt.y(), avail.bottom() - self.height() + 1))
                return QPoint(x, y)
        return None

    def _default_position(self, prefer_cursor: bool):
        """Next to the clock / system tray: docked against the panel edge, right aligned.

        The cursor is only used to pick the screen (multi-monitor); the spot itself is fixed so
        the popup does not wander around depending on where the tray icon / panel was clicked."""
        cursor = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor) if prefer_cursor else None
        screen = screen or QGuiApplication.primaryScreen()
        full = screen.geometry()
        avail = screen.availableGeometry()
        w, h = self.width(), self.height()

        # The panel is the side where the usable area is smaller than the screen
        gaps = {
            "bottom": full.bottom() - avail.bottom(),
            "top": avail.top() - full.top(),
            "right": full.right() - avail.right(),
            "left": avail.left() - full.left(),
        }
        edge = max(gaps, key=gaps.get) if max(gaps.values()) > 0 else "bottom"

        gap = 22  # small breathing room between the popup and the panel / screen edge
        right_x = avail.right() - w + 1 - (gap if edge == "right" else 0)
        bottom_y = avail.bottom() - h + 1 - (gap if edge == "bottom" else 0)
        if edge in ("bottom", "top"):
            x = right_x
            y = bottom_y if edge == "bottom" else avail.top() + gap
        else:
            y = bottom_y
            x = right_x if edge == "right" else avail.left() + gap

        x = max(avail.left(), min(x, right_x))
        y = max(avail.top(), min(y, bottom_y))
        return QPoint(x, y)

    def place_window(self, prefer_cursor: bool = False):
        """Moves the window to the remembered spot, or next to the clock when there is none."""
        self._suppress_save_until = time.monotonic() + 1.0
        target = self._valid_saved_position() or self._default_position(prefer_cursor)
        self.move(target)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and not self.is_pinned:
            self.hide()
        else:
            super().keyPressEvent(event)
