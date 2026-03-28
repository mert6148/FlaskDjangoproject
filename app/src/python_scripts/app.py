# Modern ve Kapsamlı CSS & JS Framework Python Scripti
# Geliştirici: Mert Doğanay
# Versiyon: 3.0

import datetime
import sys
import os
import json
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path

@dataclass
class AppConfig:
    """Uygulama konfigürasyonu"""
    version: str = "3.0"
    author: str = "Mert Doğanay"
    default_lang: str = "tr"
    output_dir: str = "output"
    debug_mode: bool = True

class LanguageManager:
    """Çoklu dil yöneticisi"""
    
    def __init__(self):
        self.languages = {
            'tr': {
                'welcome': 'Hoş Geldiniz!',
                'desc': 'Bu modern CSS ve JavaScript framework ile güzel arayüzler oluşturabilirsiniz.',
                'theme': 'Tema Değiştir',
                'alt_theme': 'Alternatif Tema',
                'feature1': 'Modern CSS değişkenleri ve animasyonlar',
                'feature2': 'Responsive tasarım ve hover efektleri',
                'feature3': 'JavaScript ile dinamik etkileşimler',
                'feature_title1': '✨ Özellik 1',
                'feature_title2': '🚀 Özellik 2',
                'feature_title3': '⚡ Özellik 3',
                'ai_suggestion': 'AI destekli kod tamamlama aktif!',
                'created_success': '✅ Modern CSS & JS Framework oluşturuldu:',
                'python_version': 'Python sürümü:',
                'working_dir': 'Çalışma dizini:'
            },
            'en': {
                'welcome': 'Welcome!',
                'desc': 'With this modern CSS and JavaScript framework, you can create beautiful interfaces.',
                'theme': 'Switch Theme',
                'alt_theme': 'Alternative Theme',
                'feature1': 'Modern CSS variables and animations',
                'feature2': 'Responsive design and hover effects',
                'feature3': 'Dynamic interactions with JavaScript',
                'feature_title1': '✨ Feature 1',
                'feature_title2': '🚀 Feature 2',
                'feature_title3': '⚡ Feature 3',
                'ai_suggestion': 'AI-powered code completion is active!',
                'created_success': '✅ Modern CSS & JS Framework created:',
                'python_version': 'Python version:',
                'working_dir': 'Working directory:'
            }
        }
    
    def get_text(self, lang: str, key: str) -> str:
        """Belirtilen dilde metin getir"""
        return self.languages.get(lang, self.languages['tr']).get(key, key)
    
    def get_language(self, lang: str) -> Dict[str, str]:
        """Belirtilen dilin tüm metinlerini getir"""
        return self.languages.get(lang, self.languages['tr'])
    
    def add_language(self, lang_code: str, texts: Dict[str, str]) -> None:
        """Yeni dil ekle"""
        self.languages[lang_code] = texts
        print(f"✅ Yeni dil eklendi: {lang_code}")

