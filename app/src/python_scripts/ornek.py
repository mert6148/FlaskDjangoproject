#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merthtmlcss Python CSS Yöneticisi v4.0
CSS kodları oluşturan ve yöneten gelişmiş Python uygulaması
"""

import os
import json
import datetime
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class CSSConfig:
    """CSS konfigürasyon ayarları"""
    output_dir: str = "css_output"
    minify: bool = False
    source_maps: bool = True
    auto_prefix: bool = True
    version: str = "4.0"
    author: str = "Mert Doğanay"

class CSSVariableManager:
    """CSS değişkenlerini yöneten sınıf"""
    
    def __init__(self):
        self.variables = {
            'primary-color': '#667eea',
            'secondary-color': '#764ba2',
            'success-color': '#2ed573',
            'error-color': '#ff4757',
            'warning-color': '#ffa502',
            'info-color': '#3742fa',
            'light-color': '#ffffff',
            'dark-color': '#1a1a1a',
            'gray-color': '#747d8c',
            'accent-color': '#ff6b6b',
            'border-radius': '12px',
            'box-shadow': '0 4px 15px rgba(0,0,0,0.1)',
            'transition': 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            'font-family': "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
            'breakpoint-sm': '576px',
            'breakpoint-md': '768px',
            'breakpoint-lg': '992px',
            'breakpoint-xl': '1200px',
            'breakpoint-xxl': '1400px',
            'max-width': '1200px'
        }
    
    def add_variable(self, name: str, value: str) -> None:
        """CSS değişkeni ekle"""
        self.variables[name] = value
        logging.info(f"CSS değişkeni eklendi: {name} = {value}")
    
    def remove_variable(self, name: str) -> bool:
        """CSS değişkeni kaldır"""
        if name in self.variables:
            del self.variables[name]
            logging.info(f"CSS değişkeni kaldırıldı: {name}")
            return True
        return False
    
    def get_variables(self) -> Dict[str, str]:
        """Tüm değişkenleri getir"""
        return self.variables.copy()
    
    def export_variables(self, filename: str = "css_variables.json") -> str:
        """Değişkenleri JSON dosyasına kaydet"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.variables, f, indent=2, ensure_ascii=False)
        return filename

