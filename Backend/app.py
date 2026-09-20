from flask import Flask, request, jsonify
from flask_cors import CORS
from scamcheck import analyze_input
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()

    result = analyze_input(
        data.get("type"),
        data.get("content"),
        data.get("url")
    )

    return jsonify(result)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ScamCheck backend running"})

if __name__ == "__main__":
    app.run(debug=False, port=5000)