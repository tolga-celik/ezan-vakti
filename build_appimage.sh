#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🕌 Ezan Vakti - AppImage Derleme Başlatılıyor"
echo "=========================================="

# 1. Sanal ortamı kontrol et
if [ ! -d "build_venv" ]; then
    echo "[-] Python derleme ortamı hazırlanıyor..."
    python3 -m venv --system-site-packages build_venv
    ./build_venv/bin/pip install pyinstaller
fi

# 2. İkonları üret (SVG -> PNG)
echo "[+] Uygulama ikonları doğrulanıyor..."
python3 -c "
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QColor
from PyQt6.QtSvg import QSvgRenderer

app = QApplication(sys.argv)
renderer = QSvgRenderer('$SCRIPT_DIR/assets/icon.svg')
img = QImage(256, 256, QImage.Format.Format_ARGB32)
img.fill(QColor(0, 0, 0, 0))
p = QPainter(img)
renderer.render(p)
p.end()
img.save('$SCRIPT_DIR/assets/icon.png')
"

# 3. PyInstaller ile ikili derleme
echo "[+] PyInstaller ile dosyalar derleniyor..."
./build_venv/bin/pyinstaller \
    --noconfirm \
    --onedir \
    --windowed \
    --name ezan-vakti \
    --add-data "assets:assets" \
    --hidden-import "PyQt6.QtCore" \
    --hidden-import "PyQt6.QtGui" \
    --hidden-import "PyQt6.QtWidgets" \
    --hidden-import "PyQt6.QtSvg" \
    --hidden-import "PyQt6.QtMultimedia" \
    --hidden-import "sqlite3" \
    main.py

# 4. AppDir yapısını oluştur
echo "[+] AppDir klasör yapısı kuruluyor..."
rm -rf AppDir
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps
mkdir -p AppDir/usr/share/icons/hicolor/scalable/apps

# Dosyaları kopyala
cp -r dist/ezan-vakti/* AppDir/usr/bin/
cp assets/ezan-vakti.desktop AppDir/usr/share/applications/
cp assets/ezan-vakti.desktop AppDir/
cp assets/icon.png AppDir/usr/share/icons/hicolor/256x256/apps/ezan-vakti.png
cp assets/icon.png AppDir/ezan-vakti.png
cp assets/icon.svg AppDir/usr/share/icons/hicolor/scalable/apps/ezan-vakti.svg

# AppRun oluştur
cat << 'EOF' > AppDir/AppRun
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/bin:${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export QT_PLUGIN_PATH="${HERE}/usr/bin/PyQt6/Qt6/plugins:${QT_PLUGIN_PATH}"
export QML2_IMPORT_PATH="${HERE}/usr/bin/PyQt6/Qt6/qml:${QML2_IMPORT_PATH}"
exec "${HERE}/usr/bin/ezan-vakti" "$@"
EOF
chmod +x AppDir/AppRun

# 5. AppImage Paketleme
echo "[+] AppImage paketi oluşturuluyor..."
if [ ! -f "packaging/appimagetool" ]; then
    mkdir -p packaging
    curl -L -o packaging/appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x packaging/appimagetool
fi

ARCH=x86_64 ./packaging/appimagetool --appimage-extract-and-run AppDir EzanVakti-x86_64.AppImage

chmod +x EzanVakti-x86_64.AppImage
echo "=========================================="
echo "✅ BAŞARILI! AppImage oluşturuldu: EzanVakti-x86_64.AppImage"
echo "=========================================="
