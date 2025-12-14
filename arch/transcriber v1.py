# perfect for listening to english
import os, queue, json, sqlite3, time, threading
import sounddevice as sd
import vosk

MODEL_PATH = "vosk-model-small-en-us-0.15"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Download from: https://alphacephei.com/vosk/models")

model = vosk.Model(MODEL_PATH)
recognizer = vosk.KaldiRecognizer(model, 16000)

DB_FILE = "transcriptions.db"
q = queue.Queue()

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            text TEXT
        )
    """)
    conn.commit()
    return conn

conn = init_db()

def save_transcript(text):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO transcripts (timestamp, text) VALUES (?, ?)", (ts, text))
    conn.commit()

def audio_callback(indata, frames, time, status):
    if status:
        print("Audio status:", status, flush=True)
    q.put(bytes(indata))

def transcribe_loop():
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype="int16",
                           channels=1, callback=audio_callback):
        print("🎤 Listening... (transcripts visible on dashboard)")
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "")
                if text.strip():
                    print("✅", text)
                    save_transcript(text)
            # (Optional: handle partials)

# Run transcription in a background thread
def start_transcriber():
    t = threading.Thread(target=transcribe_loop, daemon=True)
    t.start()
