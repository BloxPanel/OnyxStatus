from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "overall": "operational",
        "components": [
            {
                "name": "Onyx Discord Bot",
                "status": "operational"
            },
            {
                "name": "Onyx Website",
                "status": "operational"
            },
            {
                "name": "Onyx API",
                "status": "operational"
            }
        ]
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port
    )