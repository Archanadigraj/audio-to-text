import sqlite3
import time

VOCAB_DB = "vocabulary.db"

def init_vocab_db():
    conn = sqlite3.connect(VOCAB_DB, check_same_thread=False)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            language TEXT,
            meaning TEXT,
            usage_count INTEGER DEFAULT 1,
            last_used TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS unvalidated_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT,
            language TEXT,
            detected_at TEXT,
            UNIQUE(word, language)
        )
    """)

    conn.commit()
    return conn

conn = init_vocab_db()

def is_known_word(word):
    cursor = conn.execute(
        "SELECT 1 FROM vocabulary WHERE word = ?",
        (word,)
    )
    return cursor.fetchone() is not None


def store_unknown_word(word, language):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn.execute(
            "INSERT INTO unvalidated_words (word, language, detected_at) VALUES (?, ?, ?)",
            (word, language, timestamp)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # word already exists → ignore
        pass


def track_unknown_words(text, language):
    words = text.split()

    unknown_words = []

    for word in words:
        if not is_known_word(word):
            store_unknown_word(word, language)
            unknown_words.append(word)

    return unknown_words
