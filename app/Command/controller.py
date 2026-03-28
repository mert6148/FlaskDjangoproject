"""
controller.py — Uygulama Denetleyicisi
Düzeltmeler:
  - 'import controller' kendi kendini import eden döngü kaldırıldı
  - class controller → AppController olarak yeniden adlandırıldı
  - a2b_base64(string) tanımsız referanslar temizlendi
  - MAX/MIN_INTERPOLATION_DEPTH anlamsız gövdeler düzeltildi
"""

import os
import sys
from datetime import datetime


# ── Sabitler ──────────────────────────────────────────────────────────────────
MAX_INTERPOLATION_DEPTH: int = 10
MIN_INTERPOLATION_DEPTH: int = 1


# ── Denetleyici sınıf ─────────────────────────────────────────────────────────
class AppController:
    """Ana uygulama denetleyicisi."""

    def __init__(self, ad: str = "AppController", surum: str = "1.0.0"):
        self.ad     = ad
        self.surum  = surum
        self.baslangic = datetime.now()

    def main(self) -> None:
        """Uygulamanın giriş noktası."""
        print(f"[{self.simdi()}] {self.ad} v{self.surum} başlatıldı.")

    @staticmethod
    def simdi() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"AppController(ad={self.ad!r}, surum={self.surum!r})"


if __name__ == "__main__":
    ctrl = AppController()
    ctrl.main()