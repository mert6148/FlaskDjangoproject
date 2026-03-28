/**
 * app.js — Flask + SQLite Veritabanı İstemci Katmanı
 *
 * Düzeltmeler (orijinal app.js):
 *   - 'test' ve 'anotherTest' tanımsız değişken referansları kaldırıldı
 *   - String olarak yazılmış sahte "Application class" açıklaması silindi
 *   - Tüm API çağrıları, form yönetimi ve DB durum takibi eklendi
 */

"use strict";

// ── Uygulama sabitleri ────────────────────────────────────────────────────────
const APP = {
  name:    "FlaskDB App",
  version: "1.0.0",
  apiBase: "",            // Aynı origin; başka sunucu: "http://127.0.0.1:5000"
};

// ── Yardımcı: DOM seçici ──────────────────────────────────────────────────────
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

// ── Yardımcı: fetch wrapper ───────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const url = APP.apiBase + path;
  const defaults = {
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
  };
  try {
    const res = await fetch(url, { ...defaults, ...options,
      headers: { ...defaults.headers, ...(options.headers || {}) },
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    console.error(`[apiFetch] ${path}:`, err);
    return { ok: false, status: 0, data: { hata: err.message } };
  }
}

// ═════════════════════════════════════════════════════════════════════════════
// VERİTABANI DURUM YÖNETİCİSİ
// ═════════════════════════════════════════════════════════════════════════════

const DB = {
  // Önbellek
  _mesajlar:  [],
  _tabloInfo: {},
  _statusOk:  false,

  /** Sunucu sağlık kontrolü */
  async kontrol() {
    const { ok, data } = await apiFetch("/api/status");
    this._statusOk = ok;
    if (ok) {
      console.log(`[DB] Bağlantı OK · ${data.mesaj_sayisi} kayıt · ${data.zaman}`);
    } else {
      console.warn("[DB] Sunucuya ulaşılamıyor");
    }
    return { ok, data };
  },

  /** Tüm mesajları çek */
  async mesajlariGetir() {
    const { ok, data } = await apiFetch("/api/mesajlar");
    if (ok && Array.isArray(data)) {
      this._mesajlar = data;
    }
    return this._mesajlar;
  },

  /** Yeni mesaj ekle (JSON) */
  async mesajEkle(veri) {
    if (!veri?.trim()) return { ok: false, data: { hata: "Boş mesaj gönderilemez." } };
    const result = await apiFetch("/api/mesaj", {
      method: "POST",
      body: JSON.stringify({ veri }),
    });
    if (result.ok) {
      this._mesajlar.unshift(result.data.kayit);
      console.info("[DB] Mesaj eklendi:", result.data.kayit);
    }
    return result;
  },

  /** Mesaj sil */
  async mesajSil(id) {
    const result = await apiFetch(`/api/mesaj/${id}`, { method: "DELETE" });
    if (result.ok) {
      this._mesajlar = this._mesajlar.filter(m => m.id !== id);
      console.info("[DB] Mesaj silindi:", id);
    }
    return result;
  },

  /** Tüm mesajları sil */
  async tumunuSil() {
    const result = await apiFetch("/api/mesajlar", { method: "DELETE" });
    if (result.ok) this._mesajlar = [];
    return result;
  },

  /** Veritabanı istatistiklerini getir */
  async istatistikler() {
    const { ok, data } = await apiFetch("/api/db/istatistik");
    if (ok) this._tabloInfo = data;
    return data;
  },

  /** Belirli bir mesajı güncelle */
  async mesajGuncelle(id, yeniVeri) {
    return apiFetch(`/api/mesaj/${id}`, {
      method: "PUT",
      body: JSON.stringify({ veri: yeniVeri }),
    });
  },

  /** Mesajlarda arama yap */
  async ara(sorgu) {
    return apiFetch(`/api/mesajlar/ara?q=${encodeURIComponent(sorgu)}`);
  },
};

// ═════════════════════════════════════════════════════════════════════════════
// UI RENDER KATMANI
// ═════════════════════════════════════════════════════════════════════════════

const UI = {

  /** Flash benzeri bildirim göster */
  bildirim(mesaj, tur = "info") {
    const renkler = {
      success: "#2d6a4f", error: "#c0392b", warn: "#b5651d", info: "#2c5f8a"
    };
    const ikonlar = { success: "✓", error: "✗", warn: "⚠", info: "ℹ" };

    const el = document.createElement("div");
    el.style.cssText = `
      position:fixed;top:20px;right:20px;z-index:9999;
      background:#fff;border-left:3px solid ${renkler[tur]||renkler.info};
      color:${renkler[tur]||renkler.info};padding:12px 18px;
      border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,.12);
      font-family:'Geist Mono',monospace;font-size:12px;
      display:flex;align-items:center;gap:8px;
      animation:slideInRight .25s ease;
      max-width:320px;
    `;
    el.innerHTML = `<strong>${ikonlar[tur]}</strong> ${mesaj}`;
    document.body.appendChild(el);
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity .3s";
      setTimeout(() => el.remove(), 300);
    }, 3000);
  },

  /** Yükleniyor durumu */
  yukleniyorGoster(hedefId, aktif) {
    const el = document.getElementById(hedefId);
    if (!el) return;
    if (aktif) {
      el.dataset.oncekiIcerik = el.innerHTML;
      el.innerHTML = '<span class="spin" aria-label="Yükleniyor"></span>';
      el.disabled = true;
    } else {
      el.innerHTML = el.dataset.oncekiIcerik || el.innerHTML;
      el.disabled = false;
    }
  },

  /** Mesaj listesini yeniden çiz */
  listeyiGuncelle(mesajlar, hedefSelector = "#msg-list") {
    const konteyner = $(hedefSelector);
    if (!konteyner) return;

    if (!mesajlar.length) {
      konteyner.innerHTML = `
        <div class="empty">
          <div class="empty-icon">✉</div>
          <div class="empty-text">Henüz mesaj yok</div>
          <div class="empty-sub">Aşağıdaki formu kullanın</div>
        </div>`;
      return;
    }

    konteyner.innerHTML = mesajlar.map(m => `
      <div class="msg-item" data-id="${m.id}">
        <span class="msg-num">#${m.id}</span>
        <div class="msg-body">
          <div class="msg-text">${this._kacis(m.veri)}</div>
          <div class="msg-meta">
            <span>🕐 ${m.zaman || "—"}</span>
            <span>${(m.veri || "").length} karakter</span>
          </div>
        </div>
        <div class="msg-actions">
          <button class="btn btn-danger btn-sil" data-id="${m.id}">Sil</button>
        </div>
      </div>`).join("");

    // Silme event'lerini bağla
    $$(".btn-sil", konteyner).forEach(btn => {
      btn.addEventListener("click", () => this._silOnayı(Number(btn.dataset.id)));
    });
  },

  /** Sayaç rozeti güncelle */
  sayacGuncelle(n, hedefSelector = "#msg-count") {
    const el = $(hedefSelector);
    if (el) el.textContent = `${n} kayıt`;
  },

  /** DB durum göstergesi */
  dbDurumGuncelle(tamam) {
    const dot = $(".status-dot");
    if (dot) dot.style.background = tamam ? "var(--green, #2d6a4f)" : "var(--red, #c0392b)";
  },

  /** Tablo istatistiklerini göster */
  istatistikGoster(data, hedefSelector = "#db-stats") {
    const el = $(hedefSelector);
    if (!el || !data) return;
    el.innerHTML = Object.entries(data).map(([k, v]) => `
      <div class="db-stat-row">
        <span class="db-stat-key">${k}</span>
        <span class="db-stat-val">${v}</span>
      </div>`).join("");
  },

  // XSS koruması
  _kacis(str) {
    return String(str)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  },

  async _silOnayı(id) {
    if (!confirm(`#${id} numaralı mesaj silinsin mi?`)) return;
    const { ok } = await DB.mesajSil(id);
    if (ok) {
      this.listeyiGuncelle(DB._mesajlar);
      this.sayacGuncelle(DB._mesajlar.length);
      this.bildirim("Mesaj silindi.", "success");
    } else {
      this.bildirim("Silme başarısız.", "error");
    }
  },
};

// ═════════════════════════════════════════════════════════════════════════════
// FORM YÖNETİCİSİ
// ═════════════════════════════════════════════════════════════════════════════

const Form = {

  init(formId = "msgForm") {
    const form = document.getElementById(formId);
    if (!form) return;

    const textarea = form.querySelector("textarea[name='data']");
    const counter  = form.querySelector("#charCount");
    const submitBtn = form.querySelector("button[type='submit']");

    // Karakter sayacı
    if (textarea && counter) {
      textarea.addEventListener("input", () => {
        const n = textarea.value.length;
        counter.textContent = `${n} / 500`;
        counter.className = "char-count" +
          (n > 450 ? (n >= 500 ? " over" : " warn") : "");
      });
    }

    // AJAX form gönderimi
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const veri = textarea?.value?.trim() || "";
      if (!veri) { UI.bildirim("Mesaj boş olamaz.", "warn"); return; }
      if (veri.length > 500) { UI.bildirim("500 karakter sınırı aşıldı.", "error"); return; }

      UI.yukleniyorGoster("submit-btn", true);
      const { ok, data } = await DB.mesajEkle(veri);
      UI.yukleniyorGoster("submit-btn", false);

      if (ok) {
        if (textarea) textarea.value = "";
        if (counter) counter.textContent = "0 / 500";
        UI.listeyiGuncelle(DB._mesajlar);
        UI.sayacGuncelle(DB._mesajlar.length);
        UI.bildirim("Mesaj gönderildi!", "success");
      } else {
        UI.bildirim(data?.hata || "Gönderme başarısız.", "error");
      }
    });

    // Arama kutusu
    const searchInput = document.getElementById("search-input");
    if (searchInput) {
      let timer;
      searchInput.addEventListener("input", () => {
        clearTimeout(timer);
        timer = setTimeout(async () => {
          const q = searchInput.value.trim();
          if (!q) {
            UI.listeyiGuncelle(DB._mesajlar);
            return;
          }
          const { ok, data } = await DB.ara(q);
          if (ok && Array.isArray(data)) {
            UI.listeyiGuncelle(data);
            UI.bildirim(`${data.length} sonuç bulundu.`, "info");
          }
        }, 400);
      });
    }

    // Temizle butonu
    const temizleBtn = document.getElementById("temizle-btn");
    if (temizleBtn) {
      temizleBtn.addEventListener("click", async () => {
        if (!confirm("Tüm mesajlar silinsin mi?")) return;
        const { ok } = await DB.tumunuSil();
        if (ok) {
          UI.listeyiGuncelle([]);
          UI.sayacGuncelle(0);
          UI.bildirim("Tüm mesajlar silindi.", "info");
        }
      });
    }
  },
};

