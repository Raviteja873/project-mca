import re
import os
from pathlib import Path
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_file, abort
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "replace-with-a-random-secret-key"

ALLOWED_DOMAIN = "@gvpce.ac.in"
BASE_DIR = Path(__file__).parent.resolve()
TEXTBOOK_ROOT = BASE_DIR / "static" / "textbooks"
ALLOWED_EXTS = {".pdf"}

SYLLABUS = {
    1: [
        {"code": "MCS101", "name": "Mathematics for Computer Science"},
        {"code": "MCS102", "name": "Programming in C"},
        {"code": "MCS103", "name": "Data Structures"}
    ],
    2: [
        {"code": "MCS201", "name": "DBMS"},
        {"code": "MCS202", "name": "Operating Systems"},
        {"code": "MCS203", "name": "OOP with Java"}
    ],
    3: [
        {"code": "MCS301", "name": "Computer Networks"},
        {"code": "MCS302", "name": "Web Technologies"},
        {"code": "MCS303", "name": "Data Mining"}
    ],
    4: [
        {"code": "MCS401", "name": "Machine Learning"},
        {"code": "MCS402", "name": "Cloud Computing"},
        {"code": "MCS403", "name": "Internet of Things (IoT)"}
    ]
}

def is_allowed_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip()
    basic_re = r"^[a-zA-Z0-9._%+-]+@"
    return bool(re.match(basic_re, email)) and email.lower().endswith(ALLOWED_DOMAIN)

def list_textbooks_for_semester(semester: int):
    sem_dir = TEXTBOOK_ROOT / f"sem{semester}"
    if not sem_dir.exists() or not sem_dir.is_dir():
        return []
    files = []
    for p in sorted(sem_dir.iterdir()):
        if p.suffix.lower() in ALLOWED_EXTS and p.is_file():
            files.append(p.name)
    return files

def get_safe_file_path(semester: int, filename: str) -> Path:
    sem_dir = TEXTBOOK_ROOT / f"sem{semester}"
    if not sem_dir.exists():
        raise ValueError("Semester folder does not exist.")
    filename_secure = secure_filename(filename)
    requested = (sem_dir / filename_secure).resolve()
    if not str(requested).startswith(str(sem_dir.resolve())):
        raise ValueError("Invalid file path.")
    if requested.suffix.lower() not in ALLOWED_EXTS:
        raise ValueError("Disallowed file type.")
    if not requested.exists() or not requested.is_file():
        raise ValueError("File not found.")
    return requested

@app.route("/")
def index():
    if session.get("email"):
        return redirect(url_for("syllabus"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if is_allowed_email(email):
            session["email"] = email
            flash(f"Welcome — logged in as {email}", "success")
            return redirect(url_for("syllabus"))
        else:
            flash(f"Only {ALLOWED_DOMAIN} college email addresses are accepted.", "danger")
    return render_template("login.html")

@app.route("/syllabus")
def syllabus():
    if not session.get("email"):
        return redirect(url_for("login"))
    return render_template("syllabus.html", syllabus=SYLLABUS, user=session.get("email"))

@app.route("/textbooks/<int:semester>")
def textbooks(semester):
    if not session.get("email"):
        return redirect(url_for("login"))
    if semester not in SYLLABUS:
        flash("Invalid semester selected.", "warning")
        return redirect(url_for("syllabus"))
    books = list_textbooks_for_semester(semester)
    return render_template("textbooks.html", semester=semester, books=books, user=session.get("email"))

@app.route("/download/<int:semester>/<path:filename>")
def download(semester, filename):
    if not session.get("email"):
        return redirect(url_for("login"))
    try:
        file_path = get_safe_file_path(semester, filename)
    except ValueError:
        abort(404)
    return send_file(str(file_path), as_attachment=True)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/logout")
def logout():
    session.pop("email", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

def ensure_semester_dirs():
    TEXTBOOK_ROOT.mkdir(parents=True, exist_ok=True)
    for i in range(1, 5):
        (TEXTBOOK_ROOT / f"sem{i}").mkdir(exist_ok=True)

if __name__ == "__main__":
    ensure_semester_dirs()
    app.run(debug=True, host="0.0.0.0", port=5000)
