import os
import time
import threading
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

CHECK_INTERVAL = 60  # seconds
REQUEST_TIMEOUT = 10  # seconds

SERVICES = {
    "platform": {
        "name": "Onyx Platform",
        "description": "Core application and dashboard",
        "url": "https://onyx.builtbybuzz.dev",
    },
    "api": {
        "name": "API",
        "description": "API requests and integrations",
        "url": None,
    },
    "webhooks": {
        "name": "Webhooks",
        "description": "Event delivery and notifications",
        "url": None,
    },
    "authentication": {
        "name": "Authentication",
        "description": "Login and account services",
        "url": None,
    },
}


# ============================================================
# STATUS STORAGE
# ============================================================

service_status = {}

status_lock = threading.Lock()


def initialize_status():
    """
    Give every service an initial state before the first
    monitoring cycle finishes.
    """

    with status_lock:
        for service_id, service in SERVICES.items():
            service_status[service_id] = {
                "name": service["name"],
                "description": service["description"],
                "status": "unknown",
                "response_time_ms": None,
                "last_checked": None,
                "status_code": None,
            }


# ============================================================
# SERVICE CHECKING
# ============================================================

def check_service(service_id, service):
    """
    Perform an HTTP request against one service and return
    the resulting health information.
    """

    url = service.get("url")

    # A service without a monitoring URL isn't configured yet.
    if not url:
        return {
            "name": service["name"],
            "description": service["description"],
            "status": "unknown",
            "response_time_ms": None,
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "status_code": None,
        }

    start_time = time.perf_counter()

    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        if 200 <= response.status_code < 400:
            status = "operational"
        elif 400 <= response.status_code < 500:
            status = "degraded"
        else:
            status = "outage"

        return {
            "name": service["name"],
            "description": service["description"],
            "status": status,
            "response_time_ms": elapsed_ms,
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "status_code": response.status_code,
        }

    except requests.RequestException:
        elapsed_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        return {
            "name": service["name"],
            "description": service["description"],
            "status": "outage",
            "response_time_ms": elapsed_ms,
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "status_code": None,
        }


def run_monitoring_cycle():
    """
    Check every configured service.
    """

    print("[MONITOR] Starting service checks...")

    for service_id, service in SERVICES.items():

        result = check_service(
            service_id,
            service,
        )

        with status_lock:
            service_status[service_id] = result

        print(
            f"[MONITOR] {result['name']}: "
            f"{result['status']} "
            f"({result['response_time_ms']} ms)"
        )


def monitoring_loop():
    """
    Continuously monitor services in the background.
    """

    while True:

        try:
            run_monitoring_cycle()

        except Exception as exc:
            print(
                f"[MONITOR] Monitoring cycle failed: {exc}"
            )

        time.sleep(CHECK_INTERVAL)


# ============================================================
# OVERALL STATUS
# ============================================================

def calculate_overall_status(services):
    """
    Determine the overall Onyx status from all configured
    components.
    """

    statuses = [
        service["status"]
        for service in services.values()
        if service["status"] != "unknown"
    ]

    if not statuses:
        return "unknown"

    if "outage" in statuses:
        return "outage"

    if "degraded" in statuses:
        return "degraded"

    return "operational"


# ============================================================
# WEB ROUTES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/status")
def api_status():

    with status_lock:
        statuses = {
            service_id: dict(data)
            for service_id, data in service_status.items()
        }

    overall = calculate_overall_status(statuses)

    return jsonify({
        "overall": overall,
        "components": statuses,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    })


@app.route("/health")
def health():
    """
    Health check specifically for the status page itself.

    This does NOT mean every Onyx service is operational.
    It only means this Flask application is responding.
    """

    return jsonify({
        "status": "ok",
        "service": "onyx-status",
    }), 200

@app.route("/test")
def test():
    """
    Test variant to test my pull requests
    """
    return "ok"

@app.route("/contact")
def contact():
    """
    Access the Contact page of the Status Page.
    """
    return render_template("contact.html")

# ============================================================
# START MONITOR
# ============================================================

initialize_status()

monitor_thread = threading.Thread(
    target=monitoring_loop,
    daemon=True,
)

monitor_thread.start()


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