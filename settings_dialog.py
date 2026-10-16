import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox,
    QSpinBox, QPushButton, QFileDialog, QGroupBox, QLineEdit, QWidget,
    QListView, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt
from cities_data import TURKEY_PROVINCES

MAKAM_INFO = [
    ("fajr", "Sabah (Saba Makamı)", "sabah-ezani.mp3"),
    ("dhuhr", "Öğle (Uşşak Makamı)", "ogle-ezani.mp3"),
    ("asr", "İkindi (Rast Makamı)", "ikindi-ezani.mp3"),
    ("maghrib", "Akşam (Segah Makamı)", "aksam-ezani.mp3"),
    ("isha", "Yatsı (Hicaz Makamı)", "yatsi-ezani.mp3")
]

LABEL_W = 100      # one shared label column width -> every field lines up perfectly
FIELD_H = 36       # one shared control height
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ui").replace("\\", "/")

STYLE = """
    QDialog {
        background-color: #1F2429;
        color: #F8FAFC;
        font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
    }
    QLabel {
        color: #E2E8F0;
        font-size: 13px;
        background: transparent;
        border: none;
    }
    QLabel#fieldLabel { color: #CBD5E1; }
    QLabel#hintLabel  { color: #94A3B8; font-size: 12px; }
    QLabel#infoLabel  { color: #94A3B8; font-size: 13px; }

    QGroupBox {
        border: 1px solid #30363D;
        border-radius: 10px;
        margin-top: 14px;
        padding-top: 14px;
        font-weight: bold;
        color: #38BDF8;
        font-size: 13px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }

    QComboBox, QLineEdit, QSpinBox {
        background-color: #272C33;
        border: 1px solid #3A414D;
        border-radius: 8px;
        color: #F8FAFC;
        padding: 0px 12px;
        min-height: 34px;
        max-height: 34px;
        font-size: 13px;
        selection-background-color: #38BDF8;
        selection-color: #0F172A;
    }
    QComboBox:hover, QLineEdit:hover, QSpinBox:hover { border-color: #4B5563; }
    QComboBox:focus, QLineEdit:focus, QSpinBox:focus,
    QComboBox:on { border: 1px solid #38BDF8; }
    QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled {
        color: #64748B; background-color: #232830; border-color: #2F353E;
    }

    QComboBox { padding-right: 36px; }
    QComboBox::drop-down {
        subcontrol-origin: border;
        subcontrol-position: center right;
        width: 34px;
        border: none;
        background: transparent;
    }
    QComboBox::down-arrow {
        image: url(__UI__/arrow_down.png);
        width: 12px;
        height: 12px;
    }
    QComboBox QAbstractItemView {
        background-color: #272C33;
        color: #F8FAFC;
        border: 1px solid #3A414D;
        padding: 4px;
        outline: 0;
        selection-background-color: #38BDF8;
        selection-color: #0F172A;
    }
    QComboBox QAbstractItemView::item {
        min-height: 28px;
        padding: 0 8px;
    }

    QSpinBox { padding-right: 30px; }
    QSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 26px;
        height: 17px;
        border: none;
        background: transparent;
    }
    QSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 26px;
        height: 17px;
        border: none;
        background: transparent;
    }
    QSpinBox::up-arrow   { image: url(__UI__/arrow_up.png);   width: 10px; height: 10px; }
    QSpinBox::down-arrow { image: url(__UI__/arrow_down.png); width: 10px; height: 10px; }
    QSpinBox::up-arrow:hover   { image: url(__UI__/arrow_up_hover.png); }
    QSpinBox::down-arrow:hover { image: url(__UI__/arrow_down_hover.png); }

    QCheckBox {
        color: #E2E8F0;
        spacing: 10px;
        font-size: 13px;
        background: transparent;
        border: none;
    }
    QCheckBox:disabled { color: #64748B; }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 1.5px solid #475569;
        background-color: #272C33;
    }
    QCheckBox::indicator:hover { border-color: #38BDF8; }
    QCheckBox::indicator:checked {
        background-color: #38BDF8;
        border-color: #38BDF8;
        image: url(__UI__/check.png);
    }
    QCheckBox::indicator:disabled { border-color: #2F353E; background-color: #232830; }

    QPushButton {
        background-color: #272C33;
        border: 1px solid #3A414D;
        color: #F8FAFC;
        border-radius: 8px;
        padding: 0px 14px;
        min-height: 34px;
        max-height: 34px;
        font-size: 13px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #333A44;
        border-color: #38BDF8;
        color: #FFFFFF;
    }
    QPushButton:pressed { background-color: #1B2026; }
    QPushButton#primaryBtn {
        background-color: #0284C7;
        border: 1px solid #38BDF8;
        color: #FFFFFE;
        font-weight: bold;
        min-height: 36px;
        max-height: 36px;
    }
    QPushButton#primaryBtn:hover { background-color: #38BDF8; color: #0F172A; }
    QPushButton#stopBtn {
        background-color: #3A1B1F;
        border: 1px solid #EF4444;
        color: #FCA5A5;
    }
    QPushButton#stopBtn:hover { background-color: #7F1D1D; color: #FFFFFE; }

    QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
    QScrollBar::handle:vertical { background: #3A414D; border-radius: 4px; min-height: 24px; }
    QScrollBar::handle:vertical:hover { background: #38BDF8; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
""".replace("__UI__", UI_DIR)


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("fieldLabel")
    lbl.setFixedWidth(LABEL_W)
    lbl.setFixedHeight(FIELD_H)
    lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
    return lbl


