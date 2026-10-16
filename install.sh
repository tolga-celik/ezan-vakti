#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPIMAGE="$SCRIPT_DIR/EzanVakti-x86_64.AppImage"

if [ ! -f "$APPIMAGE" ]; then
    echo "Hata: EzanVakti-x86_64.AppImage bulunamadı! Önce ./build_appimage.sh çalıştırın."
    exit 1
fi

echo "=========================================="
echo "🕌 Ezan Vakti - KDE Kurulumu"
echo "=========================================="

# 1. ~/.local/bin dizinine kopyala
mkdir -p "$HOME/.local/bin"
killall -9 ezan-vakti 2>/dev/null || true
pkill -9 -f "\.local/bin/ezan-vakti" 2>/dev/null || true
sleep 0.5
rm -f "$HOME/.local/bin/ezan-vakti"
cp "$APPIMAGE" "$HOME/.local/bin/ezan-vakti"
chmod +x "$HOME/.local/bin/ezan-vakti"

# 2. İkonları kur
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
cp "$SCRIPT_DIR/assets/icon.png" "$HOME/.local/share/icons/hicolor/256x256/apps/ezan-vakti.png"
cp "$SCRIPT_DIR/assets/icon.svg" "$HOME/.local/share/icons/hicolor/scalable/apps/ezan-vakti.svg"

# 3. Masaüstü dosyasını oluştur
mkdir -p "$HOME/.local/share/applications"
cat << EOF > "$HOME/.local/share/applications/ezan-vakti.desktop"
[Desktop Entry]
Type=Application
Version=1.0
Name=Ezan Vakti
GenericName=Namaz Vakitleri
Comment=Linux KDE Masaüstü Ezan Vakti ve Bildirim Uygulaması
Exec=$HOME/.local/bin/ezan-vakti
Icon=ezan-vakti
Terminal=false
Categories=Utility;Clock;KDE;Qt;
Keywords=ezan;vakit;namaz;prayer;athan;diyanet;islam;
StartupNotify=false
X-GNOME-Autostart-enabled=true
X-KDE-autostart-after=panel
EOF

# 4. Masaüstü veritabanını güncelle
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi

echo "[+] Kurulum tamamlandı!"
echo "[+] Uygulamayı KDE Başlatıcısından (Kickoff) veya terminalden 'ezan-vakti' yazarak başlatabilirsiniz."
echo "=========================================="
