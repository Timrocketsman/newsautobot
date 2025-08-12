import os
import time
import json
import random
import requests
import xml.etree.ElementTree as ET
import re
import html
from typing import List
import openai  # pip install openai

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID        = "6983437462"         # тестирование в ЛС
CHANNEL_ID     = "-1002047105840"     # публикация в канал после тестов

# OpenAI API для генерации текста по шаблону дополняющего пост
openai.api_key = "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"

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    # …дополнить до 100
]

KEYWORDS = [
    "ИИ","искусственный интеллект","нейросеть",
    "машинное обучение","deep learning","ai",
    "модель","llm","gpt","генерация","тренд"
]

SEEN_FILE = "seen_links.json"

# ============================
# Утилиты для seen_links.json
# ============================
def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

# ============================
# Парсинг RSS + фильтрация
# ============================
def parse_rss(url: str, seen: set) -> List[dict]:
    items = []
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for node in root.findall(".//item")[:10]:
            link = node.findtext("link","").strip()
            if not link or link in seen:
                continue
            title = node.findtext("title","Без заголовка").strip()
            desc = re.sub(r"<[^>]+>","",node.findtext("description","")).strip()
            text = (title+" "+desc).lower()
            if any(kw in text for kw in KEYWORDS):
                items.append({"title":title,"link":link})
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
    return items

# ============================
# Сбор новых новостей
# ============================
def collect_fresh() -> (List[dict], set):
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        fresh += parse_rss(feed, seen)
    return fresh, seen

# ============================
# Генерация дополняющего текста через OpenAI
# ============================
PROMPT_TEMPLATE = """
Ты — редактор новостей по ИИ. Допиши к этому заголовку краткий интригующий анонс (1–2 предложения):
"{title}"
Добавь призыв перейти по ссылке.
"""

def generate_annotation(title: str) -> str:
    prompt = PROMPT_TEMPLATE.replace("{title}", title)
    resp = openai.Completion.create(
        model="gpt-3.5-turbo",
        prompt=prompt,
        max_tokens=50,
        temperature=0.7
    )
    return resp.choices[0].text.strip()

# ============================
# Формирование сообщения
# ============================
def format_message(item: dict) -> str:
    annotation = generate_annotation(item["title"])
    link = item["link"]
    msg = f"{html.escape(link)}\n\n"
    msg += f"🔍 {html.escape(item['title'])}\n\n"
    msg += f"{html.escape(annotation)}\n\n"
    msg += "💡 P.S. Следите за обновлениями! 🚀\n\n"
    msg += (
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>'
    )
    return msg

# ============================
# Отправка в Telegram
# ============================
def send_to_telegram(text: str, to_channel=False):
    chat_id = CHANNEL_ID if to_channel else CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id":chat_id,
        "text":text,
        "parse_mode":"HTML",
        "disable_web_page_preview":False
    }
    r = requests.post(url, data=data, timeout=10)
    if r.status_code!=200:
        print(f"[ERROR] Telegram {r.status_code}: {r.text}")

# ============================
# Задача автопостинга
# ============================
def job():
    fresh, seen = collect_fresh()
    if not fresh:
        print("[INFO] Нет новых новостей")
        return
    for item in fresh:
        msg = format_message(item)
        send_to_telegram(msg, to_channel=False)  # тест в ЛС
        seen.add(item["link"])
        time.sleep(1)
    save_seen(seen)

# ============================
# Главный цикл: каждый час
# ============================
if __name__=="__main__":
    print("[INFO] Автопостинг запущен — каждые 3600сек")
    while True:
        job()
        time.sleep(3600)