class CSSManager:
    """CSS kodları oluşturan ve yöneten gelişmiş sınıf"""
    
    def __init__(self, config: CSSConfig = None):
        self.config = config or CSSConfig()
        self.variable_manager = CSSVariableManager()
        self.css_styles = {}
        self.output_file = 'generated_styles.css'
        self.setup_logging()
        
        # Çıktı dizinini oluştur
        Path(self.config.output_dir).mkdir(exist_ok=True)
    
    def setup_logging(self):
        """Logging ayarlarını yapılandır"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('css_manager.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def add_css_variable(self, name: str, value: str) -> None:
        """CSS değişkeni ekle"""
        self.variable_manager.add_variable(name, value)
    
    def remove_css_variable(self, name: str) -> bool:
        """CSS değişkeni kaldır"""
        return self.variable_manager.remove_variable(name)
    
    def get_css_variables(self) -> Dict[str, str]:
        """Tüm CSS değişkenlerini getir"""
        return self.variable_manager.get_variables()
    
    def export_variables(self, filename: str = None) -> str:
        """CSS değişkenlerini dışa aktar"""
        if not filename:
            filename = f"css_variables_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        return self.variable_manager.export_variables(filename)
    
    def import_variables(self, filename: str) -> bool:
        """CSS değişkenlerini içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                variables = json.load(f)
            
            for name, value in variables.items():
                self.variable_manager.add_variable(name, value)
            
            logging.info(f"CSS değişkenleri başarıyla içe aktarıldı: {filename}")
            return True
        except Exception as e:
            logging.error(f"CSS değişkenleri içe aktarılamadı: {e}")
            return False
    
    def generate_css_variables(self) -> str:
        """CSS değişkenlerini oluştur"""
        css = ":root {\n"
        for name, value in self.css_variables.items():
            css += f"    --{name}: {value};\n"
        css += "}\n\n"
        return css
    
    def create_button_styles(self) -> str:
        """Modern buton stilleri oluştur"""
        css = """
/* Modern Buton Stilleri */
.button {
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
    position: relative;
    overflow: hidden;
}

.button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}

.button:active {
    transform: translateY(0);
}

.button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.button:hover::before {
    left: 100%;
}

/* Buton varyasyonları */
.button-primary {
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
}

.button-success {
    background: linear-gradient(45deg, var(--success-color), #26de81);
}

.button-error {
    background: linear-gradient(45deg, var(--error-color), #ff3838);
}

.button-warning {
    background: linear-gradient(45deg, var(--warning-color), #ff9ff3);
}

.button-info {
    background: linear-gradient(45deg, var(--info-color), #54a0ff);
}

/* Buton boyutları */
.button-small {
    padding: 8px 16px;
    font-size: 14px;
}

.button-large {
    padding: 16px 32px;
    font-size: 18px;
}

"""
        return css
    
    def create_card_styles(self) -> str:
        """Modern kart stilleri oluştur"""
        css = """
/* Modern Kart Stilleri */
.card {
    background: var(--light-color);
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    padding: 20px;
    margin: 15px 0;
    transition: var(--transition);
    border: 1px solid rgba(0,0,0,0.1);
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.card-header {
    border-bottom: 2px solid var(--primary-color);
    padding-bottom: 10px;
    margin-bottom: 15px;
}

.card-title {
    color: var(--primary-color);
    font-size: 1.5em;
    font-weight: 700;
    margin: 0;
}

.card-subtitle {
    color: var(--gray-color);
    font-size: 1em;
    margin: 5px 0 0 0;
}

.card-body {
    line-height: 1.6;
}

.card-footer {
    border-top: 1px solid #eee;
    padding-top: 15px;
    margin-top: 15px;
    text-align: right;
}

/* Kart varyasyonları */
.card-primary {
    border-left: 4px solid var(--primary-color);
}

.card-success {
    border-left: 4px solid var(--success-color);
}

.card-error {
    border-left: 4px solid var(--error-color);
}

.card-warning {
    border-left: 4px solid var(--warning-color);
}

"""
        return css
    
    def create_form_styles(self) -> str:
        """Modern form stilleri oluştur"""
        css = """
/* Modern Form Stilleri */
.form-group {
    margin-bottom: 20px;
}

.form-label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: var(--dark-color);
}

.form-input {
    width: 100%;
    padding: 12px 16px;
    border: 2px solid #e1e8ed;
    border-radius: var(--border-radius);
    font-size: 16px;
    transition: var(--transition);
    background: var(--light-color);
}

.form-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input.error {
    border-color: var(--error-color);
    box-shadow: 0 0 0 3px rgba(255, 71, 87, 0.1);
}

.form-input.success {
    border-color: var(--success-color);
    box-shadow: 0 0 0 3px rgba(46, 213, 115, 0.1);
}

.form-textarea {
    min-height: 120px;
    resize: vertical;
}

.form-select {
    background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
    background-position: right 12px center;
    background-repeat: no-repeat;
    background-size: 16px;
    padding-right: 40px;
}

.form-error {
    color: var(--error-color);
    font-size: 14px;
    margin-top: 5px;
    display: block;
}

.form-success {
    color: var(--success-color);
    font-size: 14px;
    margin-top: 5px;
    display: block;
}

"""
        return css
    
    def create_animation_styles(self) -> str:
        """Animasyon stilleri oluştur"""
        css = """
/* Animasyon Stilleri */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideIn {
    from {
        transform: translateX(-100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOut {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

@keyframes pulse {
    0% {
        transform: scale(1);
    }
    50% {
        transform: scale(1.05);
    }
    100% {
        transform: scale(1);
    }
}

@keyframes glow {
    from {
        text-shadow: 0 0 5px var(--primary-color), 0 0 10px var(--primary-color), 0 0 15px var(--primary-color);
    }
    to {
        text-shadow: 0 0 10px var(--secondary-color), 0 0 20px var(--secondary-color), 0 0 30px var(--secondary-color);
    }
}

@keyframes rotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

/* Animasyon sınıfları */
.fade-in {
    animation: fadeIn 0.8s ease-out;
}

.slide-in {
    animation: slideIn 0.5s ease-out;
}

.slide-out {
    animation: slideOut 0.5s ease-in;
}

.pulse {
    animation: pulse 2s infinite;
}

.glow {
    animation: glow 2s ease-in-out infinite alternate;
}

.rotate {
    animation: rotate 2s linear infinite;
}

/* Animasyon gecikmeleri */
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }
.delay-4 { animation-delay: 0.4s; }
.delay-5 { animation-delay: 0.5s; }

"""
        return css
    
    def create_responsive_styles(self) -> str:
        """Responsive tasarım stilleri oluştur"""
        css = """
/* Responsive Tasarım Stilleri */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

.row {
    display: flex;
    flex-wrap: wrap;
    margin: 0 -10px;
}

.col {
    flex: 1;
    padding: 0 10px;
}

/* Grid sistemi */
.grid {
    display: grid;
    gap: 20px;
}

.grid-2 {
    grid-template-columns: repeat(2, 1fr);
}

.grid-3 {
    grid-template-columns: repeat(3, 1fr);
}

.grid-4 {
    grid-template-columns: repeat(4, 1fr);
}

/* Responsive breakpoint'ler */
@media (max-width: 768px) {
    .container {
        padding: 0 15px;
    }
    
    .grid-2,
    .grid-3,
    .grid-4 {
        grid-template-columns: 1fr;
    }
    
    .row {
        flex-direction: column;
    }
    
    .col {
        margin-bottom: 20px;
    }
    
    .button {
        width: 100%;
        text-align: center;
    }
}

@media (max-width: 480px) {
    .container {
        padding: 0 10px;
    }
    
    .card {
        padding: 15px;
    }
    
    .form-input {
        padding: 10px 12px;
    }
}

/* Utility sınıfları */
.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.mt-1 { margin-top: 10px; }
.mt-2 { margin-top: 20px; }
.mt-3 { margin-top: 30px; }

.mb-1 { margin-bottom: 10px; }
.mb-2 { margin-bottom: 20px; }
.mb-3 { margin-bottom: 30px; }

.p-1 { padding: 10px; }
.p-2 { padding: 20px; }
.p-3 { padding: 30px; }

.d-none { display: none; }
.d-block { display: block; }
.d-flex { display: flex; }
.d-grid { display: grid; }

"""
        return css
    
    def create_dark_theme_styles(self) -> str:
        """Karanlık tema stilleri oluştur"""
        css = """
/* Karanlık Tema Stilleri */
.dark-theme {
    --primary-color: #8b5cf6;
    --secondary-color: #a855f7;
    --accent-color: #f59e0b;
    --light-color: #1f2937;
    --dark-color: #f9fafb;
    --gray-color: #9ca3af;
    --text-color: #f9fafb;
    --bg-color: #111827;
    --card-bg: #1f2937;
    --border-color: #374151;
}

.dark-theme body {
    background: var(--bg-color);
    color: var(--text-color);
}

.dark-theme .card {
    background: var(--card-bg);
    border-color: var(--border-color);
}

.dark-theme .form-input {
    background: var(--card-bg);
    border-color: var(--border-color);
    color: var(--text-color);
}

.dark-theme .form-input:focus {
    border-color: var(--primary-color);
}

.dark-theme .button {
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
}
"""
        return css
    
    def create_utility_classes(self) -> str:
        """Utility CSS sınıfları oluştur"""
        css = """
/* Utility Sınıfları */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.flex-row { flex-direction: row; }
.flex-wrap { flex-wrap: wrap; }
.flex-nowrap { flex-wrap: nowrap; }

.justify-center { justify-content: center; }
.justify-start { justify-content: flex-start; }
.justify-end { justify-content: flex-end; }
.justify-between { justify-content: space-between; }
.justify-around { justify-content: space-around; }

.items-center { align-items: center; }
.items-start { align-items: flex-start; }
.items-end { align-items: flex-end; }
.items-stretch { align-items: stretch; }

.w-full { width: 100%; }
.w-auto { width: auto; }
.h-full { height: 100%; }
.h-auto { height: auto; }

.text-xs { font-size: 0.75rem; }
.text-sm { font-size: 0.875rem; }
.text-base { font-size: 1rem; }
.text-lg { font-size: 1.125rem; }
.text-xl { font-size: 1.25rem; }
.text-2xl { font-size: 1.5rem; }
.text-3xl { font-size: 1.875rem; }

.font-light { font-weight: 300; }
.font-normal { font-weight: 400; }
.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.rounded-none { border-radius: 0; }
.rounded-sm { border-radius: 0.125rem; }
.rounded { border-radius: 0.25rem; }
.rounded-md { border-radius: 0.375rem; }
.rounded-lg { border-radius: 0.5rem; }
.rounded-xl { border-radius: 0.75rem; }
.rounded-full { border-radius: 9999px; }

.shadow-sm { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
.shadow { box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); }
.shadow-md { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); }
.shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
.shadow-xl { box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04); }

.opacity-0 { opacity: 0; }
.opacity-25 { opacity: 0.25; }
.opacity-50 { opacity: 0.5; }
.opacity-75 { opacity: 0.75; }
.opacity-100 { opacity: 1; }

.transition { transition: all 0.15s ease-in-out; }
.transition-fast { transition: all 0.1s ease-in-out; }
.transition-slow { transition: all 0.3s ease-in-out; }

.transform { transform: translateX(0) translateY(0) rotate(0) skewX(0) skewY(0) scaleX(1) scaleY(1); }
.scale-95 { transform: scale(0.95); }
.scale-100 { transform: scale(1); }
.scale-105 { transform: scale(1.05); }
.scale-110 { transform: scale(1.1); }

.rotate-0 { transform: rotate(0deg); }
.rotate-90 { transform: rotate(90deg); }
.rotate-180 { transform: rotate(180deg); }
.rotate-270 { transform: rotate(270deg); }

.translate-x-0 { transform: translateX(0); }
.translate-x-1 { transform: translateX(0.25rem); }
.translate-x-2 { transform: translateX(0.5rem); }
.translate-x-4 { transform: translateX(1rem); }
.translate-x-8 { transform: translateX(2rem); }

.translate-y-0 { transform: translateY(0); }
.translate-y-1 { transform: translateY(0.25rem); }
.translate-y-2 { transform: translateY(0.5rem); }
.translate-y-4 { transform: translateY(1rem); }
.translate-y-8 { transform: translateY(2rem); }
"""
        return css
    
    def create_advanced_animations(self) -> str:
        """Gelişmiş animasyon stilleri oluştur"""
        css = """
/* Gelişmiş Animasyon Stilleri */
@keyframes bounce {
    0%, 20%, 53%, 80%, 100% {
        transform: translate3d(0,0,0);
    }
    40%, 43% {
        transform: translate3d(0, -30px, 0);
    }
    70% {
        transform: translate3d(0, -15px, 0);
    }
    90% {
        transform: translate3d(0, -4px, 0);
    }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-10px); }
    20%, 40%, 60%, 80% { transform: translateX(10px); }
}

@keyframes swing {
    20% { transform: rotate(15deg); }
    40% { transform: rotate(-10deg); }
    60% { transform: rotate(5deg); }
    80% { transform: rotate(-5deg); }
    100% { transform: rotate(0deg); }
}

@keyframes tada {
    0% { transform: scale(1); }
    10%, 20% { transform: scale(0.9) rotate(-3deg); }
    30%, 50%, 70%, 90% { transform: scale(1.1) rotate(3deg); }
    40%, 60%, 80% { transform: scale(1.1) rotate(-3deg); }
    100% { transform: scale(1) rotate(0); }
}

@keyframes wobble {
    0% { transform: translateX(0%); }
    15% { transform: translateX(-25%) rotate(-5deg); }
    30% { transform: translateX(20%) rotate(3deg); }
    45% { transform: translateX(-15%) rotate(-3deg); }
    60% { transform: translateX(10%) rotate(2deg); }
    75% { transform: translateX(-5%) rotate(-1deg); }
    100% { transform: translateX(0%); }
}

@keyframes jello {
    0%, 11.1%, 100% { transform: translate3d(0,0,0); }
    22.2% { transform: skewX(-12.5deg) skewY(-12.5deg); }
    33.3% { transform: skewX(6.25deg) skewY(6.25deg); }
    44.4% { transform: skewX(-3.125deg) skewY(-3.125deg); }
    55.5% { transform: skewX(1.5625deg) skewY(1.5625deg); }
    66.6% { transform: skewX(-0.78125deg) skewY(-0.78125deg); }
    77.7% { transform: skewX(0.390625deg) skewY(0.390625deg); }
    88.8% { transform: skewX(-0.1953125deg) skewY(-0.1953125deg); }
}

/* Animasyon sınıfları */
.bounce { animation: bounce 1s infinite; }
.shake { animation: shake 0.82s cubic-bezier(.36,.07,.19,.97) both; }
.swing { animation: swing 1s ease-in-out infinite; }
.tada { animation: tada 1s ease-in-out infinite; }
.wobble { animation: wobble 1s ease-in-out infinite; }
.jello { animation: jello 1s ease-in-out infinite; }

/* Hover animasyonları */
.hover-lift:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.hover-scale:hover {
    transform: scale(1.05);
}

.hover-rotate:hover {
    transform: rotate(5deg);
}

.hover-glow:hover {
    box-shadow: 0 0 20px var(--primary-color);
}

/* Scroll animasyonları */
.scroll-fade-in {
    opacity: 0;
    transform: translateY(30px);
    transition: all 0.6s ease-out;
}

.scroll-fade-in.visible {
    opacity: 1;
    transform: translateY(0);
}

/* Loading animasyonları */
.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.loading-dots {
    display: inline-block;
}

.loading-dots::after {
    content: '';
    animation: dots 1.5s steps(5, end) infinite;
}

@keyframes dots {
    0%, 20% { content: ''; }
    40% { content: '.'; }
    60% { content: '..'; }
    80%, 100% { content: '...'; }
}
"""
        return css
    
    def generate_complete_css(self) -> str:
        """Tüm CSS stillerini oluştur"""
        css = f"""/*
Merthtmlcss CSS Framework
Oluşturulma Tarihi: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Geliştirici: Mert Doğanay
Versiyon: 3.0
*/

{self.generate_css_variables()}
{self.create_button_styles()}
{self.create_card_styles()}
{self.create_form_styles()}
{self.create_animation_styles()}
{self.create_responsive_styles()}
{self.create_dark_theme_styles()}
{self.create_utility_classes()}
{self.create_advanced_animations()}
"""
        return css
    
    def save_css_file(self, filename: Optional[str] = None) -> str:
        """CSS dosyasını kaydet"""
        if filename:
            self.output_file = filename
        
        css_content = self.generate_complete_css()
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        print(f"✅ CSS dosyası başarıyla oluşturuldu: {self.output_file}")
        return self.output_file
    
    def create_custom_style(self, selector: str, properties: Dict[str, str]) -> str:
        """Özel CSS stili oluştur"""
        css = f"{selector} {{\n"
        for property_name, value in properties.items():
            css += f"    {property_name}: {value};\n"
        css += "}\n\n"
        return css
    
    def add_custom_style(self, selector: str, properties: Dict[str, str]) -> None:
        """Özel stil ekle"""
        self.css_styles[selector] = properties
        print(f"✅ Özel stil eklendi: {selector}")