def _row(label_text: str, *widgets, stretch_first: bool = True) -> QWidget:
    """A label + controls row; fixed height so nothing can clip or jump."""
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    lay.addWidget(_field_label(label_text))
    for i, w in enumerate(widgets):
        lay.addWidget(w, 1 if (i == 0 and stretch_first) else 0)
    box.setFixedHeight(FIELD_H)
    return box


def _make_combo() -> QComboBox:
    combo = QComboBox()
    combo.setView(QListView())     # makes the style sheet apply to the popup on every platform
    combo.setFixedHeight(FIELD_H)
    combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(10)
    return combo


class SettingsDialog(QDialog):
    def __init__(self, settings_manager, prayer_engine, sound_player, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.engine = prayer_engine
        self.sound_player = sound_player

        # NOTE: window titles are plain text - a single "&" is displayed as "&"
        self.setWindowTitle("Ayarlar — Hava Durumu & Ezan Vakti")
        self.setFixedWidth(560)
        self.setStyleSheet(STYLE)

        self._init_ui()

    # ------------------------------------------------------------------
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 14, 20, 20)
        main_layout.setSpacing(12)

        # ----------------------------------------------------
        # 1. Konum
        # ----------------------------------------------------
        loc_group = QGroupBox("📍  Konum ve Hesaplama")
        loc_layout = QVBoxLayout(loc_group)
        loc_layout.setSpacing(10)
        loc_layout.setContentsMargins(16, 12, 16, 14)

        self.city_combo = _make_combo()
        self.city_combo.setMaxVisibleItems(12)
        self.city_combo.addItem("— Listeden seçin —", None)
        for display_name, api_name in TURKEY_PROVINCES:
            self.city_combo.addItem(display_name, api_name)
        loc_layout.addWidget(_row("İl / İlçe:", self.city_combo))

        self.custom_city_input = QLineEdit()
        self.custom_city_input.setFixedHeight(FIELD_H)
        self.custom_city_input.setClearButtonEnabled(True)
        self.custom_city_input.setPlaceholderText("Örn: Darıca, Gebze, Berlin, Londra")
        loc_layout.addWidget(_row("Manuel Şehir:", self.custom_city_input))

        self.location_hint = QLabel("")
        self.location_hint.setObjectName("hintLabel")
        self.location_hint.setContentsMargins(LABEL_W + 8, 0, 0, 0)
        loc_layout.addWidget(self.location_hint)

        # Show the *real* current location: a manual city must not leave the list on an old city
        cur_city = (self.settings.get("city", "Darica") or "").strip()
        selected_idx = 0
        for i, (display_name, api_name) in enumerate(TURKEY_PROVINCES, start=1):
            if api_name.lower() == cur_city.lower() or display_name.lower() == cur_city.lower():
                selected_idx = i
                break
        self.city_combo.setCurrentIndex(selected_idx)
        if selected_idx == 0 and cur_city:
            self.custom_city_input.setText(cur_city)

        self.city_combo.currentIndexChanged.connect(self._on_city_combo_changed)
        self.custom_city_input.textChanged.connect(self._on_manual_city_changed)
        self._refresh_location_hint()

        main_layout.addWidget(loc_group)

        # ----------------------------------------------------
        # 2. Bildirimler
        # ----------------------------------------------------
        notif_group = QGroupBox("🔔  Bildirimler")
        notif_layout = QVBoxLayout(notif_group)
        notif_layout.setSpacing(10)
        notif_layout.setContentsMargins(16, 12, 16, 14)

        self.cb_notif = QCheckBox("Vakit girdiğinde masaüstü bildirimi göster")
        self.cb_notif.setChecked(self.settings.get("notifications_enabled", True))
        notif_layout.addWidget(self.cb_notif)

        early_row = QHBoxLayout()
        early_row.setContentsMargins(0, 0, 0, 0)
        early_row.setSpacing(12)
        self.cb_early = QCheckBox("Vakit girmeden önce uyar:")
        self.cb_early.setChecked(self.settings.get("early_notification_enabled", True))
        self.spin_early = QSpinBox()
        self.spin_early.setRange(5, 60)
        self.spin_early.setSuffix(" dakika")
        self.spin_early.setValue(self.settings.get("early_notification_minutes", 15))
        self.spin_early.setFixedSize(140, FIELD_H)
        self.spin_early.setEnabled(self.cb_early.isChecked())
        self.cb_early.toggled.connect(self.spin_early.setEnabled)
        early_row.addWidget(self.cb_early, 0, Qt.AlignmentFlag.AlignVCenter)
        early_row.addWidget(self.spin_early, 0, Qt.AlignmentFlag.AlignVCenter)
        early_row.addStretch()
        notif_layout.addLayout(early_row)

        main_layout.addWidget(notif_group)

        # ----------------------------------------------------
        # 3. Sesli Uyarı & Ezan
        # ----------------------------------------------------
        sound_group = QGroupBox("🔊  Sesli Uyarı && Ezan")
        sound_layout = QVBoxLayout(sound_group)
        sound_layout.setSpacing(10)
        sound_layout.setContentsMargins(16, 12, 16, 14)

        self.cb_sound = QCheckBox("Sesli ezan / bildirim tonu çal")
        self.cb_sound.setChecked(self.settings.get("sound_enabled", True))
        sound_layout.addWidget(self.cb_sound)

        self.sound_type_combo = _make_combo()
        self.sound_type_combo.addItem("🕌  Vaktine Göre Makam Ezanları", "makam_ezan")
        self.sound_type_combo.addItem("🔔  Yumuşak Bildirim Çanı", "chime")
        self.sound_type_combo.addItem("📁  Özel Ses / Ezan Dosyası (MP3/WAV)", "custom")
        cur_sound_type = self.settings.get("sound_type", "makam_ezan")
        self.sound_type_combo.setCurrentIndex({"chime": 1, "custom": 2}.get(cur_sound_type, 0))
        sound_layout.addWidget(_row("Ses Türü:", self.sound_type_combo))

        # Mode specific row - a stack with one fixed height, so the dialog never jumps around
        self.mode_stack = QStackedWidget()
        self.mode_stack.setFixedHeight(FIELD_H)

        self.makam_select_combo = _make_combo()
        for p_key, p_name, _ in MAKAM_INFO:
            self.makam_select_combo.addItem(p_name, p_key)
        self.mode_stack.addWidget(_row("Makam:", self.makam_select_combo))

        chime_info = QLabel("Kısa ve yumuşak bir bildirim çanı çalınır.")
        chime_info.setObjectName("infoLabel")
        chime_info.setFixedHeight(FIELD_H)
        self.mode_stack.addWidget(_row("Ses:", chime_info))

        self.custom_sound_input = QLineEdit()
        self.custom_sound_input.setFixedHeight(FIELD_H)
        self.custom_sound_input.setText(self.settings.get("custom_sound_path", ""))
        self.custom_sound_input.setPlaceholderText("Özel ses dosyasının yolu...")
        self.browse_btn = QPushButton("Gözat...")
        self.browse_btn.setFixedWidth(96)
        self.browse_btn.clicked.connect(self._browse_sound)
        self.mode_stack.addWidget(_row("Dosya:", self.custom_sound_input, self.browse_btn))

        sound_layout.addWidget(self.mode_stack)

        # Preview row: always visible (makam, bell and custom file can all be tried out)
        self.test_sound_btn = QPushButton("▶   Dinle")
        self.test_sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.test_sound_btn.clicked.connect(self._test_sound)
        self.stop_sound_btn = QPushButton("■   Durdur")
        self.stop_sound_btn.setObjectName("stopBtn")
        self.stop_sound_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_sound_btn.clicked.connect(self._stop_sound)

        preview_box = QWidget()
        preview_lay = QHBoxLayout(preview_box)
        preview_lay.setContentsMargins(0, 0, 0, 0)
        preview_lay.setSpacing(8)
        preview_lay.addWidget(_field_label("Önizleme:"))
        preview_lay.addWidget(self.test_sound_btn, 1)
        preview_lay.addWidget(self.stop_sound_btn, 1)
        preview_box.setFixedHeight(FIELD_H)
        sound_layout.addWidget(preview_box)

        self.sound_type_combo.currentIndexChanged.connect(self._on_sound_type_changed)
        self._on_sound_type_changed(self.sound_type_combo.currentIndex())
        main_layout.addWidget(sound_group)

        # ----------------------------------------------------
        # 4. Sistem
        # ----------------------------------------------------
        sys_group = QGroupBox("🚀  Sistem")
        sys_layout = QVBoxLayout(sys_group)
        sys_layout.setContentsMargins(16, 12, 16, 14)

        self.cb_autostart = QCheckBox("Bilgisayar açıldığında otomatik başlat (KDE / Autostart)")
        self.cb_autostart.setChecked(self.settings.get("autostart", False))
        sys_layout.addWidget(self.cb_autostart)
        main_layout.addWidget(sys_group)

        # ----------------------------------------------------
        # Alt Butonlar
        # ----------------------------------------------------
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 6, 0, 0)
        btn_layout.setSpacing(10)
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.setFixedWidth(110)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Kaydet ve Uygula")
        save_btn.setObjectName("primaryBtn")
        save_btn.setFixedWidth(180)
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Location handling (list <-> manual field are mutually exclusive)
    # ------------------------------------------------------------------
    def _on_city_combo_changed(self, idx: int):
        if idx > 0 and self.custom_city_input.text():
            self.custom_city_input.blockSignals(True)
            self.custom_city_input.clear()
            self.custom_city_input.blockSignals(False)
        self._refresh_location_hint()

    def _on_manual_city_changed(self, text: str):
        if text.strip() and self.city_combo.currentIndex() != 0:
            self.city_combo.blockSignals(True)
            self.city_combo.setCurrentIndex(0)   # leave the old list city
            self.city_combo.blockSignals(False)
        self._refresh_location_hint()

    def _chosen_city(self) -> str:
        manual = self.custom_city_input.text().strip()
        if manual:
            return manual
        return self.city_combo.currentData() or (self.settings.get("city", "Darica") or "Darica")

    def _refresh_location_hint(self):
        manual = self.custom_city_input.text().strip()
        if manual:
            shown = manual
        elif self.city_combo.currentIndex() > 0:
            shown = self.city_combo.currentText()
        else:
            shown = self.settings.get("city", "Darica")
        self.location_hint.setText(f"Kullanılacak konum:  {shown}")

    # ------------------------------------------------------------------
    # Sound
    # ------------------------------------------------------------------
    def _on_sound_type_changed(self, idx):
        mode = self.sound_type_combo.currentData()
        self.mode_stack.setCurrentIndex({"makam_ezan": 0, "chime": 1, "custom": 2}.get(mode, 0))

    def _browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Ses Dosyası Seç", os.path.expanduser("~"), "Ses Dosyaları (*.mp3 *.wav *.m4a *.webm *.ogg)"
        )
        if file_path:
            self.custom_sound_input.setText(file_path)

    def _test_sound(self):
        mode = self.sound_type_combo.currentData()
        custom_path = self.custom_sound_input.text().strip()
        if mode == "custom" and not os.path.isfile(custom_path):
            self.custom_sound_input.setFocus()
            return

        keys = ("sound_enabled", "sound_type", "custom_sound_path")
        backup = {k: self.settings.settings.get(k) for k in keys}
        try:
            self.settings.settings["sound_enabled"] = True
            self.settings.settings["sound_type"] = mode
            self.settings.settings["custom_sound_path"] = custom_path
            if mode == "makam_ezan":
                self.sound_player.play_alert(self.makam_select_combo.currentData())
            else:
                # 'chime' -> the soft bell, 'custom' -> the chosen file
                self.sound_player.play_alert("chime")
        finally:
            self.settings.settings.update(backup)

    def _stop_sound(self):
        self.sound_player.stop_alert()

    def _on_cancel(self):
        self._stop_sound()
        self.reject()

    def _save_settings(self):
        self._stop_sound()
        self.settings.set("city", self._chosen_city())
        self.settings.set("notifications_enabled", self.cb_notif.isChecked())
        self.settings.set("early_notification_enabled", self.cb_early.isChecked())
        self.settings.set("early_notification_minutes", self.spin_early.value())
        self.settings.set("sound_enabled", self.cb_sound.isChecked())
        self.settings.set("sound_type", self.sound_type_combo.currentData())
        self.settings.set("custom_sound_path", self.custom_sound_input.text().strip())
        self.settings.set("autostart", self.cb_autostart.isChecked())

        self.accept()

    def closeEvent(self, event):
        self._stop_sound()
        super().closeEvent(event)

    def done(self, result):
        self._stop_sound()
        super().done(result)
