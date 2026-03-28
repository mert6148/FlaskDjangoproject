"""
main.py — Uygulama Giriş Noktası
Düzeltmeler:
  - 'import mac_ver(...)' geçersiz ifade kaldırıldı
  - socket/struct import eksiklikleri eklendi
  - ProxyBasicAuthHandler / as_completed anlamsız gövde temizlendi
  - xmlcharrefreplace_errors yanlış kullanımı düzeltildi
"""

import os
import sys
import socket
import struct
from controller import AppController


# ── Yardımcı fonksiyonlar ─────────────────────────────────────────────────────

def v4_int_to_packed(address: int) -> str:
    """32-bit integer IPv4 adresini noktalı dört bölümlü stringe çevirir."""
    return socket.inet_ntoa(struct.pack("!I", address))


def platform_bilgisi() -> dict:
    """Çalışma zamanı platform bilgilerini döndürür."""
    import platform
    return {
        "sistem":   platform.system(),
        "surum":    platform.version(),
        "python":   platform.python_version(),
        "mimari":   platform.machine(),
    }


# ── Ana sınıf ─────────────────────────────────────────────────────────────────

class Main:
    """Uygulama başlatıcı."""

    def __init__(self):
        self.ctrl = AppController(ad="FlaskDjango App", surum="1.0.0")

    def calistir(self) -> None:
        self.ctrl.main()
        bilgi = platform_bilgisi()
        for k, v in bilgi.items():
            print(f"  {k:<10}: {v}")


if __name__ == "__main__":
    Main().calistir()