def main():
    """Ana fonksiyon"""
    print("🎨 Merthtmlcss CSS Yöneticisi v4.0 Başlatılıyor...")
    print("📁 Bulunduğunuz dizindeki dosyalar:", os.listdir('.'))
    
    # CSS yöneticisini oluştur
    config = CSSConfig(
        output_dir="css_output",
        minify=False,
        source_maps=True,
        auto_prefix=True,
        version="4.0",
        author="Mert Doğanay"
    )
    
    css_manager = CSSManager(config)
    
    # Özel CSS değişkenleri ekle
    css_manager.add_css_variable('gradient-primary', 'linear-gradient(45deg, #667eea, #764ba2)')
    css_manager.add_css_variable('gradient-success', 'linear-gradient(45deg, #2ed573, #26de81)')
    css_manager.add_css_variable('gradient-error', 'linear-gradient(45deg, #ff4757, #ff3838)')
    css_manager.add_css_variable('gradient-warning', 'linear-gradient(45deg, #ffa502, #ff9f1a)')
    css_manager.add_css_variable('gradient-info', 'linear-gradient(45deg, #3742fa, #54a0ff)')
    css_manager.add_css_variable('gradient-accent', 'linear-gradient(45deg, #ff6b6b, #feca57)')
    
    # Özel stiller ekle
    css_manager.add_custom_style('.hero-section', {
        'background': 'var(--gradient-primary)',
        'color': 'var(--light-color)',
        'padding': '80px 0',
        'text-align': 'center',
        'position': 'relative',
        'overflow': 'hidden'
    })
    
    css_manager.add_custom_style('.hero-section::before', {
        'content': '""',
        'position': 'absolute',
        'top': '0',
        'left': '0',
        'right': '0',
        'bottom': '0',
        'background': 'var(--gradient-accent)',
        'opacity': '0.1',
        'z-index': '1'
    })
    
    css_manager.add_custom_style('.feature-card', {
        'background': 'var(--light-color)',
        'border-radius': 'var(--border-radius)',
        'padding': '30px',
        'text-align': 'center',
        'box-shadow': 'var(--box-shadow)',
        'transition': 'var(--transition)',
        'position': 'relative',
        'z-index': '2'
    })
    
    css_manager.add_custom_style('.glass-effect', {
        'background': 'rgba(255, 255, 255, 0.1)',
        'backdrop-filter': 'blur(10px)',
        'border': '1px solid rgba(255, 255, 255, 0.2)',
        'border-radius': 'var(--border-radius)'
    })
    
    # CSS dosyasını oluştur
    output_file = css_manager.save_css_file('merthtmlcss-styles.css')
    
    # CSS değişkenlerini dışa aktar
    variables_file = css_manager.export_variables()
    
    print(f"\n🎉 CSS dosyası başarıyla oluşturuldu!")
    print(f"📁 CSS dosyası: {os.path.abspath(output_file)}")
    print(f"📊 CSS değişkenleri: {os.path.abspath(variables_file)}")
    print(f"📊 Toplam CSS değişkeni: {len(css_manager.get_css_variables())}")
    print(f"🎨 Özel stil sayısı: {len(css_manager.css_styles)}")
    
    # HTML örneği oluştur
    html_example = create_advanced_html_example()
    
    # HTML örneğini kaydet
    with open('css-example.html', 'w', encoding='utf-8') as f:
        f.write(html_example)
    
    print(f"📄 HTML örneği oluşturuldu: css-example.html")
    print("\n🚀 Kullanım için:")
    print("1. merthtmlcss-styles.css dosyasını HTML'inize dahil edin")
    print("2. css-example.html dosyasını tarayıcıda açın")
    print("3. CSS sınıflarını kullanmaya başlayın!")
    print("\n✨ Yeni Özellikler:")
    print("   - Karanlık tema desteği")
    print("   - Gelişmiş animasyonlar")
    print("   - Utility sınıfları")
    print("   - Glass morphism efektleri")
    print("   - Responsive tasarım")
    print("   - CSS değişken yönetimi")

