import os
import json
import sys

DEFAULT_SETTINGS = {
    "country": "Turkey",
    "city": "Darica",
    "district": "",
    "method": 13,  # Diyanet İşleri Başkanlığı
    "notifications_enabled": True,
    "early_notification_enabled": True,
    "early_notification_minutes": 15,
    "sound_enabled": True,
    "sound_type": "makam_ezan",  # 'makam_ezan', 'chime', or 'custom'
    "custom_sound_path": "",
    "autostart": False,
    "theme": "dark",
    "window_pos": None,       # [x, y] last position of the popup, None = default (next to the clock)
    "first_run_done": False   # popup is shown once automatically on the very first launch
}

class SettingsManager:
    def __init__(self):
        self.config_dir = os.path.expanduser("~/.config/ezan-vakti")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.autostart_dir = os.path.expanduser("~/.config/autostart")
        self.autostart_file = os.path.join(self.autostart_dir, "ezan-vakti.desktop")
        self.settings = DEFAULT_SETTINGS.copy()
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.settings.update(data)
            except Exception as e:
                print(f"Ayar yükleme hatası: {e}")
        else:
            self.save()

    def save(self):
        os.makedirs(self.config_dir, exist_ok=True)
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ayar kaydetme hatası: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()
        if key == "autostart":
            self.update_autostart(value)

    def set_window_pos(self, x, y):
        """Remembers where the user dragged the popup (None, None resets to default)."""
        self.settings["window_pos"] = None if x is None else [int(x), int(y)]
        self.save()

    def update_autostart(self, enable: bool):
        os.makedirs(self.autostart_dir, exist_ok=True)
        if enable:
            exec_path = os.path.abspath(sys.argv[0])
            desktop_content = f"""[Desktop Entry]
Type=Application
Version=1.0
Name=Ezan Vakti
Comment=Linux KDE Sistem Tepsisi Ezan Vakti Uygulaması
Exec={sys.executable} "{exec_path}"
Icon=appointment-soon
Terminal=false
Categories=Utility;Clock;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
            try:
                with open(self.autostart_file, "w", encoding="utf-8") as f:
                    f.write(desktop_content)
                os.chmod(self.autostart_file, 0o755)
            except Exception as e:
                print(f"Otomatik başlatma oluşturulamadı: {e}")
        else:
            if os.path.exists(self.autostart_file):
                try:
                    os.remove(self.autostart_file)
                except Exception as e:
                    print(f"Otomatik başlatma silinemedi: {e}")
