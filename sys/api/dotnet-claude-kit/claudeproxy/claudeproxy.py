"""
claude_proxy.py — Python 3 Claude Proxy Güvenlik Katmanı
=========================================================
Flask tabanlı Python proxy sunucusu.
C# proxy ile birlikte veya bağımsız olarak çalışır.

Özellikler:
  - AES-256-GCM istek/yanıt şifreleme
  - JWT kimlik doğrulama
  - Rate limiting (sliding window)
  - Prompt enjeksiyon koruması
  - JSON şema doğrulaması
  - Denetim kayıt sistemi
  - IP kara/beyaz listesi

Kurulum:
  pip install flask flask-limiter PyJWT cryptography httpx python-dotenv
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import uuid
from base64 import b64decode, b64encode
from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Flask, jsonify, request, g
import jwt

# ─────────────────────────────────────────────────────────────────────────────
# YAPILANDIRMA
# ─────────────────────────────────────────────────────────────────────────────

class ProxyConfig:
    """Proxy yapılandırma sabitleri — ortam değişkenlerinden yüklenir."""

    CLAUDE_API_URL:    str  = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/messages")
    CLAUDE_API_KEY:    str  = os.getenv("CLAUDE_API_KEY", "")
    JWT_SECRET:        str  = os.getenv("JWT_SECRET", secrets.token_hex(32))
    JWT_ALGORITHM:     str  = "HS256"
    JWT_EXPIRY_SEC:    int  = int(os.getenv("JWT_EXPIRY_SEC", "3600"))
    ENC_KEY:           bytes = (
        b64decode(os.getenv("ENC_KEY", ""))
        if os.getenv("ENC_KEY")
        else secrets.token_bytes(32)
    )
    RATE_PER_MINUTE:   int  = int(os.getenv("RATE_PER_MINUTE", "20"))
    RATE_PER_HOUR:     int  = int(os.getenv("RATE_PER_HOUR", "200"))
    MAX_PROMPT_LEN:    int  = int(os.getenv("MAX_PROMPT_LEN", "8000"))
    ENABLE_ENCRYPTION: bool = os.getenv("ENABLE_ENCRYPTION", "true").lower() == "true"
    ENABLE_AUDIT:      bool = os.getenv("ENABLE_AUDIT", "true").lower() == "true"
    ALLOWED_IPS:       list = json.loads(os.getenv("ALLOWED_IPS", "[]"))
    BLOCKED_IPS:       list = json.loads(os.getenv("BLOCKED_IPS", "[]"))
    ALLOWED_ORIGINS:   list = json.loads(os.getenv("ALLOWED_ORIGINS",
                                                    '["http://localhost:3000"]'))
    DEFAULT_MODEL:     str  = "claude-sonnet-4-20250514"


# ─────────────────────────────────────────────────────────────────────────────
# LOGLAMA
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger     = logging.getLogger("claude.proxy")
audit_log  = logging.getLogger("claude.audit")


# ─────────────────────────────────────────────────────────────────────────────
# ŞİFRELEME SERVİSİ
# ─────────────────────────────────────────────────────────────────────────────

class EncryptionService:
    """
    AES-256-GCM ile simetrik şifreleme.

    Şifreli format: base64(nonce[12] + şifreli + tag[16])
    """

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("Şifreleme anahtarı tam olarak 32 byte olmalıdır.")
        self._aesgcm = AESGCM(key)

    def encrypt(self, plaintext: str) -> str:
        """Metni AES-256-GCM ile şifreler. Döndürür: base64 string."""
        nonce  = secrets.token_bytes(12)
        cipher = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return b64encode(nonce + cipher).decode("utf-8")

    def decrypt(self, encrypted_b64: str) -> str:
        """base64 şifreli metni çözer."""
        data   = b64decode(encrypted_b64)
        nonce  = data[:12]
        cipher = data[12:]
        plain  = self._aesgcm.decrypt(nonce, cipher, None)
        return plain.decode("utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# RATE LIMITER
# ─────────────────────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Sliding window rate limiter.

    İstek geçmişi belleğe alınır; production için Redis kullanın.
    """

    def __init__(self, per_minute: int, per_hour: int) -> None:
        self._per_minute = per_minute
        self._per_hour   = per_hour
        self._windows: dict[str, deque[float]] = defaultdict(deque)

    def try_acquire(self, key: str) -> bool:
        """
        Anahtarın rate limit dahilinde olup olmadığını kontrol eder.

        :returns: True → istek kabul edilebilir
        """
        now    = time.monotonic()
        hits   = self._windows[key]

        # 1 saatten eski girişleri temizle
        while hits and now - hits[0] > 3600:
            hits.popleft()

        per_hour   = len(hits)
        per_minute = sum(1 for t in hits if now - t < 60)

        if per_hour >= self._per_hour or per_minute >= self._per_minute:
            return False

        hits.append(now)
        return True

    def get_usage(self, key: str) -> dict:
        now  = time.monotonic()
        hits = self._windows.get(key, deque())
        return {
            "per_minute": sum(1 for t in hits if now - t < 60),
            "per_hour":   len(hits),
        }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT KORUMASI
