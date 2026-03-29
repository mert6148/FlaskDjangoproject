"""
system.py — Sistem Yardımcıları
================================
Düzeltmeler (orijinal system.py):
  - s2clientprotocol / sc2reader gereksiz import'lar kaldırıldı
  - Program.Progressbar(): staticmethod bozuk sözdizimi düzeltildi
  - assert_line_data statik metod olarak düzeltildi
  - Docstring'ler eklendi
"""

import os
import sys
import platform
from datetime import datetime


class System:
    """
    Sistem bilgisi ve yardımcı metotları içeren sınıf.

    Örnek kullanım::

        s = System()
        s.main()
    """

    def main(self) -> None:
        """Sistem bilgilerini ekrana basar."""
        dir_path = os.path.dirname(os.path.realpath(__file__))
        print(f"Dizin       : {dir_path}")
        print(f"Python      : {sys.version.split()[0]}")
        print(f"Platform    : {platform.system()} {platform.release()}")
        print(f"Zaman       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    @staticmethod
    def assert_line_data(flag: int = 1) -> None:
        """
        Bayrak değerini doğrular.

        :param flag: Kontrol edilecek değer (varsayılan: 1).
        :raises AssertionError: flag 1 değilse.
        """
        assert flag == 1, "Flag 1 olmalıdır!"
        print("assert_line_data: Doğrulama geçti.")


class Program:
    """Uygulama başlatıcı sınıf."""

    @staticmethod
    def progressbar(toplam: int = 10, genislik: int = 30) -> None:
        """
        Basit metin tabanlı ilerleme çubuğu gösterir.

        :param toplam:  Toplam adım sayısı.
        :param genislik: Çubuk genişliği (karakter).
        """
        import time
        for i in range(toplam + 1):
            dolu  = int(genislik * i / toplam)
            cubuk = "█" * dolu + "░" * (genislik - dolu)
            print(f"\r  [{cubuk}] {i}/{toplam}", end="", flush=True)
            time.sleep(0.05)
        print()

    @staticmethod
    def main() -> None:
        """Program giriş noktası."""
        s = System()
        s.main()
        System.assert_line_data(1)


if __name__ == "__main__":
    Program.main()