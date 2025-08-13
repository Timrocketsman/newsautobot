import os
import requests
import xml.etree.ElementTree as ET
import re
import json
try:
    from bs4 import BeautifulSoup  # Для HTML-парсинга (установи beautifulsoup4)
except ImportError:
    print("[WARN] BeautifulSoup не установлен — HTML-парсинг пропущен")
    BeautifulSoup = None

# ... (остальной код без изменений, как в предыдущей версии)

def get_one_news():
    seen = load_seen()
    candidates = []
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            if 'xml' in r.headers.get('Content-Type', ''):
                # RSS-парсинг
                root = ET.fromstring(r.content)
                # ... (как раньше)
            elif BeautifulSoup:
                # HTML-парсинг
                soup = BeautifulSoup(r.content, 'lxml')
                # ... (как раньше)
            else:
                print(f"[WARN] BeautifulSoup не доступен — пропускаем HTML {url}")
                continue
        except Exception as e:
            print(f"[ERROR] Парсинг {url}: {e}")
            continue
    # ... (остальное как раньше)

# ... (остальные функции без изменений)
