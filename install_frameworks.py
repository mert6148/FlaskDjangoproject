"""Proje için Python frameworkleri yükler ve automaticamente assets/src dizinlerini geliştirir."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd, **kwargs):
    print("$", " ".join(cmd))
    subprocess.check_call(cmd, **kwargs)


def install_python_frameworks():
    venv = ROOT / ".venv"
    if not venv.exists():
        print("[INFO] Sanal ortam oluşturuluyor...")
        run([sys.executable, "-m", "venv", str(venv)])

    pip = venv / "Scripts" / "pip.exe" if os.name == "nt" else venv / "bin" / "pip"
    python = venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"

    run([str(pip), "install", "--upgrade", "pip"])
    run([str(pip), "install", "flask", "django", "fastapi", "uvicorn", "sqlalchemy", "flask-sqlalchemy", "djangorestframework"])

    return python


def generate_assets_and_src():
    print('[INFO] assets/src dizinlerine örnek dosyalar oluşturuluyor...')

    assets = ROOT / "assets"
    src = ROOT / "src"
    assets.mkdir(parents=True, exist_ok=True)
    src.mkdir(parents=True, exist_ok=True)

    (assets / "frontend_readme.md").write_text("""# Assets Geliştirme

Bu klasör, JavaScript ve stil dosyalarını ve framework eklentilerini içerir.
""", encoding="utf-8")

    (src / "api_demo.py").write_text("""from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/ping')
def ping():
    return jsonify({'pong': True})

if __name__ == '__main__':
    app.run(port=5002, debug=True)
""", encoding="utf-8")

    (src / "frontend_demo.js").write_text("""async function ping() {
  const res = await fetch('/api/ping');
  const data = await res.json();
  console.log('ping->', data);
}

ping();
""", encoding="utf-8")

    (assets / "index.html").write_text("""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'><title>Asset Demo</title></head>
<body>
<h1>Asset Klasörü Çalışıyor</h1>
<script src='../src/frontend_demo.js'></script>
</body>
</html>
""", encoding="utf-8")

    # Framework köprüsü olan .md
    (ROOT / "frameworks_status.md").write_text("""# Yüklü framework durumları

- Flask: Evet
- Django: Evet
- FastAPI: Evet
""", encoding="utf-8")

    return [assets, src]


def main():
    p = install_python_frameworks()
    created = generate_assets_and_src()
    print("[SUCCESS] Frameworkler yüklendi.")
    print("[SUCCESS] Diziler oluşturuldu:")
    for c in created:
        print(" -", c)
    print("[INFO] Çalıştırmak için: {} src/api_demo.py".format(p))


if __name__ == '__main__':
    main()
