from flask import Flask, render_template, request
import pickle
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Load ML model
model = pickle.load(open("models/model.pkl", "rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl", "rb"))

# Create database if not exists
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

conn.commit()
conn.close()


# HOME PAGE
@app.route("/")
def home():

    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT news,result,confidence,date
    FROM predictions
    ORDER BY id DESC
    LIMIT 5
    """)

    history = cursor.fetchall()

    conn.close()

    return render_template("index.html", history=history)


# PREDICT ROUTE
@app.route("/predict", methods=["POST"])
def predict():

    news = request.form["news"]

    vect = vectorizer.transform([news])

    prediction = model.predict(vect)
    prob = model.predict_proba(vect)

    confidence = round(max(prob[0]) * 100, 2)

    if prediction[0] == 0:
        result = "Fake News"
        warning = "⚠ This news may be misleading."
    else:
        result = "Real News"
        warning = "✅ This news appears reliable."

    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO predictions (news,result,confidence,date)
    VALUES (?,?,?,?)
    """, (news, result, confidence,
          datetime.now().strftime("%Y-%m-%d %H:%M")))

    conn.commit()
    conn.close()

    return render_template(
        "result.html",
        result=result,
        confidence=confidence,
        warning=warning
    )


# DASHBOARD PAGE
@app.route("/dashboard")
def dashboard():

    conn = sqlite3.connect("database/history.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT result, COUNT(*)
    FROM predictions
    GROUP BY result
    """)

    data = cursor.fetchall()

    conn.close()

    fake = 0
    real = 0

    for row in data:
        if row[0] == "Fake News":
            fake = row[1]
        else:
            real = row[1]

    return render_template(
        "dashboard.html",
        fake=fake,
        real=real
    )


# LOGIN PAGE
@app.route("/login")
def login():
    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True)