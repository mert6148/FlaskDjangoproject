#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
syscheck.py — Sistem Gereksinim Kontrol Aracı
=============================================
Proje: FlaskDjango App
Desteklenen OS: Windows · Linux · macOS

Kullanım:
  python syscheck.py              # tam rapor
  python syscheck.py --json       # JSON çıktı
  python syscheck.py --quiet      # sadece PASS/FAIL
  python syscheck.py --fix        # eksik paketleri otomatik kur
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from typing import Callable


# ═════════════════════════════════════════════════════════════════════════════
# RENKLİ ÇIKTI (ANSI — Windows 10+ ve Unix)
# ═════════════════════════════════════════════════════════════════════════════

if platform.system() == "Windows":
    os.system("color")          # Windows terminalde ANSI'yi etkinleştir

R = "\033[91m"   # kırmızı
G = "\033[92m"   # yeşil
Y = "\033[93m"   # sarı
B = "\033[94m"   # mavi
C = "\033[96m"   # camgöbeği
W = "\033[97m"   # beyaz
D = "\033[2m"    # soluk
X = "\033[0m"    # sıfırla
BOLD = "\033[1m"


def renkli(metin: str, renk: str) -> str:
    return f"{renk}{metin}{X}"


# ═════════════════════════════════════════════════════════════════════════════
# KONTROL SONUCU
# ═════════════════════════════════════════════════════════════════════════════

@dataclass
class KontrolSonucu:
    ad:      str
    tamam:   bool
    mesaj:   str
    detay:   str = ""
    uyari:   bool = False       # PASS ama dikkat edilmeli

    @property
    def sembol(self) -> str:
        if self.tamam and not self.uyari:
            return renkli("✓", G)
        if self.uyari:
            return renkli("⚠", Y)
        return renkli("✗", R)

    @property
    def etiket(self) -> str:
        if self.tamam and not self.uyari:
            return renkli("PASS", G)
        if self.uyari:
            return renkli("WARN", Y)
        return renkli("FAIL", R)

    def to_dict(self) -> dict:
        return {
            "ad":    self.ad,
            "tamam": self.tamam,
            "uyari": self.uyari,
            "mesaj": self.mesaj,
            "detay": self.detay,
        }


# ═════════════════════════════════════════════════════════════════════════════
# KONTROL FONKSİYONLARI
# ═════════════════════════════════════════════════════════════════════════════

def _surum_tuple(s: str) -> tuple[int, ...]:
    """'3.11.2' → (3, 11, 2)"""
    try:
        return tuple(int(x) for x in s.split(".")[:3])
    except ValueError:
        return (0,)


# ── 1. Python sürümü ──────────────────────────────────────────────────────────
def python_surum_kontrol(min_surum: tuple = (3, 10)) -> KontrolSonucu:
    mevcut = sys.version_info[:3]
    mevcut_str = ".".join(str(x) for x in mevcut)
    min_str    = ".".join(str(x) for x in min_surum)
    tamam = mevcut >= min_surum
    return KontrolSonucu(
        ad    = "Python Sürümü",
        tamam = tamam,
        mesaj = f"Python {mevcut_str} {'≥' if tamam else '<'} {min_str} (gerekli)",
        detay = f"Yürütücü: {sys.executable}",
    )


# ── 2. İşletim sistemi ────────────────────────────────────────────────────────
def isletim_sistemi_kontrol() -> KontrolSonucu:
    sistem = platform.system()
    surum  = platform.version()
    mimari = platform.machine()
    desteklenen = sistem in ("Windows", "Linux", "Darwin")
    return KontrolSonucu(
        ad    = "İşletim Sistemi",
        tamam = desteklenen,
        mesaj = f"{sistem} {platform.release()} ({mimari})",
        detay = surum[:80] if len(surum) > 80 else surum,
        uyari = sistem == "Darwin",   # macOS: desteklenir ama test edilmemiş
    )


# ── 3. Disk alanı ─────────────────────────────────────────────────────────────
def disk_alani_kontrol(min_mb: int = 200) -> KontrolSonucu:
    try:
        kullanim = shutil.disk_usage(Path.cwd())
        bos_mb   = kullanim.free // (1024 * 1024)
        tamam    = bos_mb >= min_mb
        return KontrolSonucu(
            ad    = "Disk Alanı",
            tamam = tamam,
            mesaj = f"{bos_mb:,} MB boş  (min {min_mb} MB gerekli)",
            detay = f"Toplam: {kullanim.total//(1024**3)} GB  |  Kullanılan: {kullanim.used//(1024**3)} GB",
            uyari = (min_mb <= bos_mb < min_mb * 2),
        )
    except Exception as e:
        return KontrolSonucu(ad="Disk Alanı", tamam=False, mesaj=str(e))


