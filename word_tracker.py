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
        if is_known_word(word):
            # Incremental learning: update usage count
            update_word_usage(word)
        else:
            store_unknown_word(word, language)
            unknown_words.append(word)

    return unknown_words


def update_word_usage(word):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE vocabulary
        SET usage_count = usage_count + 1,
            last_used = ?
        WHERE word = ?
    """, (timestamp, word))

    conn.commit()
    
    
def add_word_to_vocabulary(word, language, meaning):
    """
    Move a validated word into the vocabulary table
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        INSERT OR IGNORE INTO vocabulary
        (word, language, meaning, usage_count, last_used)
        VALUES (?, ?, ?, 1, ?)
    """, (word, language, meaning, timestamp))

    conn.commit()


def remove_unvalidated_word(word):
    """
    Remove word from temporary unvalidated list
    """
    conn.execute(
        "DELETE FROM unvalidated_words WHERE word = ?",
        (word,)
    )
    conn.commit()




