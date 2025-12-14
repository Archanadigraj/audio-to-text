import socket

def is_internet_available():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=2)
        return True
    except OSError:
        return False


import requests

def validate_word_online(word, target_lang="en"):
    """
    Validate word using Google Translate public API
    """
    url = "https://translate.googleapis.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": "auto",
        "tl": target_lang,
        "dt": "t",
        "q": word
    }

    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()
    translated_text = data[0][0][0]
    detected_lang = data[2]

    return {
        "word": word,
        "language": detected_lang,
        "meaning": translated_text
    }


def add_word_to_vocabulary(word, language, meaning):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        INSERT OR IGNORE INTO vocabulary
        (word, language, meaning, usage_count, last_used)
        VALUES (?, ?, ?, 1, ?)
    """, (word, language, meaning, timestamp))

    conn.commit()


def remove_unvalidated_word(word):
    conn.execute(
        "DELETE FROM unvalidated_words WHERE word = ?",
        (word,)
    )
    conn.commit()


from word_tracker import conn, add_word_to_vocabulary, remove_unvalidated_word
from validator import is_internet_available, validate_word_online

def process_unvalidated_words():
    if not is_internet_available():
        print("🌐 Internet not available. Skipping validation.")
        return

    cursor = conn.execute(
        "SELECT word, language FROM unvalidated_words"
    )

    for word, lang in cursor.fetchall():
        try:
            result = validate_word_online(word)

            add_word_to_vocabulary(
                word=result["word"],
                language=result["language"],
                meaning=result["meaning"]
            )

            remove_unvalidated_word(word)

            print(f"✅ Learned word: {word} → {result['meaning']}")

        except Exception as e:
            print(f"❌ Failed to validate {word}: {e}")