def create_advanced_html_example() -> str:
    """Gelişmiş HTML örneği oluştur"""
    return """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merthtmlcss CSS Framework v4.0</title>
    <link rel="stylesheet" href="merthtmlcss-styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header class="hero-section glass-effect">
            <h1 class="glow text-3xl font-bold">Merthtmlcss CSS Framework v4.0</h1>
            <p class="text-lg mt-4">Modern ve responsive CSS framework'ü</p>
            <button class="button button-primary hover-lift" id="startBtn">Başla</button>
        </header>
        
        <div class="grid grid-3">
            <div class="feature-card fade-in delay-1 hover-scale">
                <h3 class="text-xl font-semibold">Modern Tasarım</h3>
                <p>Güncel tasarım trendlerine uygun stiller</p>
                <button class="button button-small" onclick="showFeature('Modern Tasarım')">Detay</button>
            </div>
            <div class="feature-card fade-in delay-2 hover-scale">
                <h3 class="text-xl font-semibold">Responsive</h3>
                <p>Tüm cihazlarda mükemmel görünüm</p>
                <button class="button button-small" onclick="showFeature('Responsive')">Detay</button>
            </div>
            <div class="feature-card fade-in delay-3 hover-scale">
                <h3 class="text-xl font-semibold">Animasyonlar</h3>
                <p>Etkileyici CSS animasyonları</p>
                <button class="button button-small" onclick="showFeature('Animasyonlar')">Detay</button>
            </div>
        </div>
        
        <div class="theme-toggle-section text-center mt-8">
            <button class="button" onclick="toggleTheme()">🌙 Tema Değiştir</button>
        </div>
        
        <div class="animation-showcase mt-8">
            <h2 class="text-2xl font-bold text-center mb-6">Animasyon Gösterisi</h2>
            <div class="flex justify-center items-center gap-4">
                <div class="bounce">🎾</div>
                <div class="shake">📱</div>
                <div class="swing">🎭</div>
                <div class="tada">🎉</div>
                <div class="wobble">🎨</div>
                <div class="jello">🍭</div>
            </div>
        </div>
        
        <div id="notification" class="notification" style="display: none;"></div>
    </div>
    
    <script>
    // Merthtmlcss JavaScript Framework v4.0
    class MerthtmlcssApp {
        constructor() {
            this.notification = document.getElementById('notification');
            this.startBtn = document.getElementById('startBtn');
            this.init();
        }
        
        init() {
            this.setupEventListeners();
            this.loadFeatures();
            this.setupTheme();
            this.setupScrollAnimations();
            console.log("🎨 Merthtmlcss App v4.0 başlatıldı");
        }
        
        setupEventListeners() {
            this.startBtn.addEventListener('click', () => this.handleStart());
            
            // Kart hover efektleri
            document.querySelectorAll('.feature-card').forEach(card => {
                card.addEventListener('mouseenter', () => this.cardHover(card));
                card.addEventListener('mouseleave', () => this.cardLeave(card));
            });
        }
        
        setupTheme() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.classList.add('dark-theme');
            }
        }
        
        setupScrollAnimations() {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('visible');
                    }
                });
            });
            
            document.querySelectorAll('.scroll-fade-in').forEach(el => {
                observer.observe(el);
            });
        }
        
        handleStart() {
            this.startBtn.textContent = 'Başlatıldı! 🚀';
            this.startBtn.classList.add('button-success');
            this.showNotification('Framework başarıyla başlatıldı!', 'success');
            
            setTimeout(() => {
                this.startBtn.textContent = 'Başla';
                this.startBtn.classList.remove('button-success');
            }, 2000);
        }
        
        cardHover(card) {
            card.style.transform = 'scale(1.02)';
            card.style.boxShadow = '0 15px 35px rgba(0,0,0,0.2)';
        }
        
        cardLeave(card) {
            card.style.transform = 'scale(1)';
            card.style.boxShadow = '';
        }
        
        showNotification(message, type = 'info') {
            if (this.notification) {
                this.notification.textContent = message;
                this.notification.className = `notification ${type}`;
                this.notification.style.display = 'block';
                
                setTimeout(() => {
                    this.notification.style.display = 'none';
                }, 3000);
            }
        }
        
        loadFeatures() {
            const features = [
                { name: 'Modern Tasarım', description: 'CSS Grid, Flexbox ve modern layout teknikleri' },
                { name: 'Responsive', description: 'Mobil-first yaklaşım ve breakpoint sistemi' },
                { name: 'Animasyonlar', description: 'CSS keyframes ve transition efektleri' }
            ];
            
            console.log('Özellikler yüklendi:', features);
        }
    }
    
    // Global fonksiyonlar
    function showFeature(featureName) {
        const messages = {
            'Modern Tasarım': 'CSS Grid ve Flexbox ile modern layout oluşturma',
            'Responsive': 'Tüm cihazlarda mükemmel görünüm sağlama',
            'Animasyonlar': 'CSS animasyonları ile etkileyici efektler'
        };
        
        const app = window.merthtmlcssApp;
        if (app) {
            app.showNotification(messages[featureName] || 'Özellik detayı', 'info');
        }
    }
    
    function toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        const app = window.merthtmlcssApp;
        if (app) {
            app.showNotification(`Tema ${isDark ? 'karanlık' : 'aydınlık'} moda geçirildi`, 'success');
        }
    }
    
    // Sayfa yüklendiğinde app'i başlat
    document.addEventListener('DOMContentLoaded', () => {
        window.merthtmlcssApp = new MerthtmlcssApp();
        
        // Kaydedilmiş temayı yükle
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
    });
    </script>
</body>
</html>"""

if __name__ == "__main__":
    main()
    