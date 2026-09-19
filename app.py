import os

from flask import Flask, render_template


app = Flask(__name__)


# ============================================================
# WEB ROUTES
# ============================================================

@app.route("/")
def home():
    """
    Serve the main Onyx status page.

    Live status information is retrieved by the frontend
    directly from the Onyx Cloudflare status API.
    """

    return render_template("index.html")


@app.route("/health")
def health():
    """
    Health check for the status website itself.

    This endpoint only confirms that this Flask application
    is online and responding. It does not represent the
    health of the Onyx Discord bot.
    """

    return {
        "status": "ok",
        "service": "onyx-status-website",
    }, 200


@app.route("/test")
def test():
    """
    Simple endpoint used for testing deployments and
    pull requests.
    """

    return "ok", 200


@app.route("/contact")
def contact():
    """
    Serve the Onyx contact page.
    """

    return render_template("contact.html")


# ============================================================
# LOCAL DEVELOPMENT
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000,
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )