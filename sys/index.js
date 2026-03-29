/**
 * index.js — Sistem Modülü İstemci Katmanı
 * ==========================================
 * Düzeltmeler (orijinal index.js):
 *   - Tekrarlayan DOMContentLoaded listener'lar birleştirildi
 *   - system.author → author alanı JSON'dan okunuyor (yoksa 'Bilinmiyor')
 *   - cancelAnimationFrame yanlış atama kaldırıldı
 *   - output nesnesinde 'system' iki kez geçiyordu, temizlendi
 *
 * @module index
 * @version 1.0.0
 */

"use strict";

// ── Veri yükle ────────────────────────────────────────────────────────────────
/** @type {import('./system.json')} */
const system = require("./system.json");

const name                  = system.name;
const version               = system.version;
const author                = system.author ?? "Bilinmiyor";
const AWSTemplateFormatVersion = system.AWSTemplateFormatVersion ?? null;

/**
 * Uygulamanın çıktı nesnesi — DOM ve harici tüketiciler için standart yapı.
 * @typedef {Object} SystemOutput
 * @property {Object} system - Sistem meta verisi
 */
const output = {
  system: {
    name,
    version,
    author,
    AWSTemplateFormatVersion,
  },
};

// ── DOM yükleme ───────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  /** @param {string} id @param {string} value */
  function setById(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  // Ham JSON çıktısı
  const outputEl = document.getElementById("output");
  if (outputEl) outputEl.textContent = JSON.stringify(output, null, 2);

  // Tekil alanlar
  setById("name",                   name);
  setById("version",                version);
  setById("author",                 author);
  setById("AWSTemplateFormatVersion",
    AWSTemplateFormatVersion ? JSON.stringify(AWSTemplateFormatVersion) : "—");
});

// ── Dışa aktar ────────────────────────────────────────────────────────────────
module.exports = { system, output, name, version, author };