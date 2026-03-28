import os
import base64
import hashlib

# ── C/C++ uzantı setleri ──────────────────────────────────────────────────────
C_CPP_HEADER_EXTENSIONS = {'.h', '.hpp', '.hxx'}
C_CPP_SOURCE_EXTENSIONS = {'.c', '.cpp', '.cxx'}
C_CPP_ALL_EXTENSIONS    = C_CPP_HEADER_EXTENSIONS | C_CPP_SOURCE_EXTENSIONS

# ── C/C++ dosya türü tespiti ──────────────────────────────────────────────────
def is_c_cpp_makefile(file_path: str) -> bool:
    return os.path.basename(file_path).lower() == 'makefile'

def is_c_cpp_header(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() in C_CPP_HEADER_EXTENSIONS

def is_c_cpp_source(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() in C_CPP_SOURCE_EXTENSIONS

def is_c_sharp_source(file_path: str) -> bool:
    _, ext = os.path.splitext(file_path)
    return ext.lower() == '.cs'

# ── base64 yardımcıları ───────────────────────────────────────────────────────
def a2b_base64(string: str) -> bytes:
    """base64 string → bytes dönüşümü."""
    return base64.b64decode(string)

def b2a_base64(data: bytes) -> str:
    """bytes → base64 string dönüşümü."""
    return base64.b64encode(data).decode('utf-8')

# ── Dosya karşılaştırma ───────────────────────────────────────────────────────
def sameopenfile(fp1, fp2) -> bool:
    """İki dosya nesnesinin aynı dosyayı gösterip göstermediğini kontrol eder."""
    try:
        return os.path.samefile(fp1.name, fp2.name)
    except (AttributeError, OSError):
        return False