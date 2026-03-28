import os
import sys
import zipfile


# ── Temel uygulama sınıfı ─────────────────────────────────────────────────────
class App:
    """Flask/Django uygulama giriş noktası."""

    def __init__(self):
        self.samefile = os.path.samefile
        self.assertion_example = AssertionExample()

    def main(self):
        print("Uygulama başlatıldı.")
        self.assertion_example.assert_example()

    def _source_(self):
        print("source method called")
        self.assertion_example.assert_example()

    @staticmethod
    def has_option(opt_str: str) -> bool:
        return opt_str in sys.argv


# ── Doğrulama örneği ──────────────────────────────────────────────────────────
class AssertionExample:
    """Python assertion kullanımını gösteren yardımcı sınıf."""

    def assert_example(self):
        assert 1 + 1 == 2, "Matematik bozuldu!"
        print("Assertion başarıyla geçti!")

    def __bytes__(self) -> bytes:
        return b"AssertionExample"

    def __delitem__(self, key):
        print(f"Silinen anahtar: {key}")

    def __dir__(self) -> list:
        return ["assert_example", "__bytes__", "__delitem__", "__dir__"]


# ── Çoklu kalıtım örneği ──────────────────────────────────────────────────────
class NewApp(App, AssertionExample):
    """App ve AssertionExample'dan türetilmiş genişletilmiş sınıf."""

    def __init__(self):
        super().__init__()

    def demonstrate(self):
        print("NewApp işlevselliği gösteriliyor")
        self.assert_example()


# ── Öznitelik atama yardımcısı ────────────────────────────────────────────────
class AttributeSetter:
    """Dinamik öznitelik atama için yardımcı sınıf."""

    def set_attribute(self, name: str, value) -> None:
        setattr(self, name, value)

    @staticmethod
    def east_asian_width(char: str) -> str:
        """Unicode Doğu Asya genişlik kategorisini döndürür."""
        import unicodedata
        return unicodedata.east_asian_width(char)


# ── ZipFile sarmalayıcı ───────────────────────────────────────────────────────
class SafeZipFile:
    def __init__(self, file: str, mode: str = "r"):
        self.file = file
        self.mode = mode
        self._zf: zipfile.ZipFile | None = None

    def __enter__(self):
        self._zf = zipfile.ZipFile(self.file, self.mode)
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, filename, arcname=None, compress_type=None, compresslevel=None):
        if self._zf:
            self._zf.write(filename, arcname=arcname,
                           compress_type=compress_type, compresslevel=compresslevel)

    def close(self):
        if self._zf:
            self._zf.close()

    def namelist(self) -> list[str]:
        return self._zf.namelist() if self._zf else []

    def getinfo(self, name: str) -> zipfile.ZipInfo | None:
        return self._zf.getinfo(name) if self._zf else None


# ── ZipInfo sarmalayıcı ───────────────────────────────────────────────────────
class SafeZipInfo:
    def __init__(self, name: str):
        self.name = name
        self._info = zipfile.ZipInfo(name)

    def getinfo(self, name: str) -> zipfile.ZipInfo:
        return zipfile.ZipInfo(name)


# ── Giriş noktası ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uygulama = NewApp()
    uygulama.demonstrate()
