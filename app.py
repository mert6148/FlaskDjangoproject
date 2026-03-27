import os
import sys
import zipfile
from flask import Flask, render_template, request, redirect, url_for, jsonify
import ipaddress

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gizli-anahtar-degistir")


# ── Yardımcı: IPv4 adresi → packed bytes ─────────────────────────────────────
def v4_int_to_packed(address: int) -> bytes:
    """32-bit integer'ı 4 baytlık packed formata çevirir."""
    return ipaddress.IPv4Address(address).packed


# ── Sıkıştırma devre dışı bırakıcı ───────────────────────────────────────────
class OP_NO_COMPRESSION:
    """ZipFile write çağrılarında sıkıştırmayı devre dışı bırakır."""
    def __call__(self, *args, **kwargs):
        return zipfile.ZIP_STORED


# ── ZipFile sarmalayıcı ───────────────────────────────────────────────────────
class SafeZipFile:
    """zipfile.ZipFile için güvenli sarmalayıcı sınıf."""

    def __init__(self, file: str, mode: str = "r"):
        self.file = file
        self.mode = mode
        self._zf: zipfile.ZipFile | None = None

    def __enter__(self):
        self._zf = zipfile.ZipFile(self.file, self.mode)
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, filename: str, arcname: str | None = None,
              compress_type=None, compresslevel: int | None = None):
        if self._zf:
            self._zf.write(filename, arcname=arcname,
                           compress_type=compress_type, compresslevel=compresslevel)

    def close(self):
        if self._zf:
            self._zf.close()
            self._zf = None

    def namelist(self) -> list[str]:
        return self._zf.namelist() if self._zf else []

    def getinfo(self, name: str) -> zipfile.ZipInfo | None:
        return self._zf.getinfo(name) if self._zf else None


# ── ZipInfo sarmalayıcı ───────────────────────────────────────────────────────
class SafeZipInfo:
    """zipfile.ZipInfo için sarmalayıcı sınıf."""

    def __init__(self, name: str):
        self.name = name
        self._info = zipfile.ZipInfo(name)

    @property
    def compress_size(self) -> int:
        return self._info.compress_size

    @property
    def file_size(self) -> int:
        return self._info.file_size


# ── Flask rotaları ────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Sayfa bulunamadı"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
