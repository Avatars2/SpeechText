import io
import os
import wave
from typing import Optional

import numpy as np
import soundfile as sf
import speech_recognition as sr

from app.core.languages import get_language


class SpeechToTextEngine:
    """
    Handles speech recognition from in-memory audio buffers and file inputs.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()
        # Improve recognition accuracy
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def transcribe_wav_bytes(self, wav_bytes: bytes, lang_code: str = "en") -> str:
        """
        Transcribe audio from raw WAV bytes (e.g., from microphone).
        """
        if not wav_bytes:
            raise ValueError("No audio recorded. Please record some speech first.")

        audio_file = io.BytesIO(wav_bytes)
        return self._recognize_stream(audio_file, lang_code)

    def transcribe_file(self, file_path: str, lang_code: str = "en") -> str:
        """
        Transcribe an audio file from disk (.wav, .mp3, .flac, .ogg).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Check if native WAV
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".wav":
            try:
                with sr.AudioFile(file_path) as source:
                    audio_data = self.recognizer.record(source)
                    return self._recognize_audio_data(audio_data, lang_code)
            except Exception:
                # If standard wave reader fails, fall back to soundfile conversion
                pass

        # Convert using soundfile to standard 16-bit PCM WAV in memory
        try:
            data, samplerate = sf.read(file_path, dtype="int16")
            # If multi-channel, convert to mono
            if data.ndim > 1:
                data = data.mean(axis=1).astype(np.int16)

            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(samplerate)
                wf.writeframes(data.tobytes())
            wav_buf.seek(0)

            return self._recognize_stream(wav_buf, lang_code)
        except Exception as e:
            raise RuntimeError(f"Failed to read audio file '{os.path.basename(file_path)}': {e}")

    def _recognize_stream(self, stream: io.BytesIO, lang_code: str) -> str:
        """Extract audio from BytesIO stream and transcribe."""
        stream.seek(0)
        with sr.AudioFile(stream) as source:
            audio_data = self.recognizer.record(source)
            return self._recognize_audio_data(audio_data, lang_code)

    def _recognize_audio_data(self, audio_data: sr.AudioData, lang_code: str) -> str:
        """Run speech recognition with Google Speech API using the requested language."""
        lang = get_language(lang_code)
        try:
            text = self.recognizer.recognize_google(audio_data, language=lang.stt_code)
            return text.strip()
        except sr.UnknownValueError:
            raise RuntimeError(
                f"Could not understand the audio in {lang.display_name}. "
                "Please speak clearly or verify the language selection."
            )
        except sr.RequestError as e:
            raise ConnectionError(
                f"Network error while connecting to speech service: {e}. "
                "Please verify your internet connection."
            )