// ═════════════════════════════════════════════════════════════════════════════
// UYGULAMA BAŞLATICI
// ═════════════════════════════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", async () => {
  console.log(`[${APP.name}] v${APP.version} başlatılıyor...`);

  // 1. DB bağlantı kontrolü
  const { ok: dbOk, data: statusData } = await DB.kontrol();
  UI.dbDurumGuncelle(dbOk);

  if (dbOk) {
    // 2. İlk verileri yükle
    const mesajlar = await DB.mesajlariGetir();
    UI.listeyiGuncelle(mesajlar, "#msg-list");
    UI.sayacGuncelle(mesajlar.length);

    // 3. DB istatistikleri
    const stats = await DB.istatistikler();
    UI.istatistikGoster(stats);

    // 4. Periyodik yenileme (60 saniyede bir)
    setInterval(async () => {
      const ms = await DB.mesajlariGetir();
      UI.listeyiGuncelle(ms, "#msg-list");
      UI.sayacGuncelle(ms.length);
    }, 60_000);

  } else {
    UI.bildirim("Sunucuya bağlanılamadı. Sayfa formu kullanılıyor.", "warn");
  }

  // 5. Form yöneticisini başlat
  Form.init("msgForm");

  console.log(`[${APP.name}] Hazır.`);
});

// ── Genel stil animasyonu (JS ile ekleniyor) ──────────────────────────────────
const style = document.createElement("style");
style.textContent = `
  @keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
  }
  .spin {
    display: inline-block; width: 14px; height: 14px; border-radius: 50%;
    border: 2px solid #ccc; border-top-color: #333;
    animation: spin .7s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
`;
document.head.appendChild(style);

// ── Dışa aktar (ES module ortamı için) ───────────────────────────────────────
export { APP, DB, UI, Form };