# ── 4. RAM kontrolü ───────────────────────────────────────────────────────────
def ram_kontrol(min_mb: int = 256) -> KontrolSonucu:
    try:
        import psutil
        ram = psutil.virtual_memory()
        mevcut_mb = ram.available // (1024 * 1024)
        tamam = mevcut_mb >= min_mb
        return KontrolSonucu(
            ad    = "RAM (Kullanılabilir)",
            tamam = tamam,
            mesaj = f"{mevcut_mb:,} MB mevcut  (min {min_mb} MB)",
            detay = f"Toplam RAM: {ram.total//(1024**2):,} MB  |  %{ram.percent:.0f} kullanımda",
            uyari = (min_mb <= mevcut_mb < min_mb * 2),
        )
    except ImportError:
        return KontrolSonucu(
            ad    = "RAM (Kullanılabilir)",
            tamam = True,
            mesaj = "psutil kurulu değil — RAM kontrolü atlandı",
            uyari = True,
        )


# ── 5. pip varlığı ────────────────────────────────────────────────────────────
def pip_kontrol() -> KontrolSonucu:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        tamam = result.returncode == 0
        surum = result.stdout.strip().split()[1] if tamam else "?"
        return KontrolSonucu(
            ad    = "pip",
            tamam = tamam,
            mesaj = f"pip {surum}" if tamam else "pip bulunamadı",
            detay = "python -m pip install --upgrade pip  →  güncelleyebilirsiniz",
        )
    except Exception as e:
        return KontrolSonucu(ad="pip", tamam=False, mesaj=str(e))