# ─────────────────────────────────────────────────────────────────────────────

class PromptGuard:
    """
    Prompt enjeksiyon ve kötüye kullanım koruması.

    Örüntüler:
      - Sistem prompt manipülasyonu
      - Jailbreak girişimleri
      - Zararlı içerik kategorileri
    """

    INJECTION_PATTERNS: list[re.Pattern] = [
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.I),
        re.compile(r"system\s+prompt",                            re.I),
        re.compile(r"\bjailbreak\b",                              re.I),
        re.compile(r"\bDAN\s+mode\b",                             re.I),
        re.compile(r"pretend\s+you\s+(are|have\s+no)",            re.I),
        re.compile(r"forget\s+(all\s+)?your\s+(rules?|guidelines?|restrictions?)", re.I),
        re.compile(r"act\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(?:evil|unrestricted|unfiltered)", re.I),
        re.compile(r"\[INST\]|\[\/INST\]|<\|im_start\|>|<\|im_end\|>", re.I),
    ]

    CONTENT_PATTERNS: list[re.Pattern] = [
        re.compile(r"\b(bomb|weapon|explosive)\s+(make|build|create|instructions?)\b", re.I),
        re.compile(r"\b(malware|ransomware|virus)\s+(code|create|write)\b",            re.I),
    ]

    def inspect(self, prompt: str) -> tuple[bool, str | None]:
        """
        Prompt'u güvenlik açısından inceler.

        :returns: (temiz_mi, hata_mesajı)
        """
        if not prompt or not prompt.strip():
            return False, "Prompt boş olamaz."

        for pattern in self.INJECTION_PATTERNS:
            if pattern.search(prompt):
                return False, "Prompt enjeksiyon girişimi tespit edildi."

        for pattern in self.CONTENT_PATTERNS:
            if pattern.search(prompt):
                return False, "İzin verilmeyen içerik kategorisi."

        return True, None


# ─────────────────────────────────────────────────────────────────────────────
# JSON ŞEMA DOĞRULAMASI
# ─────────────────────────────────────────────────────────────────────────────

# İstek şeması (schema/proxy_request.schema.json ile senkronize)
REQUEST_SCHEMA: dict = {
    "required":   ["prompt"],
    "properties": {
        "prompt":       {"type": str,   "min": 1,    "max": 8000},
        "model":        {"type": str,   "optional": True},
        "max_tokens":   {"type": int,   "min": 1,    "max": 8192, "optional": True},
        "is_encrypted": {"type": bool,  "optional": True},
        "system":       {"type": str,   "optional": True},
    }
}


def validate_request_json(data: dict) -> tuple[bool, str | None]:
    """
    Gelen JSON verisini şema açısından doğrular.

    :returns: (geçerli_mi, hata_mesajı)
    """
    if not isinstance(data, dict):
        return False, "İstek gövdesi JSON nesnesi olmalıdır."

    for field in REQUEST_SCHEMA["required"]:
        if field not in data:
            return False, f"'{field}' alanı zorunludur."

    for field, rules in REQUEST_SCHEMA["properties"].items():
        if field not in data:
            continue
        val = data[field]
        if not isinstance(val, rules["type"]):
            return False, f"'{field}' türü {rules['type'].__name__} olmalıdır."
        if "min" in rules and isinstance(val, (str, int)):
            if (len(val) if isinstance(val, str) else val) < rules["min"]:
                return False, f"'{field}' min {rules['min']} olmalıdır."
        if "max" in rules and isinstance(val, (str, int)):
            if (len(val) if isinstance(val, str) else val) > rules["max"]:
                return False, f"'{field}' max {rules['max']} olmalıdır."

    return True, None


