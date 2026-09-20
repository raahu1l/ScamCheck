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
    data = request.get_json(silent=True)

    # Validate JSON body
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request."}), 400

    content = data.get("content") or ""
    url = data.get("url") or ""

    # Validate data types
    if not isinstance(content, str):
        return jsonify({"error": "Content must be text."}), 400

    if not isinstance(url, str):
        return jsonify({"error": "URL must be text."}), 400

    # Require at least one input
    if not content.strip() and not url.strip():
        return jsonify({
            "error": "Please provide posting text or an application URL."
        }), 400

    # Prevent excessively large input
    if len(content) > 20000:
        return jsonify({
            "error": "Posting text is too large. Maximum 20,000 characters."
        }), 400

    # Prevent excessively long URLs
    if len(url) > 2000:
        return jsonify({
            "error": "URL is too long."
        }), 400

    result = analyze_input(
        data.get("type"),
        content.strip(),
        url.strip() or None
    )

    return jsonify(result)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ScamCheck backend running"})


if __name__ == "__main__":
    app.run(debug=False, port=5000)