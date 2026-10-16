import os
import shutil
import subprocess
from typing import Optional
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, QTimer
# NOTE: PyQt6.QtMultimedia is imported lazily (see _ensure_*): loading FFmpeg and the GPU
# video drivers costs tens of MB of RAM that an idle tray app does not need.

# Traditional Ottoman / Turkish Prayer Makams
MAKAM_PRAYER_FILES = {
    "fajr": "sabah-ezani.mp3",     # Saba Makamı
    "dhuhr": "ogle-ezani.mp3",     # Uşşak Makamı
    "asr": "ikindi-ezani.mp3",      # Rast Makamı
    "maghrib": "aksam-ezani.mp3",   # Segah Makamı
    "isha": "yatsi-ezani.mp3"       # Hicaz Makamı
}

class SoundPlayer(QObject):
    # Emitted with True when any alert/adhan starts playing and False when it ends or is stopped
    playing_changed = pyqtSignal(bool)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings = settings_manager
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.default_chime = os.path.join(self.assets_dir, "chime.wav")

        # Created on first use, freed shortly after playback ends
        self.audio_output = None
        self.player = None
        self.sound_effect = None

        self._fallback_proc = None
        self._last_playing = False

        self._release_timer = QTimer(self)
        self._release_timer.setSingleShot(True)
        self._release_timer.setInterval(4000)
        self._release_timer.timeout.connect(self._release_backend)

    def _ensure_player(self):
        if self.player is None:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(0.85)
            self.player = QMediaPlayer()
            self.player.setAudioOutput(self.audio_output)
            self.player.playbackStateChanged.connect(self._on_backend_state)
        return self.player

    def _ensure_effect(self):
        if self.sound_effect is None:
            from PyQt6.QtMultimedia import QSoundEffect
            self.sound_effect = QSoundEffect()
            self.sound_effect.setVolume(0.85)
            self.sound_effect.playingChanged.connect(self._on_backend_state)
        return self.sound_effect

    def _on_backend_state(self, *_args):
        self._emit_state()
        if not self.is_playing():
            self._release_timer.start()

    def _release_backend(self):
        """Frees the multimedia objects once nothing is playing any more."""
        if self.is_playing():
            return
        if self.player is not None:
            try:
                self.player.playbackStateChanged.disconnect(self._on_backend_state)
            except Exception:
                pass
            self.player.setAudioOutput(None)
            self.player.deleteLater()
            self.player = None
        if self.audio_output is not None:
            self.audio_output.deleteLater()
            self.audio_output = None
        if self.sound_effect is not None:
            try:
                self.sound_effect.playingChanged.disconnect(self._on_backend_state)
            except Exception:
                pass
            self.sound_effect.deleteLater()
            self.sound_effect = None

    def _emit_state(self, *_args):
        playing = self.is_playing()
        if playing != self._last_playing:
            self._last_playing = playing
            self.playing_changed.emit(playing)

    def play_alert(self, prayer_key: Optional[str] = None):
        if not self.settings.get("sound_enabled", True):
            return

        self.stop_alert()

        sound_type = self.settings.get("sound_type", "makam_ezan")
        sound_file = self.default_chime

        if sound_type == "makam_ezan":
            # Select specific adhan by prayer makam
            p_key = (prayer_key or "dhuhr").lower()
            if p_key == "chime":
                # Early reminders / bell preview always use the soft bell, never an adhan
                sound_file = self.default_chime
            else:
                rel_file = MAKAM_PRAYER_FILES.get(p_key, "ogle-ezani.mp3")
                sound_file = os.path.join(self.assets_dir, rel_file)
            if not os.path.exists(sound_file):
                # Fallback to .webm or chime
                sound_file = self.default_chime
        elif sound_type == "custom":
            custom_path = self.settings.get("custom_sound_path", "")
            if custom_path and os.path.isfile(custom_path):
                sound_file = custom_path
            else:
                sound_file = os.path.join(self.assets_dir, "ogle-ezani.mp3")
        else: # 'chime'
            sound_file = self.default_chime

        if not os.path.exists(sound_file):
            return

        # Play using QSoundEffect for low-latency WAV, or QMediaPlayer for MP3/Audio
        try:
            self._release_timer.stop()
            if sound_file.lower().endswith(".wav"):
                effect = self._ensure_effect()
                effect.setSource(QUrl.fromLocalFile(sound_file))
                effect.play()
            else:
                player = self._ensure_player()
                player.setSource(QUrl.fromLocalFile(sound_file))
                player.play()
        except Exception as e:
            # Fallback to system audio player commands (PipeWire / PulseAudio / ALSA)
            for cmd in ["pw-play", "paplay", "aplay"]:
                if shutil.which(cmd):
                    try:
                        self._fallback_proc = subprocess.Popen([cmd, sound_file])
                        self._emit_state()
                        break
                    except Exception:
                        pass

    def stop_alert(self):
        if self.sound_effect is not None:
            try:
                self.sound_effect.stop()
            except Exception:
                pass
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
        if self._fallback_proc:
            try:
                self._fallback_proc.terminate()
            except Exception:
                pass
            self._fallback_proc = None
        self._emit_state()
        self._release_timer.start()

    def is_playing(self) -> bool:
        fallback_running = self._fallback_proc is not None and self._fallback_proc.poll() is None
        player_playing = False
        if self.player is not None:
            from PyQt6.QtMultimedia import QMediaPlayer
            player_playing = self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        effect_playing = self.sound_effect is not None and self.sound_effect.isPlaying()
        return player_playing or effect_playing or fallback_running
