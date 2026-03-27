// ── Sistem meta verileri ────────────────────────────────────────────────────
const name    = "system";
const version = "1.0.0";
const AWSTemplateFormatVersion = { version: "2010-09-09" };

const system = { name, version, AWSTemplateFormatVersion };

// ── DOM yüklendikten sonra çalışacak yardımcı ───────────────────────────────
function setElementText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = typeof value === "object" ? JSON.stringify(value) : value;
}

document.addEventListener("DOMContentLoaded", () => {
    setElementText("system",                 system);
    setElementText("name",                   name);
    setElementText("version",                version);
    setElementText("AWSTemplateFormatVersion", AWSTemplateFormatVersion);
    initConditionChecks();
});

// ── Koşul tanımları ──────────────────────────────────────────────────────────
const conditions = {
    condition1:  true,
    condition2:  false,
    condition3:  true,   // önceden tanımsız — varsayılan true
    condition4:  false,
    condition5:  true,
    condition6:  false,
    condition7:  true,
    condition8:  false,
    condition9:  true,
    condition10: false,
};

// ── Koşul kontrollerini çalıştır ─────────────────────────────────────────────
function initConditionChecks() {
    Object.entries(conditions).forEach(([key, value]) => {
        console.log(`${key} is ${value}`);
    });
}

// ── URL parametrelerini ayrıştır ─────────────────────────────────────────────
function parseQueryParam(paramName) {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(paramName);
    return raw ? decodeURIComponent(raw) : null;
}

// ── Dışa aktar ───────────────────────────────────────────────────────────────
export { system, conditions, parseQueryParam };
