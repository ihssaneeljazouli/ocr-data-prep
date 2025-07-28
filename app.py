import os
import shutil
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

# --- CONFIGURATION ---
DB_PATH = 'words.db'
IMG_FOLDER = 'static/words/words_output'

# --- INITIALISATION FLASK ---
app = Flask(__name__)
app.secret_key = 'supersecret'  # nécessaire pour la session

# --- CRÉATION BASE SI ELLE N'EXISTE PAS ---
def init_db():
    os.makedirs(IMG_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            text TEXT,
            status TEXT CHECK(status IN ('pending', 'processing')) DEFAULT 'pending',
            annotator TEXT
        )
    """)

    for filename in sorted(os.listdir(IMG_FOLDER)):
        if filename.endswith('.png') or filename.endswith('.jpg'):
            full_path = os.path.join(IMG_FOLDER, filename)
            cur.execute("INSERT OR IGNORE INTO images (path, status) VALUES (?, 'pending')", (full_path,))

    conn.commit()
    conn.close()

# --- COMPTE IMAGES RESTANTES ---
def get_remaining_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status = 'pending'")
    count = cur.fetchone()[0]
    conn.close()
    return count

# --- PAGE D'ACCUEIL ---
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        annotator = request.form.get("annotator", "").strip()
        session['annotator'] = annotator or "anonyme"
        return redirect(url_for("annotate"))

    remaining = get_remaining_count()
    return render_template("home.html", remaining=remaining)

# --- PAGE D'ANNOTATION ---
@app.route("/annotate", methods=["GET", "POST"])
def annotate():
    annotator = session.get("annotator", "anonyme")

    if request.method == "POST":
        image_id = int(request.form["image_id"])
        word_text = request.form["text"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            UPDATE images
            SET text = ?, status = 'processing', annotator = ?
            WHERE id = ?
        """, (word_text, annotator, image_id))
        conn.commit()
        conn.close()

        return redirect(url_for("annotate"))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, path FROM images WHERE status = 'pending' LIMIT 1")
    row = cur.fetchone()
    conn.close()

    if row:
        image_id, image_path = row
        return render_template("annotate.html", image_id=image_id, image_path=image_path, annotator=annotator)
    else:
        return "<h2>🎉 Toutes les images ont été annotées !</h2>"

# --- EXPORT FINAL ---
@app.route("/export")
def export():
    EXPORT_IMG_DIR = 'dataset/images'
    EXPORT_LABEL_DIR = 'dataset/labels'
    os.makedirs(EXPORT_IMG_DIR, exist_ok=True)
    os.makedirs(EXPORT_LABEL_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT path, text FROM images WHERE text IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    for path, label in rows:
        filename = os.path.basename(path)
        new_img_path = os.path.join(EXPORT_IMG_DIR, filename)
        new_txt_path = os.path.join(EXPORT_LABEL_DIR, filename.rsplit('.', 1)[0] + '.txt')

        shutil.copy(path, new_img_path)
        with open(new_txt_path, 'w', encoding='utf-8') as f:
            f.write(label.strip())

    return f"Export de {len(rows)} mots effectué avec succès."

# --- POINT D'ENTRÉE ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)