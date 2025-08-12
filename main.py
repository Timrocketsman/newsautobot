import requests
import xml.etree.ElementTree as ET
import re
import random
import html
import json
import os
import time
from datetime import datetime, timedelta

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID     = "-1002047105840"   # канал для публикации

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    # … добавьте свои ленты
]

KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "ai", "deep learning",
    "gpt", "генерация", "тренд"
]

SEEN_FILE = "seen_links.json"

# ============================
# Загрузка/сохранение просмотренных ссылок
# ============================
def load_seen():
    if os.path.exists(SEEN_FILE):
        return set(json.load(open(SEEN_FILE, encoding="utf-8")))
    return set()

def save_seen(seen):
    json.dump(list(seen), open(SEEN_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ============================
# Парсер RSS + фильтрация
# ============================
def parse_rss(url, seen):
    out = []
    try:
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for item in root.findall(".//item")[:10]:
            link  = item.findtext("link","").strip()
            if not link or link in seen:
                continue
            title = item.findtext("title","Без заголовка").strip()
            desc  = re.sub(r"<[^>]+>","", item.findtext("description","")).strip()
            text  = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                out.append({"title": title, "link": link})
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
    return out

# ============================
# Сбор новых новостей
# ============================
def collect_news():
    seen = load_seen()
    fresh = []
    for rss in RSS_FEEDS:
        fresh += parse_rss(rss, seen)
    return fresh, seen

# ============================
# Форматирование текста
# ============================
def format_post(article):
    title = article["title"]
    if len(title)>80:
        title = title[:77].rstrip()+"..."
    link = article["link"]
    return (
        f"{html.escape(link)}\n\n"
        f"🔍 {html.escape(title)}\n\n"
        f"💡 P.S. Следите за обновлениями! 🚀\n\n"
        f"<a href=\"https://t.me/BrainAid_bot\">Бот</a>⚫️"
        f"<a href=\"https://t.me/m/h5Kv1jd9MWMy\">PerplexityPro</a>⚫️"
        f"<a href=\"https://brainaid.ru/\">Сайт</a>"
    )

# ============================
# Отправка с отложенной публикацией
# ============================
def schedule_post(text, post_time: datetime):
    """
    Отправить сообщение в канал не сейчас, а в указанный момент post_time.
    Telegram Bot API (v6.7+) поддерживает параметр schedule_date.
    """
    ts = int(post_time.timestamp())
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "schedule_date": ts
    }
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code == 200:
        print(f"[SUCCESS] Запланировано на {post_time}")
    else:
        print(f"[ERROR] Telegram {resp.status_code}: {resp.text}")

# ============================
# Основная логика
# ============================
def main():
    news, seen = collect_news()
    if not news:
        print("[WARNING] Нет новых новостей")
        return

    article = random.choice(news)
    seen.add(article["link"])
    save_seen(seen)

    post_text = format_post(article)
    # Запланировать публикацию через 1 час от текущего времени:
    publish_time = datetime.utcnow() + timedelta(hours=1)
    schedule_post(post_text, publish_time)

if __name__ == "__main__":
    main()