# ─────────────────────────────────────────────────────────────────────────────
# JWT ARAÇLARI
# ─────────────────────────────────────────────────────────────────────────────

def generate_token(user_id: str, role: str = "user") -> str:
    """JWT token üretir."""
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + ProxyConfig.JWT_EXPIRY_SEC,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, ProxyConfig.JWT_SECRET,
                      algorithm=ProxyConfig.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Token'ı doğrular ve payload'ı döndürür."""
    try:
        return jwt.decode(token, ProxyConfig.JWT_SECRET,
                          algorithms=[ProxyConfig.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# FLASK UYGULAMASI
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)

# Servis örnekleri
_enc         = EncryptionService(ProxyConfig.ENC_KEY)
_rate        = RateLimiter(ProxyConfig.RATE_PER_MINUTE, ProxyConfig.RATE_PER_HOUR)
_guard       = PromptGuard()


# ── Decorator'lar ─────────────────────────────────────────────────────────────

def jwt_required(f):
    """JWT kimlik doğrulama decorator'ı."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Yetkilendirme başlığı eksik."}), 401
        payload = decode_token(auth.split(" ", 1)[1])
        if not payload:
            return jsonify({"error": "Geçersiz veya süresi dolmuş token."}), 401
        g.user_id = payload["sub"]
        g.role    = payload.get("role", "user")
        return f(*args, **kwargs)
    return wrapped


def ip_guard(f):
    """IP kara/beyaz liste kontrolü."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        if ip in ProxyConfig.BLOCKED_IPS:
            audit_log.warning("[BLOCKED] IP=%s reason=kara_liste", ip)
            return jsonify({"error": "Erişim reddedildi."}), 403
        if ProxyConfig.ALLOWED_IPS and ip not in ProxyConfig.ALLOWED_IPS:
            audit_log.warning("[BLOCKED] IP=%s reason=beyaz_liste_disi", ip)
            return jsonify({"error": "Erişim reddedildi."}), 403
        return f(*args, **kwargs)
    return wrapped


def rate_limit(f):
    """Rate limiting decorator'ı."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        key = getattr(g, "user_id", None) or request.remote_addr or "unknown"
        if not _rate.try_acquire(key):
            audit_log.warning("[RATE_LIMIT] key=%s", key)
            return jsonify({"error": "Çok fazla istek. Lütfen bekleyin."}), 429
        return f(*args, **kwargs)
    return wrapped


def add_security_headers(response):
    """Güvenlik HTTP başlıklarını ekler."""
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Content-Security-Policy"]   = "default-src 'self'"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"]             = "no-store"
    response.headers.pop("Server", None)
    return response


app.after_request(add_security_headers)


# ── ENDPOINT'LER ──────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """GET /health — Sağlık kontrolü."""
    return jsonify({"status": "ok", "version": "1.0.0",
                    "timestamp": datetime.now(timezone.utc).isoformat()})


@app.post("/auth/token")
def auth_token():
    """
    POST /auth/token — JWT token al.

    Body: {"username": "...", "password": "..."}
    """
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    # Gerçek uygulamada veritabanı doğrulaması
    if username == "admin" and password == "changeme":
        token = generate_token(username, role="admin")
        return jsonify({"token": token, "expires_in": ProxyConfig.JWT_EXPIRY_SEC})

    audit_log.warning("[AUTH_FAIL] user=%s", username)
    return jsonify({"error": "Geçersiz kimlik bilgileri."}), 401


