# Speech & Text Converter

A modern, responsive desktop application built with Python and Tkinter for Speech-to-Text conversion, Text-to-Speech synthesis, and multilingual translation across **English (India)**, **Hindi (हिन्दी)**, and **Gujarati (ગુજરાતી)**.

---

## 🌟 Key Features

- **🎙️ Speech to Text (Voice Recognition)**:
  - Non-blocking live microphone recording with animated pulse ring.
  - Two-step recording workflow: Click mic to start, click mic again to save, then click *"Convert & Translate Text"* to process.
  - Upload & transcribe audio files (`.wav`, `.mp3`, `.m4a`, `.aac`, `.flac`, `.ogg`).

- **🔊 Text to Speech (Voice Synthesis)**:
  - Natural speech synthesis powered by `gTTS` with offline `pyttsx3` fallback.
  - Non-blocking audio playback using `sounddevice` and `soundfile` with session-tracked cutoff to prevent audio overlapping.

- **🌐 Multilingual Translation**:
  - Seamless bidirectional translation between **English (India)**, **Hindi**, and **Gujarati**.
  - Multi-endpoint fallback system ensuring high reliability.

- **📄 Document Processing & Export**:
  - Import text directly from `.pdf` documents (`pypdf`).
  - Export styled `.pdf` documents with full Unicode Indic typography support (via Windows `Nirmala.ttc`).
  - Download options for Original PDF, Original Audio, Translation PDF, and Translation Audio.

- **🕒 History Tracking**:
  - Structured, searchable history table (Type, Language Pair, Date & Time, Preview).
  - Split-panel text inspection with one-click copy buttons for both original and translated text.

---

## 🛠️ Technology Stack

| Component | Library / Framework |
| :--- | :--- |
| **GUI Framework** | Tkinter & `ttk` |
| **Microphone Capture** | `sounddevice` + `numpy` (No PyAudio / C++ build tools required) |
| **Speech Recognition** | `SpeechRecognition` (Google Speech API) |
| **Text to Speech** | `gTTS` + `pyttsx3` |
| **Audio Playback** | `sounddevice` + `soundfile` |
| **PDF Processing** | `fpdf2` (Unicode Indic support) + `pypdf` |

---

## 📁 Project Structure

```
SpeechText/
├── app/
│   ├── core/
│   │   ├── audio_recorder.py   # Microphone recorder (sounddevice + numpy)
│   │   ├── document.py         # PDF reader & styled Unicode PDF exporter
│   │   ├── history_manager.py  # History persistence (JSON)
│   │   ├── languages.py        # Language configurations & flags
│   │   ├── speech_to_text.py   # Speech recognition engine
│   │   ├── text_to_speech.py   # Speech synthesis & playback
│   │   └── translator.py       # Multilingual translation engine
│   ├── gui/
│   │   ├── app_window.py       # Main window with top-right navigation
│   │   ├── dashboard.py        # 2-column workspace (STT & TTS modes)
│   │   └── history.py          # History table & split details inspector
│   └── utils/
│       └── constants.py        # Color palette, fonts & window dimensions
├── exports/                    # Generated PDF, MP3 & history logs
├── main.py                     # Application entry point
├── requirements.txt            # Project dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** (Tested on Python 3.10 – 3.14)
- **Windows OS** (with system font `Nirmala.ttc` for native Hindi and Gujarati rendering)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Avatars2/SpeechText.git
   cd SpeechText
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
