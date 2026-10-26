import io
import queue
import threading
import time
import wave
from typing import Optional

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """
    Non-blocking microphone recorder.
    Records 16-bit mono PCM audio suitable for speech recognition.
    """

    SAMPLE_RATE = 16000  # 16 kHz is standard for Google Speech API
    CHANNELS = 1         # Mono audio

    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self._is_recording = False
        self._stream: Optional[sd.InputStream] = None
        self._queue: queue.Queue = queue.Queue()
        self._chunks: list[np.ndarray] = []
        self._start_time: float = 0.0
        self._lock = threading.Lock()

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._is_recording

    @property
    def elapsed_seconds(self) -> float:
        if not self._is_recording:
            return 0.0
        return max(0.0, time.time() - self._start_time)

    def start_recording(self) -> None:
        """Begin audio capture from default input device."""
        with self._lock:
            if self._is_recording:
                return

            self._chunks.clear()
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break

            self._is_recording = True
            self._start_time = time.time()

            def _callback(indata, frames, time_info, status):
                if status:
                    pass
                if self._is_recording:
                    self._queue.put(indata.copy())

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.CHANNELS,
                dtype="int16",
                callback=_callback,
            )
            self._stream.start()

    def stop_recording(self) -> bytes:
        """
        Stop audio capture and return raw WAV bytes.
        """
        with self._lock:
            if not self._is_recording:
                return b""

            self._is_recording = False

            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

            # Collect remaining chunks from the queue
            while not self._queue.empty():
                try:
                    self._chunks.append(self._queue.get_nowait())
                except queue.Empty:
                    break

        if not self._chunks:
            return b""

        audio_data = np.concatenate(self._chunks, axis=0)
        return self._to_wav_bytes(audio_data, self.sample_rate)

    @staticmethod
    def _to_wav_bytes(audio_data: np.ndarray, sample_rate: int) -> bytes:
        """Pack 16-bit PCM numpy array into a valid in-memory WAV file."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        return buffer.getvalue()

