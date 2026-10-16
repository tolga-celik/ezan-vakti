import os
import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QGridLayout, QFrame,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QLinearGradient, QBrush, QPen

PRAYER_DISPLAY_NAMES = [
    ("fajr", "İmsak", "🌙"),
    ("sunrise", "Güneş", "🌅"),
    ("dhuhr", "Öğle", "☀️"),
    ("asr", "İkindi", "🌤️"),
    ("maghrib", "Akşam", "🌇"),
    ("isha", "Yatsı", "🌌")
]

class PrayerCard(QFrame):
    def __init__(self, key, label, icon, parent=None):
        super().__init__(parent)
        self.key = key
        self.label_text = label
        self.icon_symbol = icon
        self.is_current = False
        self.is_next = False
        self.setObjectName("prayerCard")
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(130, 95)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)
        
        self.icon_label = QLabel(self.icon_symbol)
        self.icon_label.setStyleSheet("font-size: 16px;")
        
        self.name_label = QLabel(self.label_text)
        self.name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8;")
        
        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()

        self.time_label = QLabel("--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("font-size: 19px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px;")

        self.status_badge = QLabel("")
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setStyleSheet("font-size: 10px; font-weight: bold; color: #64748B;")

        layout.addLayout(header_layout)
        layout.addWidget(self.time_label)
        layout.addWidget(self.status_badge)

        self.update_style()

    def set_time(self, time_str):
        self.time_label.setText(time_str)

    def set_state(self, is_current: bool, is_next: bool):
        self.is_current = is_current
        self.is_next = is_next
        self.update_style()

    def update_style(self):
        if self.is_current:
            self.setStyleSheet("""
                QFrame#prayerCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(16, 185, 129, 0.25), stop:1 rgba(6, 95, 70, 0.35));
                    border: 1.5px solid #10B981;
                    border-radius: 10px;
                }
            """)
            self.name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #34D399;")
            self.time_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF;")
            self.status_badge.setText("● ŞU AN")
            self.status_badge.setStyleSheet("font-size: 10px; font-weight: bold; color: #10B981;")
        elif self.is_next:
            self.setStyleSheet("""
                QFrame#prayerCard {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(245, 158, 11, 0.2), stop:1 rgba(180, 83, 9, 0.25));
                    border: 1.5px solid #F59E0B;
                    border-radius: 10px;
                }
            """)
            self.name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FCD34D;")
            self.time_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #FFFFFF;")
            self.status_badge.setText("▼ SIRADAKİ")
            self.status_badge.setStyleSheet("font-size: 10px; font-weight: bold; color: #F59E0B;")
        else:
            self.setStyleSheet("""
                QFrame#prayerCard {
                    background-color: rgba(30, 41, 59, 0.7);
                    border: 1px solid rgba(71, 85, 105, 0.4);
                    border-radius: 10px;
                }
                QFrame#prayerCard:hover {
                    background-color: rgba(51, 65, 85, 0.85);
                    border-color: rgba(148, 163, 184, 0.5);
                }
            """)
            self.name_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8;")
            self.time_label.setStyleSheet("font-size: 19px; font-weight: 700; color: #E2E8F0;")
            self.status_badge.setText("")

class PopupWindow(QWidget):
    request_settings = pyqtSignal()
    request_refresh = pyqtSignal()

    def __init__(self, prayer_engine, settings_manager, sound_player, parent=None):
        super().__init__(parent)
        self.engine = prayer_engine
        self.settings = settings_manager
        self.sound_player = sound_player

        # Frameless popup style
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 560)

        self._drag_pos = QPoint()
        self._init_ui()

        # Update tick
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)

    def _init_ui(self):
        # Outer container layout for drop shadow padding
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(12, 12, 12, 12)

        # Main background container
        self.container = QFrame()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QFrame#container {
                background-color: rgba(15, 23, 42, 0.96);
                border: 1.5px solid rgba(51, 65, 85, 0.8);
                border-radius: 20px;
            }
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 18, 20, 18)
        container_layout.setSpacing(12)

        # 1. Header (Ottoman Logo, Title, Close Button)
        top_bar = QHBoxLayout()
        
        logo_label = QLabel("🕌")
        logo_label.setStyleSheet("font-size: 24px;")
        
        title_box = QVBoxLayout()
        title_box.setSpacing(1)
        self.title_label = QLabel("EZAN VAKTİ")
        self.title_label.setStyleSheet("font-size: 15px; font-weight: 900; color: #F8FAFC; letter-spacing: 1px;")
        
        self.city_badge = QLabel("📍 İstanbul")
        self.city_badge.setStyleSheet("font-size: 12px; color: #10B981; font-weight: bold;")
        title_box.addWidget(self.title_label)
        title_box.addWidget(self.city_badge)

        top_bar.addWidget(logo_label)
        top_bar.addLayout(title_box)
        top_bar.addStretch()

        self.btn_sound = QPushButton("🔊")
        self.btn_sound.setToolTip("Sesi Aç / Kapat")
        self.btn_sound.setFixedSize(32, 32)
        self.btn_sound.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover { background: #334155; }
        """)
        self.btn_sound.clicked.connect(self._toggle_sound)

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip("Vakitleri Yenile")
        self.btn_refresh.setFixedSize(32, 32)
        self.btn_refresh.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background: #334155; }
        """)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Gizle")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #94A3B8;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background: #EF4444; color: white; border-color: #EF4444; }
        """)
        self.btn_close.clicked.connect(self.hide)

        top_bar.addWidget(self.btn_sound)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_close)
        container_layout.addLayout(top_bar)

        # 2. Date and Live Clock Banner
        date_bar = QHBoxLayout()
        self.date_label = QLabel("--")
        self.date_label.setStyleSheet("font-size: 12px; color: #94A3B8;")
        
        self.hijri_label = QLabel("--")
        self.hijri_label.setStyleSheet("font-size: 12px; color: #FCD34D; font-weight: 500;")
        
        date_bar.addWidget(self.date_label)
        date_bar.addStretch()
        date_bar.addWidget(self.hijri_label)
        container_layout.addLayout(date_bar)

        # 3. Next Prayer Countdown Hero Card
        self.hero_card = QFrame()
        self.hero_card.setObjectName("heroCard")
        self.hero_card.setStyleSheet("""
            QFrame#heroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
                border: 1.5px solid #334155;
                border-radius: 14px;
            }
        """)
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.setContentsMargins(16, 12, 16, 12)
        hero_layout.setSpacing(6)

        hero_top = QHBoxLayout()
        self.next_title_label = QLabel("SONRAKİ VAKTE KALAN")
        self.next_title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #94A3B8; letter-spacing: 0.8px;")
        
        self.next_name_badge = QLabel("İKİNDİ (15:59)")
        self.next_name_badge.setStyleSheet("font-size: 12px; font-weight: bold; color: #F59E0B;")
        hero_top.addWidget(self.next_title_label)
        hero_top.addStretch()
        hero_top.addWidget(self.next_name_badge)
        hero_layout.addLayout(hero_top)

        self.countdown_label = QLabel("00:00:00")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("""
            font-size: 38px;
            font-weight: 900;
            color: #F8FAFC;
            letter-spacing: 2px;
            font-family: 'Monospace', 'Courier New', monospace;
        """)
        hero_layout.addWidget(self.countdown_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #0F172A;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #F59E0B);
                border-radius: 4px;
            }
        """)
        hero_layout.addWidget(self.progress_bar)

        # Kerahat Banner (Hidden by default)
        self.kerahat_banner = QLabel("")
        self.kerahat_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.kerahat_banner.setStyleSheet("""
            background-color: rgba(245, 158, 11, 0.15);
            color: #FCD34D;
            border: 1px solid rgba(245, 158, 11, 0.4);
            border-radius: 6px;
            padding: 4px;
            font-size: 11px;
            font-weight: bold;
        """)
        self.kerahat_banner.setVisible(False)
        hero_layout.addWidget(self.kerahat_banner)

        container_layout.addWidget(self.hero_card)

        # 4. Daily 6 Prayers Grid
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(10)

        self.cards = {}
        for idx, (key, label, icon) in enumerate(PRAYER_DISPLAY_NAMES):
            row = idx // 3
            col = idx % 3
            card = PrayerCard(key, label, icon, self)
            self.cards[key] = card
            grid_layout.addWidget(card, row, col)

        container_layout.addLayout(grid_layout)

        # 5. Bottom Navigation / Settings
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 4, 0, 0)

        settings_btn = QPushButton("⚙️ Ayarlar")
        settings_btn.setStyleSheet("""
            QPushButton {
                background: #1E293B;
                border: 1px solid #334155;
                color: #CBD5E1;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #334155;
                color: #F8FAFC;
            }
        """)
        settings_btn.clicked.connect(self.request_settings.emit)

        bottom_bar.addWidget(settings_btn)
        bottom_bar.addStretch()

        self.live_clock_label = QLabel("00:00:00")
        self.live_clock_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: bold; font-family: monospace;")
        bottom_bar.addWidget(self.live_clock_label)

        container_layout.addLayout(bottom_bar)
        outer_layout.addWidget(self.container)

    def _toggle_sound(self):
        cur = self.settings.get("sound_enabled", True)
        self.settings.set("sound_enabled", not cur)
        self.btn_sound.setText("🔊" if not cur else "🔇")

    def _on_refresh_clicked(self):
        self.request_refresh.emit()
        self.update_times()

    def update_times(self):
        now = datetime.datetime.now()
        data = self.engine.get_current_and_next_prayer(now)

        # Update headers
        city_name = self.settings.get("city", "İstanbul")
        self.city_badge.setText(f"📍 {city_name.capitalize()}")
        
        # Gregorian date in Turkish
        day_names_tr = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        month_names_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        
        gregorian_str = f"{now.day} {month_names_tr[now.month - 1]} {now.year} {day_names_tr[now.weekday()]}"
        self.date_label.setText(gregorian_str)
        self.hijri_label.setText(f"🌙 {data['today_timings'].get('hijri_formatted', '')}")

        # Live clock
        self.live_clock_label.setText(now.strftime("%H:%M:%S"))

        # Countdown & Hero
        self.countdown_label.setText(data["countdown_str"])
        self.next_name_badge.setText(f"{data['next_prayer_name'].upper()} ({data['next_prayer_time']})")
        self.progress_bar.setValue(int(data["progress"] * 100))

        # Kerahat Banner
        if data.get("kerahat_status"):
            self.kerahat_banner.setText(f"⚠️ {data['kerahat_status']}")
            self.kerahat_banner.setVisible(True)
        else:
            self.kerahat_banner.setVisible(False)

        # Update 6 prayer cards
        today_t = data["today_timings"]
        current_k = data["current_prayer_key"].lower()
        next_k = data["next_prayer_key"].lower()

        for key, card in self.cards.items():
            card.set_time(today_t.get(key, "--:--"))
            card.set_state(is_current=(key == current_k), is_next=(key == next_k))

        # Mute button state
        sound_enabled = self.settings.get("sound_enabled", True)
        self.btn_sound.setText("🔊" if sound_enabled else "🔇")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
