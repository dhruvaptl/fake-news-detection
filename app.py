from flask import Flask, render_template, request, redirect, url_for, flash, session
import pickle
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "fake_news_secret_key_123"

# Load ML model
model = pickle.load(open("models/model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))


def init_db():
    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS predictions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        news TEXT,
        result TEXT,
        confidence REAL,
        date TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT news, result, confidence, date
    FROM predictions
    ORDER BY id DESC
    LIMIT 5
    """)
    history = cursor.fetchall()

    conn.close()

    return render_template("index.html", history=history, user=session.get("user"))


@app.route("/predict", methods=["POST"])
def predict():
    news = request.form.get("news", "").strip()

    if not news:
        return render_template(
            "result.html",
            result="No Input",
            confidence=0,
            warning="⚠ Please enter some news text first.",
            user=session.get("user")
        )

    vect = vectorizer.transform([news])

    prediction_data = model.predict(vect)
    prob = model.predict_proba(vect)
    confidence = round(max(prob[0]) * 100, 2)

    if prediction_data[0] == 0:
        result = "Fake News"
        warning = "⚠️ This news may be misleading or suspicious based on the current model prediction."
    else:
        result = "Real News"
        warning = "✅ This news appears more reliable based on the current model prediction."

    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO predictions (news, result, confidence, date)
    VALUES (?, ?, ?, ?)
    """, (
        news,
        result,
        confidence,
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        result=result,
        confidence=confidence,
        warning=warning,
        user=session.get("user")
    )


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT result, COUNT(*)
    FROM predictions
    GROUP BY result
    """)
    data = cursor.fetchall()

    cursor.execute("""
    SELECT news, result, confidence, date
    FROM predictions
    ORDER BY id DESC
    LIMIT 5
    """)
    history = cursor.fetchall()

    conn.close()

    fake = 0
    real = 0

    for row in data:
        if row[0] == "Fake News":
            fake = row[1]
        elif row[0] == "Real News":
            real = row[1]

    total = fake + real

    return render_template(
        "dashboard.html",
        fake=fake,
        real=real,
        total=total,
        history=history,
        user=session.get("user")
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        action = request.form.get("action", "").strip()

        if not email or not password:
            flash("Please enter both email and password.")
            return redirect(url_for("login"))

        conn = sqlite3.connect("database/history.db")
        cursor = conn.cursor()

        if action == "signup":
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            existing_user = cursor.fetchone()

            if existing_user:
                conn.close()
                flash("This email is already registered. Please login.")
                return redirect(url_for("login"))

            cursor.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, password)
            )
            conn.commit()
            conn.close()

            flash("Signup successful. Now login with your registered email and password.")
            return redirect(url_for("login"))

        elif action == "login":
            cursor.execute(
                "SELECT * FROM users WHERE email = ? AND password = ?",
                (email, password)
            )
            user = cursor.fetchone()
            conn.close()

            if user:
                session["user"] = email
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid email or password.")
                return redirect(url_for("login"))

        else:
            conn.close()
            flash("Invalid action.")
            return redirect(url_for("login"))

    return render_template("login.html", user=session.get("user"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        new_password = request.form.get("new_password", "").strip()

        if not email or not new_password:
            flash("Please enter your email and new password.")
            return redirect(url_for("forgot_password"))

        conn = sqlite3.connect("database/history.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if not user:
            conn.close()
            flash("This email is not registered.")
            return redirect(url_for("forgot_password"))

        cursor.execute(
            "UPDATE users SET password = ? WHERE email = ?",
            (new_password, email)
        )
        conn.commit()
        conn.close()

        flash("Password reset successful. Please login with your new password.")
        return redirect(url_for("login"))

    return render_template("forgot_password.html", user=session.get("user"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)