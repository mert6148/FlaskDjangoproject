import os
import sys
import subprocess
import time
import atexit

from flask import Flask, jsonify, request, redirect, url_for, send_from_directory
import requests

app = Flask(__name__, static_folder="docs", static_url_path="")

BACKENDS = {
    "flask": "http://127.0.0.1:5000",
    "django": "http://127.0.0.1:8000",
}

backend_processes = {}
current_backend = os.environ.get("MODE", "flask")


def start_backend(mode: str) -> None:
    if mode not in BACKENDS:
        raise ValueError(f"Bilinmeyen backend: {mode}")

    if mode in backend_processes and backend_processes[mode].poll() is None:
        return

    env = os.environ.copy()
    env["MODE"] = mode
    # auth/main.py, app.py veya build handles this mode well.
    backend_processes[mode] = subprocess.Popen(
        [sys.executable, "auth/main.py"],
        cwd=os.getcwd(),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)


def stop_backends() -> None:
    for proc in backend_processes.values():
        if proc and proc.poll() is None:
            proc.terminate()
    backend_processes.clear()


def proxy_request(path: str):
    target_url = BACKENDS[current_backend] + path
    method = request.method
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
    try:
        resp = requests.request(
            method,
            target_url,
            headers=headers,
            params=request.args,
            json=request.get_json(silent=True),
            data=request.get_data(),
            timeout=10,
        )
    except requests.RequestException as e:
        return jsonify({"error": "Backend bağlantısı hatası", "detail": str(e)}), 502

    response = jsonify(resp.json()) if resp.headers.get("content-type", "").startswith("application/json") else resp.content
    return (response, resp.status_code, resp.headers.items())


@app.route("/")
def root():
    return send_from_directory("docs", "index.html")


@app.route("/docs/<path:p>")
def docs_files(p):
    return send_from_directory("docs", p)


@app.route("/api/mode", methods=["GET", "POST"])
def mode_endpoint():
    global current_backend
    if request.method == "GET":
        return jsonify({"mode": current_backend, "backends": list(BACKENDS.keys())})

    data = request.get_json(silent=True) or {}
    selected = data.get("mode")
    if selected not in BACKENDS:
        return jsonify({"error": "Geçersiz mod"}), 400

    current_backend = selected
    start_backend(selected)
    return jsonify({"mode": current_backend})


@app.route("/api/proxy/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def api_proxy(path):
    return proxy_request(f"/{path}")


@app.route("/api/status")
def status():
    has_flask = False
    has_django = False
    try:
        has_flask = requests.get(BACKENDS["flask"] + "/api/status", timeout=2).ok
    except Exception:
        pass
    try:
        has_django = requests.get(BACKENDS["django"] + "/", timeout=2).ok
    except Exception:
        pass
    return jsonify({"current_backend": current_backend, "flask_up": has_flask, "django_up": has_django})


if __name__ == "__main__":
    # Her iki backend'i de başlat
    start_backend("flask")
    start_backend("django")

    atexit.register(stop_backends)

    print("Frontend otomasyon kubigi 9000 portunda başlatılıyor...")
    app.run(host="0.0.0.0", port=9000, debug=True)