class HTMLGenerator:
    """HTML dosyası oluşturucu"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.lang_manager = LanguageManager()
    
    def generate_html(self, lang: str = 'tr') -> str:
        """HTML içeriği oluştur"""
        t = self.lang_manager.get_language(lang)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        css_link = '<link rel="stylesheet" href="merthtmlcss-styles.css">'
        js_link = '<script src="script.js"></script>'
        
        html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern CSS & JS Framework</title>
    <meta name="description" content="{t['desc']}">
    <meta name="author" content="{self.config.author}">
    <meta name="version" content="{self.config.version}">
    {css_link}
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎨</text></svg>">
</head>
<body>
    <div class="container">
        <header class="hero-section">
            <h1 class="main-title glow">
                🎨 Modern CSS & JS Framework
            </h1>
            <p class="hero-description">{t['desc']}</p>
        </header>
        
        <main>
            <div class="card fade-in">
                <h3>{t['welcome']}</h3>
                <p>{t['desc']}</p>
                <div class="notification" id="ai-suggestion">{t['ai_suggestion']}</div>
            </div>
            
            <div class="controls-section">
                <button class="button theme-toggle" onclick="toggleTheme()">
                    🌙 {t['theme']}
                </button>
                <button class="button" onclick="temaDegistir()">
                    🎨 {t['alt_theme']}
                </button>
            </div>
            
            <div class="features-grid">
                <div class="feature-card fade-in delay-1">
                    <h4>{t['feature_title1']}</h4>
                    <p>{t['feature1']}</p>
                    <button class="button button-small" onclick="showFeature('{t['feature_title1']}')">
                        Detay
                    </button>
                </div>
                <div class="feature-card fade-in delay-2">
                    <h4>{t['feature_title2']}</h4>
                    <p>{t['feature2']}</p>
                    <button class="button button-small" onclick="showFeature('{t['feature_title2']}')">
                        Detay
                    </button>
                </div>
                <div class="feature-card fade-in delay-3">
                    <h4>{t['feature_title3']}</h4>
                    <p>{t['feature3']}</p>
                    <button class="button button-small" onclick="showFeature('{t['feature_title3']}')">
                        Detay
                    </button>
                </div>
            </div>
        </main>
        
        <footer class="app-footer">
            <div class="footer-content">
                <span>Geliştirici: {self.config.author} | Sürüm: {self.config.version} | {now}</span>
                <div class="footer-links">
                    <a href="#" onclick="showAbout()">Hakkında</a>
                    <a href="#" onclick="showContact()">İletişim</a>
                </div>
            </div>
        </footer>
    </div>
    
    {js_link}
    <script>
        // Framework konfigürasyonu
        window.FrameworkConfig = {{
            version: '{self.config.version}',
            author: '{self.config.author}',
            language: '{lang}',
            debugMode: {str(self.config.debug_mode).lower()}
        }};
    </script>
</body>
</html>'''
        
        return html
    
    def save_html(self, html_content: str, filename: str = 'modern-app.html') -> str:
        """HTML dosyasını kaydet"""
        output_path = Path(self.config.output_dir)
        output_path.mkdir(exist_ok=True)
        
        file_path = output_path / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(file_path)

class AppManager:
    """Ana uygulama yöneticisi"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.html_generator = HTMLGenerator(config)
        self.lang_manager = LanguageManager()
    
    def create_framework(self, lang: str = 'tr') -> Dict[str, str]:
        """Framework oluştur"""
        try:
            print(f"🚀 {lang.upper()} dilinde framework oluşturuluyor...")
            
            # HTML oluştur
            html_content = self.html_generator.generate_html(lang)
            html_file = self.html_generator.save_html(html_content)
            
            # CSS dosyası oluştur
            css_file = self.create_css_file()
            
            # JavaScript dosyası oluştur
            js_file = self.create_js_file()
            
            result = {
                'html_file': html_file,
                'css_file': css_file,
                'js_file': js_file,
                'success': True
            }
            
            print(f"✅ Framework başarıyla oluşturuldu!")
            print(f"📁 HTML: {html_file}")
            print(f"🎨 CSS: {css_file}")
            print(f"⚡ JS: {js_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Framework oluşturulurken hata: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_css_file(self) -> str:
        """CSS dosyası oluştur"""
        css_content = self.generate_css_content()
        css_file = Path(self.config.output_dir) / 'merthtmlcss-styles.css'
        
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        return str(css_file)
    
    def create_js_file(self) -> str:
        """JavaScript dosyası oluştur"""
        js_content = self.generate_js_content()
        js_file = Path(self.config.output_dir) / 'script.js'
        
        with open(js_file, 'w', encoding='utf-8') as f:
            f.write(js_content)
        
        return str(js_file)
    
    def generate_css_content(self) -> str:
        """CSS içeriği oluştur"""
        return f"""/*
Merthtmlcss CSS Framework
Versiyon: {self.config.version}
Geliştirici: {self.config.author}
Oluşturulma: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*/

:root {{
    --primary-color: #667eea;
    --secondary-color: #764ba2;
    --accent-color: #ff6b6b;
    --success-color: #51cf66;
    --warning-color: #ffd43b;
    --error-color: #ff4757;
    --light-color: #ffffff;
    --dark-color: #1a1a1a;
    --gray-color: #6c757d;
    --border-radius: 12px;
    --box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

/* Temel stiller */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.6;
    color: var(--dark-color);
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}}

/* Hero section */
.hero-section {{
    text-align: center;
    padding: 4rem 0;
    margin-bottom: 3rem;
}}

.main-title {{
    font-size: clamp(2rem, 5vw, 4rem);
    font-weight: 800;
    margin-bottom: 1rem;
    background: linear-gradient(45deg, var(--primary-color), var(--accent-color));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.hero-description {{
    font-size: 1.2rem;
    color: var(--gray-color);
    max-width: 600px;
    margin: 0 auto;
}}

/* Kartlar */
.card {{
    background: var(--light-color);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 2rem;
    margin: 1.5rem 0;
    transition: var(--transition);
}}

.card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}}

/* Butonlar */
.button {{
    display: inline-block;
    padding: 12px 24px;
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
    color: var(--light-color);
    text-decoration: none;
    border: none; 
    border-radius: var(--border-radius);
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: var(--transition);
    box-shadow: var(--box-shadow);
    margin: 0.5rem;
}}

.button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}}

.button-small {{
    padding: 8px 16px;
    font-size: 14px;
}}

/* Grid sistem */
.features-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin: 3rem 0;
}}

.feature-card {{
    background: var(--light-color);
    border-radius: var(--border-radius);
    padding: 2rem;
    text-align: center;
    box-shadow: var(--box-shadow);
    transition: var(--transition);
}}

.feature-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.2);
}}

/* Animasyonlar */
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

@keyframes glow {{
    0%, 100% {{ text-shadow: 0 0 5px var(--primary-color); }}
    50% {{ text-shadow: 0 0 20px var(--accent-color), 0 0 30px var(--accent-color); }}
}}

.fade-in {{ animation: fadeIn 0.8s ease-out; }}
.glow {{ animation: glow 2s ease-in-out infinite; }}

.delay-1 {{ animation-delay: 0.1s; }}
.delay-2 {{ animation-delay: 0.2s; }}
.delay-3 {{ animation-delay: 0.3s; }}

/* Responsive */
@media (max-width: 768px) {{
    .container {{ padding: 1rem; }}
    .features-grid {{ grid-template-columns: 1fr; }}
    .button {{ width: 100%; text-align: center; }}
}}

/* Footer */
.app-footer {{
    margin-top: 4rem;
    padding: 2rem 0;
    border-top: 1px solid #eee;
    text-align: center;
}}

.footer-content {{
    display: flex;
    flex-direction: column;
    gap: 1rem;
}}

.footer-links a {{
    color: var(--primary-color);
    text-decoration: none;
    margin: 0 1rem;
    transition: var(--transition);
}}

.footer-links a:hover {{
    color: var(--accent-color);
}}

/* Notification */
.notification {{
    background: linear-gradient(135deg, var(--success-color), #a8e6cf);
    color: var(--light-color);
    padding: 1rem;
    border-radius: var(--border-radius);
    margin-top: 1rem;
    text-align: center;
    font-weight: 500;
}}

/* Controls section */
.controls-section {{
    text-align: center;
    margin: 2rem 0;
}}
"""
    
    def generate_js_content(self) -> str:
        """JavaScript içeriği oluştur"""
        return f"""// Merthtmlcss JavaScript Framework
// Versiyon: {self.config.version}
// Geliştirici: {self.config.author}

class MerthtmlcssApp {{
    constructor() {{
        this.config = window.FrameworkConfig || {{}};
        this.notification = document.getElementById('ai-suggestion');
        this.init();
    }}
    
    init() {{
        this.setupEventListeners();
        this.loadFeatures();
        this.setupTheme();
        console.log("🎨 Merthtmlcss App başlatıldı", this.config);
    }}
    
    setupEventListeners() {{
        // Tema değiştirme
        document.querySelectorAll('.theme-toggle').forEach(btn => {{
            btn.addEventListener('click', () => this.toggleTheme());
        }});
        
        // Kart hover efektleri
        document.querySelectorAll('.feature-card').forEach(card => {{
            card.addEventListener('mouseenter', () => this.cardHover(card));
            card.addEventListener('mouseleave', () => this.cardLeave(card));
        }});
    }}
    
    setupTheme() {{
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {{
            document.body.classList.add('dark-theme');
        }}
    }}
    
    toggleTheme() {{
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        this.showNotification(`Tema ${{isDark ? 'karanlık' : 'aydınlık'}} moda geçirildi`, 'success');
    }}
    
    cardHover(card) {{
        card.style.transform = 'scale(1.02)';
        card.style.boxShadow = '0 15px 35px rgba(0,0,0,0.2)';
    }}
    
    cardLeave(card) {{
        card.style.transform = 'scale(1)';
        card.style.boxShadow = '';
    }}
    
    showNotification(message, type = 'info') {{
        if (this.notification) {{
            this.notification.textContent = message;
            this.notification.className = `notification ${{type}}`;
        }}
        
        // Otomatik kapatma
        setTimeout(() => {{
            if (this.notification) {{
                this.notification.style.display = 'none';
            }}
        }}, 3000);
    }}
    
    loadFeatures() {{
        const features = [
            {{ name: 'Modern Tasarım', description: 'CSS Grid, Flexbox ve modern layout teknikleri' }},
            {{ name: 'Responsive', description: 'Mobil-first yaklaşım ve breakpoint sistemi' }},
            {{ name: 'Animasyonlar', description: 'CSS keyframes ve transition efektleri' }}
        ];
        
        console.log('Özellikler yüklendi:', features);
    }}
}}

// Global fonksiyonlar
function showFeature(featureName) {{
    const messages = {{
        '✨ Özellik 1': 'CSS Grid ve Flexbox ile modern layout oluşturma',
        '🚀 Özellik 2': 'Tüm cihazlarda mükemmel görünüm sağlama',
        '⚡ Özellik 3': 'CSS animasyonları ile etkileyici efektler'
    }};
    
    const app = window.merthtmlcssApp;
    if (app) {{
        app.showNotification(messages[featureName] || 'Özellik detayı', 'info');
    }}
}}

function temaDegistir() {{
    const app = window.merthtmlcssApp;
    if (app) {{
        app.toggleTheme();
    }}
}}

function toggleTheme() {{
    const app = window.merthtmlcssApp;
    if (app) {{
        app.toggleTheme();
    }}
}}

function showAbout() {{
    alert('Merthtmlcss Framework - Modern web geliştirme için tasarlanmış CSS ve JavaScript framework\'ü');
}}

function showContact() {{
    alert('İletişim: mertdoganay437@gmail.com\\nGitHub: @mert6148');
}}

// Sayfa yüklendiğinde app'i başlat
document.addEventListener('DOMContentLoaded', () => {{
    window.merthtmlcssApp = new MerthtmlcssApp();
}});

// Service Worker kaydı (PWA desteği)
if ('serviceWorker' in navigator) {{
    window.addEventListener('load', () => {{
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {{
                console.log('Service Worker kaydedildi:', registration.scope);
            }})
            .catch(error => {{
                console.log('Service Worker kaydı başarısız:', error);
            }});
    }});
}}
"""

def main():
    """Ana fonksiyon"""
    config = AppConfig()
    
    print(f"🚀 Merthtmlcss Framework v{config.version}")
    print(f"👨‍💻 Geliştirici: {config.author}")
    print(f"🐍 Python sürümü: {sys.version}")
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    
    # Uygulama yöneticisini oluştur
    app_manager = AppManager(config)
    
    # Türkçe framework oluştur
    result_tr = app_manager.create_framework('tr')
    
    if result_tr['success']:
        print(f"\n🎉 Framework başarıyla oluşturuldu!")
        print(f"📁 Çıktı dizini: {config.output_dir}")
        
        # İngilizce framework de oluştur
        result_en = app_manager.create_framework('en')
        if result_en['success']:
            print("🌍 İngilizce versiyon da oluşturuldu!")
    else:
        print(f"❌ Framework oluşturulamadı: {result_tr.get('error', 'Bilinmeyen hata')}")

def main():
    """Yan fonksiyon"""
    config = AppConfig()
    
    print(f"🚀 Merthtmlcss Framework v{config.version}")
    print(f"👨‍💻 Geliştirici: {config.author}")
    print(f"🐍 Python sürümü: {sys.version}")
    print(f"📁 Çalışma dizini: {os.getcwd()}")
    
    # Uygulama yöneticisini oluştur
    app_manager = AppManager(config)
    
    # Türkçe framework oluştur
    result_tr = app_manager.create_framework('tr')
    
    if result_tr['success']:
        print(f"\n🎉 Framework başarıyla oluşturuldu!")
        print(f"📁 Çıktı dizini: {config.output_dir}")
        
        # İngilizce framework de oluştur
        result_en = app_manager.create_framework('en')
        if result_en['success']:
            print("🌍 İngilizce versiyon da oluşturuldu!")
    else:
        print(f"❌ Framework oluşturulamadı: {result_tr.get('error', 'Bilinmeyen hata')}")

if __name__ == "__main__":
    main()