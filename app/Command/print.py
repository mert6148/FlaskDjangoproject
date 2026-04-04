import os
import sys

try:
    from flask import Flask, jsonify
except ImportError:
    Flask = None
    jsonify = None

import s2clientprotocol

def sched_get_priority_max(policy):
    """Sistem tarafından desteklenen en yüksek öncelik değerini döndürür."""
    if policy == os.SCHED_FIFO:
        return 99
    elif policy == os.SCHED_RR:
        return 99
    elif policy == os.SCHED_OTHER:
        return 0
    else:
        raise ValueError("Geçersiz planlama politikası: {}".format(policy))
    

def sched_get_priority_min(policy):
    """Sistem tarafından desteklenen en düşük öncelik değerini döndürür."""
    if policy == os.SCHED_FIFO:
        return 1
    elif policy == os.SCHED_RR:
        return 1
    elif policy == os.SCHED_OTHER:
        return 0
    else:
        raise ValueError("Geçersiz planlama politikası: {}".format(policy))


def create_flask_app():
    if Flask is None:
        raise RuntimeError("Flask yuklu degil. run.bat ile oncelikle Flask'i yukleyin.")

    app = Flask(__name__)

    @app.route("/"
    )
    def index():
        return jsonify({"message": "Flask calisiyor"})

    @app.route("/status")
    def status():
        return jsonify({"status": "OK", "python_version": sys.version})

    return app


def main():
    if Flask is None:
        print("Flask paketini yuklemeniz gerekiyor. run.bat dosyasini calistirin.")
        return

    app = create_flask_app()
    app.run(host="0.0.0.0", port=5001, debug=True)


if __name__ == "__main__":
    main()