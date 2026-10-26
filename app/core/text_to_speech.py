from datetime import datetime
import os
import tempfile
import threading
import time
from typing import Callable, Optional

from gtts import gTTS
import numpy as np
import pyttsx3
import sounddevice as sd
import soundfile as sf

from app.core.languages import get_language


class TextToSpeechEngine:
    def __init__(self):
        self._is_playing = False
        self._lock = threading.Lock()
        self._session_id = 0
        self._play_thread: Optional[threading.Thread] = None
        self._current_temp_file: Optional[str] = None

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    def save_speech_file(self, text: str, lang_code: str, output_path: str) -> str:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Text cannot be empty.")

        lang = get_language(lang_code)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        try:
            # Primary: gTTS for natural multilingual voice
            tts = gTTS(text=clean_text, lang=lang.tts_code, slow=False)
            tts.save(output_path)
            return output_path
        except Exception as gtts_err:
            # Fallback to offline pyttsx3 if English and network error
            if lang_code == "en":
                try:
                    engine = pyttsx3.init()
                    engine.save_to_file(clean_text, output_path)
                    engine.runAndWait()
                    return output_path
                except Exception as pyttsx_err:
                    raise RuntimeError(f"Failed to generate speech: {gtts_err} | Offline engine: {pyttsx_err}")
            else:
                raise RuntimeError(
                    f"Speech generation for {lang.display_name} requires an active internet connection: {gtts_err}"
                )

    def play_speech(
        self,
        text: str,
        lang_code: str,
        on_started: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
    ) -> None:
        # Stop any existing playback and allocate new session
        self.stop_speech()

        with self._lock:
            self._session_id += 1
            current_session = self._session_id
            self._is_playing = True

        def _worker():
            temp_path = None
            try:
                # 1. Synthesize audio to temporary mp3
                fd, temp_path = tempfile.mkstemp(suffix=".mp3", prefix="speechtext_")
                os.close(fd)
                self._current_temp_file = temp_path

                self.save_speech_file(text, lang_code, temp_path)

                # Check if playback was cancelled while synthesizing
                with self._lock:
                    if self._session_id != current_session or not self._is_playing:
                        return

                if on_started:
                    on_started()

                # 2. Read audio data with soundfile and play via sounddevice
                data, samplerate = sf.read(temp_path, dtype="float32")

                with self._lock:
                    if self._session_id != current_session or not self._is_playing:
                        return

                sd.stop()
                sd.play(data, samplerate)

                # Wait for playback completion while checking cancellation
                total_duration = len(data) / float(samplerate)
                start_time = time.time()

                while time.time() - start_time < total_duration:
                    with self._lock:
                        if self._session_id != current_session or not self._is_playing:
                            sd.stop()
                            return
                    time.sleep(0.05)

                sd.stop()

            except Exception as e:
                print(f"[TTS Player Notice]: {e}")
            finally:
                # Cleanup temporary file safely
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

                # Only notify finished if this session was not preempted
                with self._lock:
                    if self._session_id == current_session:
                        self._is_playing = False
                        if on_finished:
                            on_finished()

        self._play_thread = threading.Thread(target=_worker, daemon=True)
        self._play_thread.start()

    def stop_speech(self) -> None:
        with self._lock:
            self._session_id += 1
            self._is_playing = False

        try:
            sd.stop()
        except Exception:
            pass
