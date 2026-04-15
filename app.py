from sqlite3 import TimeFromTicks
import time
from flask import Flask, render_template, request, redirect, session, send_file, flash
import sqlite3
import csv
import os
from werkzeug.utils import secure_filename
from reportlab.platypus import SimpleDocTemplate, Table
import qrcode

app = Flask(__name__)
def session_timeout():
    session.permanent = True
    now = time.time()

    if "last_activity" in session:
        last = session["last_activity"]

        # 🛠 FIX: handle old datetime values
        if not isinstance(last, (int, float)):
            session["last_activity"] = now
            return

        if now - last > 600:
            session.clear()
            return redirect("/?expired=1")

    session["last_activity"] = now

app.secret_key = "secret123"
# app.permanent_session_lifetime = timedelta(minutes=10) #AutoLogout after 10 minutes


UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# INIT DB
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # STUDENTS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS students
    (
        id INTEGER PRIMARY KEY,
        name TEXT,
        age INTEGER,
        course TEXT,
        date TEXT,
        image TEXT,
        favorite INTEGER DEFAULT 0,
        username TEXT,
        password TEXT
    )''')

    # ANNOUNCEMENTS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS announcements
    (
        id INTEGER PRIMARY KEY,
        message TEXT,
        date TEXT
    )''')

    conn.commit()
    conn.close()

init_db()

# LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role")
        username = request.form.get("username")
        password = request.form.get("password")

        # ADMIN
        if role == "admin" and username == "admin" and password == "admin":
            session["user"] = username
            session["role"] = "admin"
            session.permanent = True

        # FACULTY
        elif role == "faculty":
            session["user"] = username
            session["role"] = "faculty"
            session.permanent = True

        # STUDENT (REAL LOGIN)
        elif role == "student":
            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("SELECT * FROM students WHERE username=? AND password=?", (username, password))
            user = c.fetchone()
            conn.close()

            if user:
                session["user"] = username
                session["role"] = "student"
                session.permanent = True
                session["student_id"] = user[0]
            else:
                return render_template("login.html", error="Invalid Student login", expired=None)
                # return render_template("login.html", error="Invalid Student login")

        else:
            return render_template("login.html", error="Invalid login")

        return redirect("/dashboard")
            

    return render_template("login.html", expired=request.args.get("expired"))
    # return render_template("login.html")

# LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 📢 FETCH ANNOUNCEMENTS
    c.execute("SELECT * FROM announcements ORDER BY id DESC")
    announcements = c.fetchall()

    # 👨‍🎓 STUDENT DASHBOARD
    if session.get("role") == "student":
        c.execute("SELECT * FROM students WHERE id=?", (session.get("student_id"),))
        student = c.fetchone()
        conn.close()

        return render_template("student_dashboard.html",
                               student=student,
                               announcements=announcements)

    # 👨‍💼 ADMIN / FACULTY DASHBOARD
    c.execute("SELECT * FROM students")
    data = c.fetchall()

    total = len(data)

    # SMART INSIGHTS
    ages = [s[2] for s in data if s[2]]
    avg_age = round(sum(ages)/len(ages), 1) if ages else 0

    courses = {}
    for s in data:
        courses[s[3]] = courses.get(s[3], 0) + 1

    top_course = max(courses, key=courses.get) if courses else "N/A"
    favorites = len([s for s in data if s[6] == 1])

    conn.close()

    return render_template("dashboard.html",
        students=data,
        total=total,
        avg_age=avg_age,
        top_course=top_course,
        favorites=favorites,
        announcements=announcements
    )

# ADD STUDENT
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]
        date = request.form["date"]
        username = request.form["username"]
        password = request.form["password"]

        file = request.files["image"]
        filename = ""
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO students (name, age, course, date, image, username, password) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (name, age, course, date, filename, username, password))
        conn.commit()
        conn.close()

        flash("Student added successfully!")
        return redirect("/dashboard")

    return render_template("add_student.html")

# ADD ANNOUNCEMENT
@app.route("/add_announcement", methods=["POST"])
def add_announcement():
    if session.get("role") != "admin":
        return "Access Denied"

    message = request.form["message"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO announcements (message, date) VALUES (?, date('now'))", (message,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# DELETE ANNOUNCEMENT
@app.route("/delete_announcement/<int:id>")
def delete_announcement(id):
    if session.get("role") != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM announcements WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

# DELETE STUDENT
@app.route("/delete/<int:id>")
def delete(id):
    if session.get("role") != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Student deleted!")
    return redirect("/dashboard")

# EDIT
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if session.get("role") == "student":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        course = request.form["course"]

        c.execute("UPDATE students SET name=?, age=?, course=? WHERE id=?",
                  (name, age, course, id))
        conn.commit()
        conn.close()

        flash("Student updated!")
        return redirect("/dashboard")

    c.execute("SELECT * FROM students WHERE id=?", (id,))
    student = c.fetchone()
    conn.close()

    return render_template("edit_student.html", s=student)

# FAVORITE
@app.route("/favorite/<int:id>")
def favorite(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE students SET favorite = NOT favorite WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")

# PROFILE
@app.route("/student/<int:id>")
def student(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE id=?", (id,))
    s = c.fetchone()
    conn.close()
    return render_template("profile.html", s=s)

# EXPORT CSV
@app.route("/export")
def export():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM students")
    data = c.fetchall()
    conn.close()

    with open("students.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Name", "Age", "Course", "Date", "Image"])
        writer.writerows(data)

    return send_file("students.csv", as_attachment=True)

# SEARCH
@app.route("/search_suggestions")
def search_suggestions():
    query = request.args.get("q", "")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, name FROM students WHERE name LIKE ? LIMIT 5", ('%' + query + '%',))
    results = c.fetchall()
    conn.close()

    return {"data": results}

# EXPORT PDF
@app.route("/export_pdf")
def export_pdf():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT name, age, course FROM students")
    data = c.fetchall()
    conn.close()

    file = "students.pdf"
    doc = SimpleDocTemplate(file)

    table_data = [["Name", "Age", "Course"]] + list(data)
    table = Table(table_data)

    doc.build([table])

    return send_file(file, as_attachment=True)

# QR
@app.route("/qr/<int:id>")
def qr(id):
    url = f"http://127.0.0.1:5000/student/{id}"
    img = qrcode.make(url)
    path = f"static/uploads/qr_{id}.png"
    img.save(path)
    return send_file(path, mimetype='image/png')

app.run(debug=True)
