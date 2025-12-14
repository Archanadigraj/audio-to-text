import os
import queue
import json
import sqlite3
import time
import threading
import wave
import re

import sounddevice as sd
import vosk

# -----------------------------
# Model paths (OFFLINE)
# -----------------------------
MODEL_PATHS = {
    "en": "vosk-model-small-en-us-0.15",
    "es": "vosk-model-small-es-0.42",
    "hi": "vosk-model-small-hi-0.22"
}

# -----------------------------
# Load models & recognizers
# -----------------------------
recognizers = {}

for lang, path in MODEL_PATHS.items():
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model for '{lang}' not found.\n"
            f"Download from: https://alphacephei.com/vosk/models"
        )
    model = vosk.Model(path)
    recognizers[lang] = vosk.KaldiRecognizer(model, 16000)

# -----------------------------
# Database setup
# -----------------------------
DB_FILE = "transcriptions.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            language TEXT,
            text TEXT,
            audio_file TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# -----------------------------
# Audio storage
# -----------------------------
AUDIO_DIR = "audio_clips"
os.makedirs(AUDIO_DIR, exist_ok=True)

# -----------------------------
# Queue for audio stream
# -----------------------------
audio_queue = queue.Queue()

# -----------------------------
# Utility: Clean text
# -----------------------------
def clean_text(text: str) -> str:
    """
    Clean transcription text:
    - lowercase
    - remove symbols
    - keep English + Hindi characters
    """
    text = text.lower()
    text = re.sub(r"[^a-zA-Z\u0900-\u097F ]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# -----------------------------
# Save transcript to DB
# -----------------------------
def save_transcript(text, lang, audio_path):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO transcripts (timestamp, language, text, audio_file) VALUES (?, ?, ?, ?)",
        (timestamp, lang, text, audio_path)
    )
    conn.commit()

# -----------------------------
# Save audio chunk
# -----------------------------
def save_audio_chunk(raw_audio, lang):
    ts = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{lang}_{ts}.wav"
    filepath = os.path.join(AUDIO_DIR, filename)

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(raw_audio)

    return filepath

# -----------------------------
# Audio callback
# -----------------------------
def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio status:", status)
    audio_queue.put(bytes(indata))

# -----------------------------
# Transcription loop (OFFLINE)
# -----------------------------
def transcribe_loop():
    with sd.RawInputStream(
        samplerate=16000,
        blocksize=8000,
        dtype="int16",
        channels=1,
        callback=audio_callback
    ):
        print("🎤 Listening (offline): English | Hindi | Spanish")

        while True:
            data = audio_queue.get()

            # Silence / noise guard
            if len(data) < 4000:
                continue

            # Try each language recognizer
            for lang, recognizer in recognizers.items():
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    raw_text = result.get("text", "")
                    text = clean_text(raw_text)

                    if not text:
                        break

                    audio_path = save_audio_chunk(data, lang)
                    save_transcript(text, lang, audio_path)

                    print(f"[{lang.upper()}] {text}️ 🎵 {audio_path}")

                    # IMPORTANT: stop after first success
                    break

# -----------------------------
# Start transcriber thread
# -----------------------------
def start_transcriber():
    thread = threading.Thread(
        target=transcribe_loop,
        daemon=True
    )
    thread.start()
