"""
Flask Dashboard Server
======================
Author  : Aditya Rai
Project : Demo API Assignment - Option 1
Description:
    A beautiful web dashboard to monitor and control the LinkedIn auto-applier.
    Run this alongside main.py to get real-time visual feedback.

Usage:
    python dashboard.py
    Then open: http://localhost:5000
"""

import os
import sys

# Windows UTF-8 fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import json
import threading
import subprocess
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
logger = logging.getLogger(__name__)

# Shared state for the running pipeline
pipeline_state = {
    "status": "idle",          # idle | running | completed | error
    "current_step": 0,         # 1-4
    "step_logs": [],           # List of log messages
    "jobs": [],                # Found jobs
    "emails_sent": 0,
    "start_time": None,
    "end_time": None,
    "results": {},
}
state_lock = threading.Lock()


def load_results():
    """Load results.json if it exists."""
    if os.path.exists("results.json"):
        try:
            with open("results.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/api/status")
def get_status():
    """Return current pipeline status as JSON."""
    with state_lock:
        results = load_results()
        return jsonify({
            **pipeline_state,
            "results_file": results,
        })


@app.route("/api/run", methods=["POST"])
def run_pipeline():
    """Start the LinkedIn auto-applier pipeline."""
    with state_lock:
        if pipeline_state["status"] == "running":
            return jsonify({"error": "Pipeline already running"}), 400

        pipeline_state.update({
            "status": "running",
            "current_step": 1,
            "step_logs": ["🚀 Pipeline started..."],
            "jobs": [],
            "emails_sent": 0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "results": {},
        })

    data = request.json or {}
    demo_mode = data.get("demo", False)
    search_only = data.get("search_only", False)
    headless = data.get("headless", True)

    def run_in_thread():
        args = [sys.executable, "main.py"]
        if demo_mode:
            args.append("--demo")
        if search_only:
            args.append("--search-only")
        if headless:
            args.append("--headless")

        try:
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

            for line in proc.stdout:
                line = line.rstrip()
                if not line:
                    continue

                with state_lock:
                    pipeline_state["step_logs"].append(line)

                    # Update step tracker based on log output
                    if "STEP 1" in line:
                        pipeline_state["current_step"] = 1
                    elif "STEP 2" in line:
                        pipeline_state["current_step"] = 2
                    elif "STEP 3" in line:
                        pipeline_state["current_step"] = 3
                    elif "STEP 4" in line:
                        pipeline_state["current_step"] = 4

            proc.wait()

            with state_lock:
                if proc.returncode == 0:
                    pipeline_state["status"] = "completed"
                    pipeline_state["current_step"] = 4
                    pipeline_state["step_logs"].append("✅ Pipeline completed successfully!")
                    results = load_results()
                    pipeline_state["results"] = results
                    pipeline_state["jobs"] = results.get("jobs", [])
                    pipeline_state["emails_sent"] = results.get("emails_sent", 0)
                else:
                    pipeline_state["status"] = "error"
                    pipeline_state["step_logs"].append("❌ Pipeline exited with an error.")
                pipeline_state["end_time"] = datetime.now().isoformat()

        except Exception as e:
            with state_lock:
                pipeline_state["status"] = "error"
                pipeline_state["step_logs"].append(f"❌ Error: {e}")
                pipeline_state["end_time"] = datetime.now().isoformat()

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    return jsonify({"message": "Pipeline started"})


@app.route("/api/reset", methods=["POST"])
def reset_pipeline():
    """Reset pipeline state to idle."""
    with state_lock:
        pipeline_state.update({
            "status": "idle",
            "current_step": 0,
            "step_logs": [],
            "jobs": [],
            "emails_sent": 0,
            "start_time": None,
            "end_time": None,
            "results": {},
        })
    return jsonify({"message": "Reset successful"})


@app.route("/api/results")
def get_results():
    """Return the full results.json data."""
    return jsonify(load_results())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f">> Dashboard running at: http://localhost:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)
