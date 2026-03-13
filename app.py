from flask import Flask, render_template, request
import pickle

app = Flask(__name__)

model = pickle.load(open("model.pkl","rb"))
vectorizer = pickle.load(open("vectorizer.pkl","rb"))

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    news = request.form['news']

    vect = vectorizer.transform([news])
    prediction = model.predict(vect)

    if prediction[0] == 0:
        result = "Fake News"
    else:
        result = "Real News"

    return render_template("result.html", result=result)

if __name__ == "__main__":
    app.run(debug=True)