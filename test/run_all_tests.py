#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ana Test Koşucusu — FlaskDjango Projesi
Tüm API test suite'lerini tek komutla çalıştırır.

Kullanım:
  python run_all_tests.py            # tüm testler
  python run_all_tests.py --flask    # sadece Flask
  python run_all_tests.py --django   # sadece Django
  python run_all_tests.py --shared   # şema/güvenlik/entegrasyon
  python run_all_tests.py --json     # JSON raporu
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# ── Suite yükleyiciler ────────────────────────────────────────────────────────
def load_flask_suite() -> unittest.TestSuite:
    from test_api_flask import (
        TestFlaskHealth,
        TestKullaniciListele,
        TestKullaniciOlustur,
        TestKullaniciGetir,
        TestKullaniciGuncelle,
        TestKullaniciSil,
        TestUrunListele,
        TestUrunOlustur,
    )
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestFlaskHealth, TestKullaniciListele, TestKullaniciOlustur,
        TestKullaniciGetir, TestKullaniciGuncelle, TestKullaniciSil,
        TestUrunListele, TestUrunOlustur,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


def load_django_suite() -> unittest.TestSuite:
    from test_api_django import (
        TestKategoriListCreate, TestKategoriDetail,
        TestUrunListCreate, TestUrunActions, TestDjangoHeaders,
    )
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestKategoriListCreate, TestKategoriDetail,
        TestUrunListCreate, TestUrunActions, TestDjangoHeaders,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


def load_shared_suite() -> unittest.TestSuite:
    from test_api_shared import (
        TestFlaskResponseSchema, TestFlaskSecurity,
        TestEmailValidation, TestSystemJsonIntegrity, TestFlaskSystemIntegration,
    )
    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()
    for cls in [
        TestFlaskResponseSchema, TestFlaskSecurity, TestEmailValidation,
        TestSystemJsonIntegrity, TestFlaskSystemIntegration,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    return suite


# ── Çalıştırıcı ───────────────────────────────────────────────────────────────
def run_suite(
    suite: unittest.TestSuite,
    label: str,
    verbose: bool = True,
) -> dict:
    """Suite'i çalıştırır; özet sözlük döndürür."""
    buf    = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=2 if verbose else 1)

    start   = time.monotonic()
    result  = runner.run(suite)
    elapsed = time.monotonic() - start

    output = buf.getvalue()
    if verbose:
        print(output)

    return {
        "suite":   label,
        "total":   result.testsRun,
        "passed":  result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
        "failed":  len(result.failures),
        "errors":  len(result.errors),
        "skipped": len(result.skipped),
        "elapsed": round(elapsed, 3),
        "success": result.wasSuccessful(),
        "failures": [
            {"test": str(tc), "message": msg}
            for tc, msg in result.failures + result.errors
        ],
    }


# ── Raporlama ──────────────────────────────────────────────────────────────────
SEP   = "─" * 70
SEP2  = "═" * 70

RENK  = {
    "green":  "\033[92m",
    "red":    "\033[91m",
    "yellow": "\033[93m",
    "cyan":   "\033[96m",
    "bold":   "\033[1m",
    "reset":  "\033[0m",
}

def clr(text: str, *keys: str) -> str:
    codes = "".join(RENK.get(k, "") for k in keys)
    return f"{codes}{text}{RENK['reset']}"


def print_summary(results: list[dict]) -> None:
    print(f"\n{SEP2}")
    print(clr("  TEST SONUÇ RAPORU", "bold", "cyan"))
    print(SEP2)
    print(f"  {'Suite':<30} {'Toplam':>7} {'Geçti':>7} {'Başarısız':>10} {'Hata':>6} {'Atlandı':>8} {'Süre':>8}")
    print(SEP)

    grand_total = grand_pass = grand_fail = grand_err = grand_skip = 0

    for r in results:
        ok    = r["success"]
        sym   = clr("✓", "green") if ok else clr("✗", "red")
        label = clr(r["suite"], "green" if ok else "red")
        print(
            f"  {sym} {label:<28} "
            f"{r['total']:>7} {r['passed']:>7} "
            f"{r['failed']:>10} {r['errors']:>6} "
            f"{r['skipped']:>8} {r['elapsed']:>7.2f}s"
        )
        grand_total += r["total"]
        grand_pass  += r["passed"]
        grand_fail  += r["failed"]
        grand_err   += r["errors"]
        grand_skip  += r["skipped"]

    print(SEP)
    all_ok = all(r["success"] for r in results)
    total_label = clr("TOPLAM", "bold", "green" if all_ok else "red")
    print(
        f"  {total_label:<30} "
        f"{grand_total:>7} {grand_pass:>7} "
        f"{grand_fail:>10} {grand_err:>6} {grand_skip:>8}"
    )
    print(SEP2)

    # Başarısızlık detayları
    any_fail = any(r["failures"] for r in results)
    if any_fail:
        print(clr("\n  BAŞARISIZ TESTLER:", "bold", "red"))
        for r in results:
            for f in r["failures"]:
                print(f"\n  [{r['suite']}] {f['test']}")
                for line in f["message"].splitlines()[:6]:
                    print(f"    {line}")

    verdict = (
        clr("\n  ✓  TÜM TESTLER BAŞARILI", "bold", "green")
        if all_ok
        else clr(f"\n  ✗  {grand_fail + grand_err} TEST BAŞARISIZ", "bold", "red")
    )
    print(verdict)
    print(SEP2 + "\n")


# ── CLI ───────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="FlaskDjango API Test Koşucusu")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--flask",  action="store_true", help="Sadece Flask testleri")
    g.add_argument("--django", action="store_true", help="Sadece Django testleri")
    g.add_argument("--shared", action="store_true", help="Şema/güvenlik/entegrasyon testleri")
    p.add_argument("--json",   action="store_true", help="JSON raporu yaz (test_results.json)")
    p.add_argument("--quiet",  action="store_true", help="Ayrıntısız çıktı")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv or sys.argv[1:])

    suites: list[tuple[str, unittest.TestSuite]] = []

    if args.flask:
        suites = [("Flask API", load_flask_suite())]
    elif args.django:
        suites = [("Django REST", load_django_suite())]
    elif args.shared:
        suites = [("Şema/Güvenlik/Entegrasyon", load_shared_suite())]
    else:
        suites = [
            ("Flask API",                   load_flask_suite()),
            ("Django REST",                 load_django_suite()),
            ("Şema/Güvenlik/Entegrasyon",   load_shared_suite()),
        ]

    print(f"\n{SEP2}")
    print(clr("  FLASKDJANGO API TEST SUITE", "bold", "cyan"))
    print(clr(f"  {len(suites)} suite çalıştırılıyor...", "cyan"))
    print(SEP2)

    results = []
    for label, suite in suites:
        print(f"\n{clr(f'▶  {label}', 'bold', 'cyan')}")
        print(SEP)
        results.append(run_suite(suite, label, verbose=not args.quiet))

    print_summary(results)

    if args.json:
        out_path = ROOT / "test_results.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  JSON raporu kaydedildi → {out_path}\n")

    return 0 if all(r["success"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