# ── 6. Sanal ortam ────────────────────────────────────────────────────────────
def sanal_ortam_kontrol() -> KontrolSonucu:
    aktif = (
        hasattr(sys, "real_prefix") or
        (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
    )
    venv_yolu = Path(".venv")
    return KontrolSonucu(
        ad    = "Sanal Ortam",
        tamam = True,
        mesaj = ("Aktif sanal ortam içinde çalışıyor" if aktif
                 else "Sanal ortam aktif değil"),
        detay = (f"Önerilen: python -m venv .venv  →  {venv_yolu.resolve()}"
                 if not aktif else f"prefix: {sys.prefix}"),
        uyari = not aktif,
    )


# ── 7. Python paketi varlığı ──────────────────────────────────────────────────
GEREKLI_PAKETLER: list[tuple[str, str, str]] = [
    # (import_adi,          pip_adi,               min_surum)
    ("flask",               "flask",                "3.0.0"),
    ("flask_sqlalchemy",    "flask-sqlalchemy",     "3.1.0"),
    ("flask_limiter",       "flask-limiter",        "3.5.0"),
    ("sqlalchemy",          "sqlalchemy",           "2.0.0"),
    ("jinja2",              "jinja2",               "3.1.0"),
    ("jwt",                 "PyJWT",                "2.8.0"),
    ("argon2",              "argon2-cffi",          "23.1.0"),
    ("cryptography",        "cryptography",         "42.0.0"),
    ("pytest",              "pytest",               "8.0.0"),
]

OPSIYONEL_PAKETLER: list[tuple[str, str, str]] = [
    ("django",              "django",               "5.0.0"),
    ("rest_framework",      "djangorestframework",  "3.15.0"),
    ("psutil",              "psutil",               "5.9.0"),
    ("gunicorn",            "gunicorn",             "21.2.0"),
]


def paket_kontrol(import_adi: str, pip_adi: str, min_surum: str,
                  zorunlu: bool = True) -> KontrolSonucu:
    try:
        modul = import_module(import_adi)
        surum_str = (
            getattr(modul, "__version__", None) or
            getattr(modul, "VERSION", None) or
            getattr(modul, "version", None) or "?"
        )
        if isinstance(surum_str, tuple):
            surum_str = ".".join(str(x) for x in surum_str)

        yeterli = (
            _surum_tuple(str(surum_str)) >= _surum_tuple(min_surum)
            if surum_str != "?" else True
        )
        return KontrolSonucu(
            ad    = pip_adi,
            tamam = yeterli,
            mesaj = (f"{pip_adi}=={surum_str}" if yeterli
                     else f"{pip_adi}=={surum_str}  (min {min_surum} gerekli)"),
            detay = f"import {import_adi}",
            uyari = not yeterli and not zorunlu,
        )
    except ImportError:
        return KontrolSonucu(
            ad    = pip_adi,
            tamam = not zorunlu,
            mesaj = f"Kurulu değil  →  pip install {pip_adi}>={min_surum}",
            uyari = not zorunlu,
        )


# ── 8. Sistem komutu varlığı ──────────────────────────────────────────────────
SISTEM_KOMUTLARI: list[tuple[str, bool]] = [
    ("git",    False),   # (komut, zorunlu mu)
    ("python", True),
    ("pip",    True),
]


def komut_kontrol(komut: str, zorunlu: bool = True) -> KontrolSonucu:
    yol = shutil.which(komut)
    tamam = yol is not None
    return KontrolSonucu(
        ad    = f"Komut: {komut}",
        tamam = tamam or not zorunlu,
        mesaj = yol if tamam else f"'{komut}' PATH'te bulunamadı",
        uyari = not tamam and not zorunlu,
    )


# ── 9. Proje dosyası varlığı ──────────────────────────────────────────────────
PROJE_DOSYALARI: list[tuple[str, bool]] = [
    ("main.py",              True),
    ("controller.py",        True),
    ("requirements_api.txt", True),
    ("system.ps1",           False),
    ("run.bat",              False),
    (".env",                 False),
    ("templates/index.html", False),
    ("static/app.js",        False),
]


def dosya_kontrol(yol_str: str, zorunlu: bool = True) -> KontrolSonucu:
    yol   = Path(yol_str)
    mevcut = yol.exists()
    boyut  = f"{yol.stat().st_size:,} B" if mevcut else "—"
    return KontrolSonucu(
        ad    = yol_str,
        tamam = mevcut or not zorunlu,
        mesaj = (f"Mevcut  ({boyut})" if mevcut
                 else ("Eksik — oluşturulmalı" if zorunlu else "Mevcut değil (opsiyonel)")),
        uyari = not mevcut and not zorunlu,
    )


# ── 10. Port erişilebilirlik kontrolü ─────────────────────────────────────────
def port_kontrol(port: int = 5000) -> KontrolSonucu:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        sonuc = s.connect_ex(("127.0.0.1", port))
    kullanımda = sonuc == 0
    return KontrolSonucu(
        ad    = f"Port {port}",
        tamam = not kullanımda,
        mesaj = (f"Port {port} kullanımda — başka bir uygulama çalışıyor olabilir"
                 if kullanımda else f"Port {port} boş ve kullanılabilir"),
        uyari = kullanımda,
    )


# ═════════════════════════════════════════════════════════════════════════════
# OTOMATİK KURULUM
# ═════════════════════════════════════════════════════════════════════════════

def paket_kur(pip_adi: str, min_surum: str) -> bool:
    """Eksik paketi pip ile kurar. True → başarılı."""
    hedef = f"{pip_adi}>={min_surum}"
    print(f"  {Y}↓ Kuruluyor: {hedef}{X}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", hedef, "-q"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            print(f"  {G}✓ Kuruldu: {pip_adi}{X}")
            return True
        print(f"  {R}✗ Kurulamadı: {result.stderr.strip()[:200]}{X}")
        return False
    except Exception as e:
        print(f"  {R}✗ Hata: {e}{X}")
        return False


# ═════════════════════════════════════════════════════════════════════════════
# RAPOR YAZICI
# ═════════════════════════════════════════════════════════════════════════════

SEP  = "─" * 66
SEP2 = "═" * 66
GEN  = 34   # ad sütunu genişliği


def baslik_yaz(metin: str) -> None:
    print(f"\n{renkli(metin, B + BOLD)}")
    print(renkli(SEP, D))


def satir_yaz(sonuc: KontrolSonucu, quiet: bool = False) -> None:
    if quiet and sonuc.tamam and not sonuc.uyari:
        return
    ad_pad = f"{sonuc.ad:<{GEN}}"
    print(f"  {sonuc.sembol}  {ad_pad}  {sonuc.etiket}  {D}{sonuc.mesaj}{X}")
    if sonuc.detay and not quiet:
        print(f"     {D}{'':>{GEN+2}}  {sonuc.detay}{X}")


def ozet_yaz(sonuclar: list[KontrolSonucu]) -> None:
    print(f"\n{renkli(SEP2, D)}")
    toplam  = len(sonuclar)
    gecti   = sum(1 for s in sonuclar if s.tamam and not s.uyari)
    uyari   = sum(1 for s in sonuclar if s.uyari)
    basarisiz = toplam - gecti - uyari

    durum   = (renkli("TÜM KONTROLLER GEÇTİ", G + BOLD)
               if basarisiz == 0
               else renkli(f"{basarisiz} KONTROL BAŞARISIZ", R + BOLD))
    print(f"  {durum}")
    print(f"  {G}✓{X} {gecti}  {Y}⚠{X} {uyari}  {R}✗{X} {basarisiz}  (toplam {toplam})")
    print(renkli(SEP2, D))


# ═════════════════════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═════════════════════════════════════════════════════════════════════════════

def tum_kontrolleri_calistir() -> list[KontrolSonucu]:
    sonuclar: list[KontrolSonucu] = []

    # Python & platform
    sonuclar.append(python_surum_kontrol(min_surum=(3, 10)))
    sonuclar.append(isletim_sistemi_kontrol())
    sonuclar.append(disk_alani_kontrol(min_mb=200))
    sonuclar.append(ram_kontrol(min_mb=256))

    # Araçlar
    for komut, zorunlu in SISTEM_KOMUTLARI:
        sonuclar.append(komut_kontrol(komut, zorunlu))
    sonuclar.append(pip_kontrol())
    sonuclar.append(sanal_ortam_kontrol())

    # Zorunlu paketler
    for imp, pip, min_v in GEREKLI_PAKETLER:
        sonuclar.append(paket_kontrol(imp, pip, min_v, zorunlu=True))

    # Opsiyonel paketler
    for imp, pip, min_v in OPSIYONEL_PAKETLER:
        sonuclar.append(paket_kontrol(imp, pip, min_v, zorunlu=False))

    # Proje dosyaları
    for yol, zorunlu in PROJE_DOSYALARI:
        sonuclar.append(dosya_kontrol(yol, zorunlu))

    # Port
    sonuclar.append(port_kontrol(5000))
    sonuclar.append(port_kontrol(8000))

    return sonuclar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sistem gereksinim kontrolü")
    parser.add_argument("--json",  action="store_true", help="JSON çıktı")
    parser.add_argument("--quiet", action="store_true", help="Yalnızca hata/uyarılar")
    parser.add_argument("--fix",   action="store_true", help="Eksik paketleri otomatik kur")
    args = parser.parse_args(argv)

    if not args.json:
        print(f"\n{renkli(SEP2, C)}")
        print(f"  {renkli('SİSTEM GEREKSİNİM KONTROLÜ', C + BOLD)}")
        print(f"  {D}FlaskDjango App · {platform.node()} · {platform.system()}{X}")
        print(renkli(SEP2, C))

    sonuclar = tum_kontrolleri_calistir()

    if args.fix:
        print(f"\n{renkli('── Otomatik Kurulum ──', Y + BOLD)}")
        for imp, pip, min_v in GEREKLI_PAKETLER:
            s = paket_kontrol(imp, pip, min_v)
            if not s.tamam:
                paket_kur(pip, min_v)

    if args.json:
        print(json.dumps([s.to_dict() for s in sonuclar], ensure_ascii=False, indent=2))
        return 0 if all(s.tamam for s in sonuclar) else 1

    # ── Gruplu rapor ──────────────────────────────────────────────────────────
    gruplar = [
        ("Platform",             sonuclar[:4]),
        ("Sistem Araçları",      sonuclar[4:7]),
        ("Zorunlu Paketler",     sonuclar[7:7+len(GEREKLI_PAKETLER)]),
        ("Opsiyonel Paketler",   sonuclar[7+len(GEREKLI_PAKETLER):
                                          7+len(GEREKLI_PAKETLER)+len(OPSIYONEL_PAKETLER)]),
        ("Proje Dosyaları",      sonuclar[-(len(PROJE_DOSYALARI)+2):-2]),
        ("Ağ / Port",            sonuclar[-2:]),
    ]

    for grup_adi, grup_sonuclari in gruplar:
        baslik_yaz(grup_adi)
        for s in grup_sonuclari:
            satir_yaz(s, quiet=args.quiet)

    ozet_yaz(sonuclar)

    return 0 if all(s.tamam for s in sonuclar) else 1


if __name__ == "__main__":
    sys.exit(main())