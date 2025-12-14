# perfect for listening to english and testing on spanish and hindi
import os, queue, json, sqlite3, time, threading
import sounddevice as sd
import vosk

# Paths for different language models
MODEL_PATHS = {
    "en": "vosk-model-small-en-us-0.15",
    "es": "vosk-model-small-es-0.42",
    "hi": "vosk-model-small-hi-0.22"
}

# Choose language ("en", "es", "hi")
LANGUAGE = "en"   # change to "es" or "hi" as needed

if LANGUAGE not in MODEL_PATHS:
    raise ValueError(f"Unsupported language {LANGUAGE}, choose from {list(MODEL_PATHS.keys())}")

MODEL_PATH = MODEL_PATHS[LANGUAGE]

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Download from https://alphacephei.com/vosk/models")

# Load Vosk model
model = vosk.Model(MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, 16000)

# Database setup
DB_FILE = "transcriptions.db"
q = queue.Queue()

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

def save_transcript(text, lang):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO transcripts (timestamp, language, text) VALUES (?, ?, ?)", (ts, lang, text))
    conn.commit()

def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status, flush=True)
    q.put(bytes(indata))

def transcribe_loop():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=audio_callback):
        print(f"🎤 Listening in {LANGUAGE.upper()}... (transcripts saved to DB)")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text.strip():
                    print("✅", text)
                    save_transcript(text, LANGUAGE)
            # (Optional: handle partial results)

# Run transcription in a background thread
def start_transcriber():
    t = threading.Thread(target=transcribe_loop, daemon=True)
    t.start()
