"""
dashboard_server.py — FlaskDjango Proje Dashboard Sunucusu
Tüm proje verilerini gerçek zamanlı sunan Flask arka uç.
"""

import os
import sys
import json
import time
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from flask import Flask, jsonify, render_template_string, send_from_directory

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dashboard-secret")

ROOT = Path(__file__).resolve().parent

# ── Proje dosya listesi ────────────────────────────────────────────────────────
PROJECT_FILES = [
    {"name": "main.py",            "ext": "py",   "category": "core",    "desc": "Flask & Django uygulama giriş noktası"},
    {"name": "app.py",             "ext": "py",   "category": "core",    "desc": "Flask rotaları ve ZipFile sarmalayıcıları"},
    {"name": "print.py",           "ext": "py",   "category": "core",    "desc": "Yardımcı sınıflar ve assertion örnekleri"},
    {"name": "build.py",           "ext": "py",   "category": "build",   "desc": "FastAdmin dokümantasyon derleme aracı"},
    {"name": "verify_workflow.py", "ext": "py",   "category": "test",    "desc": "CLI doğrulama ve test aracı"},
    {"name": "index.js",           "ext": "js",   "category": "frontend","desc": "Sistem meta verileri ve DOM yardımcıları"},
    {"name": "index.html",         "ext": "html", "category": "frontend","desc": "Sistem dashboard arayüzü"},
    {"name": "system.json",        "ext": "json", "category": "config",  "desc": "Sistem yapılandırma verisi"},
    {"name": "system_output.json", "ext": "json", "category": "config",  "desc": "Sistem çıktı verisi"},
    {"name": "README.md",          "ext": "md",   "category": "docs",    "desc": "Proje dokümantasyonu"},
]

# ── Flask API endpoint'leri ───────────────────────────────────────────────────
FLASK_ENDPOINTS = [
    {"method": "GET",    "path": "/",                        "desc": "Ana sayfa"},
    {"method": "GET",    "path": "/api/status",              "desc": "Sistem durumu"},
    {"method": "GET",    "path": "/api/kullanicilar",        "desc": "Kullanıcı listesi"},
    {"method": "POST",   "path": "/api/kullanicilar",        "desc": "Yeni kullanıcı oluştur"},
    {"method": "GET",    "path": "/api/kullanicilar/<id>",   "desc": "Kullanıcı getir"},
    {"method": "PUT",    "path": "/api/kullanicilar/<id>",   "desc": "Kullanıcı güncelle"},
    {"method": "DELETE", "path": "/api/kullanicilar/<id>",   "desc": "Kullanıcı sil"},
    {"method": "GET",    "path": "/api/urunler",             "desc": "Ürün listesi"},
    {"method": "POST",   "path": "/api/urunler",             "desc": "Yeni ürün oluştur"},
]

DJANGO_ENDPOINTS = [
    {"method": "GET",  "path": "/api/kategoriler/",              "desc": "Kategori listesi"},
    {"method": "POST", "path": "/api/kategoriler/",              "desc": "Yeni kategori"},
    {"method": "GET",  "path": "/api/kategoriler/<pk>/",         "desc": "Kategori detay"},
    {"method": "PUT",  "path": "/api/kategoriler/<pk>/",         "desc": "Kategori güncelle"},
    {"method": "DELETE","path": "/api/kategoriler/<pk>/",        "desc": "Kategori sil"},
    {"method": "GET",  "path": "/api/kategoriler/<pk>/urunler/", "desc": "Kategoriye ait ürünler"},
    {"method": "GET",  "path": "/api/urunler/",                  "desc": "Ürün listesi"},
    {"method": "POST", "path": "/api/urunler/",                  "desc": "Yeni ürün"},
    {"method": "GET",  "path": "/api/urunler/stok_yok/",         "desc": "Stoğu tükenen ürünler"},
    {"method": "POST", "path": "/api/urunler/<pk>/stok_ekle/",   "desc": "Stok güncelle"},
]


def get_file_info(fname: str) -> dict:
    path = ROOT / fname
    if path.exists():
        stat = path.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%H:%M:%S")
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size/1024:.1f} KB"
        else:
            size_str = f"{size/1024/1024:.1f} MB"
        return {"exists": True, "size": size_str, "mtime": mtime, "bytes": size}
    return {"exists": False, "size": "—", "mtime": "—", "bytes": 0}


def load_json_file(fname: str) -> dict | None:
    path = ROOT / fname
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


# ── API Rotaları ─────────────────────────────────────────────────────────────

@app.route("/api/dashboard/overview")
def overview():
    """Genel proje istatistikleri."""
    files_info = []
    total_bytes = 0
    for f in PROJECT_FILES:
        info = get_file_info(f["name"])
        files_info.append({**f, **info})
        total_bytes += info["bytes"]

    return jsonify({
        "total_files": len(PROJECT_FILES),
        "total_size": f"{total_bytes/1024:.1f} KB",
        "flask_endpoints": len(FLASK_ENDPOINTS),
        "django_endpoints": len(DJANGO_ENDPOINTS),
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "files": files_info,
    })


@app.route("/api/dashboard/system")
def system_info():
    """system.json ve system_output.json içerikleri."""
    sys_data = load_json_file("system.json")
    out_data = load_json_file("system_output.json")
    return jsonify({
        "system": sys_data,
        "output": out_data,
        "env": {
            "MODE": os.environ.get("MODE", "flask"),
            "DEBUG": os.environ.get("FLASK_DEBUG", "true"),
            "PORT": os.environ.get("PORT", "5000"),
        }
    })


@app.route("/api/dashboard/endpoints")
def endpoints():
    return jsonify({
        "flask": FLASK_ENDPOINTS,
        "django": DJANGO_ENDPOINTS,
    })


@app.route("/api/dashboard/files")
def files_api():
    result = []
    for f in PROJECT_FILES:
        info = get_file_info(f["name"])
        result.append({**f, **info})
    return jsonify(result)


@app.route("/api/dashboard/verify")
def verify():
    """verify_workflow.py'yi çalıştırır."""
    vw = ROOT / "verify_workflow.py"
    if not vw.exists():
        return jsonify({"success": False, "output": "verify_workflow.py bulunamadı", "duration": 0})
    start = time.time()
    try:
        result = subprocess.run(
            [sys.executable, str(vw), "--all"],
            capture_output=True, text=True, timeout=15,
        )
        duration = round(time.time() - start, 2)
        success = result.returncode == 0
        output = (result.stdout + result.stderr).strip()
        return jsonify({"success": success, "output": output or "Çıktı yok", "duration": duration})
    except subprocess.TimeoutExpired:
        return jsonify({"success": False, "output": "Zaman aşımı (15s)", "duration": 15})
    except Exception as e:
        return jsonify({"success": False, "output": str(e), "duration": 0})


@app.route("/api/status")
def status():
    return jsonify({"status": "ok", "version": "1.0.0", "timestamp": datetime.now().isoformat()})


@app.route("/")
def index():
    """Dashboard ana sayfası."""
    dashboard_html = Path(__file__).parent / "dashboard.html"
    if dashboard_html.exists():
        return dashboard_html.read_text(encoding="utf-8")
    return jsonify({"error": "dashboard.html bulunamadı"}), 404


if __name__ == "__main__":
    print("=" * 55)
    print("  FlaskDjango Dashboard Sunucusu")
    print("  http://127.0.0.1:5050")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5050, debug=True)