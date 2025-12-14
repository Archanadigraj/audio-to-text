# the same audio chunk to be tested against English, Spanish, and Hindi models, and then only store results if that model produces text.
import os, queue, json, sqlite3, time, threading
import sounddevice as sd
import vosk

# ======================
# Language Models Setup
# ======================
MODEL_PATHS = {
    "en": "vosk-model-small-en-us-0.15",
    "es": "vosk-model-small-es-0.42",
    "hi": "vosk-model-small-hi-0.22"
}

DB_FILE = "transcriptions.db"
q = queue.Queue()

# ======================
# Load All Models
# ======================
recognizers = {}
for lang, path in MODEL_PATHS.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found: {path}. Download from https://alphacephei.com/vosk/models")
    model = vosk.Model(path)
    recognizers[lang] = vosk.KaldiRecognizer(model, 16000)

# ======================
# Database
# ======================
def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            language TEXT,
            text TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

# def save_transcript(text, lang):
#     ts = time.strftime("%Y-%m-%d %H:%M:%S")
#     conn.execute("INSERT INTO transcripts (timestamp, language, text) VALUES (?, ?, ?)", (ts, lang, text))
#     conn.commit()

def save_transcript(text, lang):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO transcripts (timestamp, language, text) VALUES (?, ?, ?)", (ts, lang, text))
    conn.commit()
# ======================
# Audio Callback
# ======================
def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status, flush=True)
    q.put(bytes(indata))

# ======================
# Main Transcribe Loop
# ======================
def transcribe_loop():
    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                           dtype="int16", channels=1,
                           callback=audio_callback):
        print("🎤 Listening... (checking EN, ES, HI)")

        while True:
            data = q.get()
            for lang, rec in recognizers.items():
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "").strip()
                    if text:
                        print(f"[{lang.upper()}] {text}")
                        save_transcript(text, lang)

# ======================
# Start Background Thread
# ======================
def start_transcriber():
    t = threading.Thread(target=transcribe_loop, daemon=True)
    t.start()
