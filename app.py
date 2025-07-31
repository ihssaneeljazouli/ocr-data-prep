import os
import shutil
import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, session

# --- CONFIGURATION ---
DB_PATH = 'words.db'
IMG_FOLDER = 'static/words/words_output'

# --- INITIALISATION FLASK ---
app = Flask(__name__)
app.secret_key = 'supersecret'

# --- CRÉATION BASE DE DONNÉES ---
def init_db():
    os.makedirs(IMG_FOLDER, exist_ok=True)

    # Vérifie si la base de données existe déjà
    first_time = not os.path.exists(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if first_time:
        # Crée la table si elle n’existe pas déjà
        cur.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                text TEXT,
                status TEXT CHECK(status IN ('pending', 'processing', 'annotated')) DEFAULT 'pending',
                annotator TEXT,
                assigned_at TIMESTAMP
            )
        """)

        for filename in sorted(os.listdir(IMG_FOLDER)):
            if filename.endswith('.png') or filename.endswith('.jpg'):
                full_path = os.path.join(IMG_FOLDER, filename)
                cur.execute("INSERT OR IGNORE INTO images (path, status) VALUES (?, 'pending')", (full_path,))

        conn.commit()

    conn.close()

# --- STATISTIQUES ---
def get_not_annotated_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status != 'annotated'")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_total_annotated_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status = 'annotated'")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_total_image_count():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images")
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_user_processing_count(annotator):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status = 'processing' AND annotator = ?", (annotator,))
    count = cur.fetchone()[0]
    conn.close()
    return count

def get_user_remaining_annotations(annotator):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status = 'processing' AND annotator = ? AND text IS NULL", (annotator,))
    count = cur.fetchone()[0]
    conn.close()
    return count

# --- REMETTRE EN PENDING APRÈS 3H ---
def reset_expired_assignments():
    now = datetime.datetime.now()
    expired_time = now - datetime.timedelta(hours=3)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE images
        SET status = 'pending', annotator = NULL, assigned_at = NULL
        WHERE status = 'processing' AND assigned_at IS NOT NULL AND assigned_at < ?
    """, (expired_time,))
    conn.commit()
    conn.close()

# --- ASSIGNATION D'IMAGES À UN UTILISATEUR ---
def assign_images_to_user(annotator_name, batch_size=50):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM images WHERE status = 'processing' AND annotator = ?", (annotator_name,))
    count = cur.fetchone()[0]
    if count == 0:
        now = datetime.datetime.now()
        cur.execute("""
            UPDATE images
            SET status = 'processing', annotator = ?, assigned_at = ?
            WHERE id IN (
                SELECT id FROM images
                WHERE status = 'pending'
                LIMIT ?
            )
        """, (annotator_name, now, batch_size))
    conn.commit()
    conn.close()

# --- EXPORTER LE DATASET ---
def export_dataset():
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

    return len(rows)


# --- PAGE D'ACCUEIL ---
@app.route("/", methods=["GET", "POST"])
def home():
    reset_expired_assignments()
    if request.method == "POST":
        annotator = request.form.get("annotator", "").strip()
        session['annotator'] = annotator or "anonyme"
        assign_images_to_user(session['annotator'])
        return redirect(url_for("annotate"))

    total = get_total_image_count()
    remaining = get_not_annotated_count()
    return render_template("home.html", remaining=remaining, total=total)

# --- PAGE D'ANNOTATION ---
@app.route("/annotate", methods=["GET", "POST"])
def annotate():
    reset_expired_assignments()
    annotator = session.get("annotator", "anonyme")

    if request.method == "POST":
        image_id = int(request.form["image_id"])
        action = request.form["action"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        if action == "add":
            word_text = request.form["text"]
            cur.execute("""
                UPDATE images
                SET text = ?, status = 'annotated'
                WHERE id = ? AND annotator = ?
            """, (word_text, image_id, annotator))

            conn.commit()
            conn.close()

            export_dataset()  
            return redirect(url_for("annotate"))


        elif action == "skip":
            cur.execute("""
                UPDATE images
                SET status = 'pending', annotator = NULL, assigned_at = NULL
                WHERE id = ? AND annotator = ?
            """, (image_id, annotator))

        conn.commit()
        conn.close()
        return redirect(url_for("annotate"))

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, path FROM images WHERE status = 'processing' AND annotator = ? LIMIT 1", (annotator,))
    row = cur.fetchone()
    conn.close()

    total = get_total_image_count()
    assigned = get_user_processing_count(annotator)
    remaining = get_user_remaining_annotations(annotator)
    total_annotated = get_total_annotated_count()

    if row:
        image_id, image_path = row
        return render_template("annotate.html", image_id=image_id, image_path=image_path,
                               annotator=annotator, total=total, assigned=assigned,
                               remaining=remaining, total_annotated=total_annotated)
    else:
        return "<h2>Toutes les images ont été annotées ou assignées!</h2>"


# --- LANCEMENT --- 
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