@app.post("/proxy/chat")
@ip_guard
@jwt_required
@rate_limit
def proxy_chat():
    """
    POST /proxy/chat — Ana proxy endpoint'i.

    Headers:
        Authorization: Bearer <token>
        Content-Type: application/json

    Body::

        {
          "prompt":       "Merhaba Claude!",
          "model":        "claude-sonnet-4-20250514",   (opsiyonel)
          "max_tokens":   1024,                          (opsiyonel)
          "is_encrypted": false,                         (opsiyonel)
          "system":       "Sen yardımsever bir asistansın." (opsiyonel)
        }

    Yanıt::

        {
          "success":      true,
          "content":      "...",
          "is_encrypted": true/false,
          "input_tokens": 10,
          "output_tokens": 50
        }
    """
    request_id = uuid.uuid4().hex[:12]
    ip         = request.remote_addr or "unknown"
    user_id    = g.user_id
    t0         = time.perf_counter()

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Geçersiz JSON gövdesi."}), 400

    # JSON şema doğrulaması
    valid, err = validate_request_json(data)
    if not valid:
        return jsonify({"error": err}), 400

    # Prompt hazırla (şifreli ise çöz)
    prompt       = data["prompt"]
    is_encrypted = data.get("is_encrypted", False)
    if is_encrypted and ProxyConfig.ENABLE_ENCRYPTION:
        try:
            prompt = _enc.decrypt(prompt)
        except Exception:
            return jsonify({"error": "Şifre çözme başarısız."}), 400

    # Uzunluk kontrolü
    if len(prompt) > ProxyConfig.MAX_PROMPT_LEN:
        return jsonify({"error": f"Prompt çok uzun. Max: {ProxyConfig.MAX_PROMPT_LEN}"}), 400

    # Güvenlik kontrolü
    clean, reason = _guard.inspect(prompt)
    if not clean:
        audit_log.warning("[BLOCKED] rid=%s ip=%s reason=%s", request_id, ip, reason)
        return jsonify({"error": reason}), 422

    if ProxyConfig.ENABLE_AUDIT:
        audit_log.info("[REQ] rid=%s ip=%s user=%s len=%d enc=%s",
                       request_id, ip, user_id, len(prompt), is_encrypted)

    # Claude API isteği
    payload = {
        "model":      data.get("model", ProxyConfig.DEFAULT_MODEL),
        "max_tokens": data.get("max_tokens", 1024),
        "messages":   [{"role": "user", "content": prompt}],
    }
    if system := data.get("system"):
        payload["system"] = system

    headers = {
        "x-api-key":         ProxyConfig.CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(ProxyConfig.CLAUDE_API_URL,
                               json=payload, headers=headers)

        duration_ms = (time.perf_counter() - t0) * 1000

        if resp.status_code != 200:
            logger.error("[CLAUDE_ERR] %d: %s", resp.status_code, resp.text[:200])
            return jsonify({"error": "Claude API hatası."}), resp.status_code

        result        = resp.json()
        content       = result["content"][0]["text"]
        input_tokens  = result["usage"]["input_tokens"]
        output_tokens = result["usage"]["output_tokens"]

        if ProxyConfig.ENABLE_AUDIT:
            audit_log.info("[RES] rid=%s status=200 out_tok=%d ms=%.1f",
                           request_id, output_tokens, duration_ms)

        # Yanıtı şifrele
        response_content = _enc.encrypt(content) if ProxyConfig.ENABLE_ENCRYPTION else content

        return jsonify({
            "success":      True,
            "content":      response_content,
            "is_encrypted": ProxyConfig.ENABLE_ENCRYPTION,
            "input_tokens": input_tokens,
            "output_tokens":output_tokens,
            "request_id":   request_id,
        })

    except httpx.TimeoutException:
        return jsonify({"error": "İstek zaman aşımına uğradı."}), 504
    except Exception as ex:
        logger.exception("[PROXY_ERR] %s", ex)
        return jsonify({"error": "Proxy iç hatası."}), 500


@app.get("/proxy/status")
@jwt_required
def proxy_status():
    """GET /proxy/status — Rate limit kullanım durumu."""
    ip    = request.remote_addr or "unknown"
    key   = g.user_id
    usage = _rate.get_usage(key)
    return jsonify({
        "user_id":   key,
        "ip":        ip,
        "usage":     usage,
        "limits":    {"per_minute": ProxyConfig.RATE_PER_MINUTE,
                      "per_hour":   ProxyConfig.RATE_PER_HOUR},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5001"))
    logger.info("Claude Proxy başlatılıyor → http://0.0.0.0:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
