from flask import Flask, render_template, jsonify, Response
import sqlite3
import csv
import io
import transcriber

app = Flask(__name__)

# Start background transcriber
transcriber.start_transcriber()

DB_FILE = "transcriptions.db"

def get_transcripts(limit=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    query = "SELECT timestamp, text FROM transcripts ORDER BY id DESC"
    if limit:
        query += f" LIMIT {limit}"
    cursor.execute(query)
    rows = cursor.fetchall()
    return [{"timestamp": r[0], "text": r[1]} for r in rows]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    return jsonify(get_transcripts(limit=20))

# 🔹 Download TXT
@app.route("/download/txt")
def download_txt():
    transcripts = get_transcripts()
    output = io.StringIO()
    for t in transcripts:
        output.write(f"{t['timestamp']} - {t['text']}\n")
    return Response(output.getvalue(),
                    mimetype="text/plain",
                    headers={"Content-Disposition": "attachment;filename=transcripts.txt"})

# 🔹 Download CSV
@app.route("/download/csv")
def download_csv():
    transcripts = get_transcripts()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Transcript"])
    for t in transcripts:
        writer.writerow([t['timestamp'], t['text']])
    return Response(output.getvalue(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=transcripts.csv"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
