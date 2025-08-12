import requests
import xml.etree.ElementTree as ET
import re
import time
import html
import json
import os
import random

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID        = "6983437462"       # тестирование в ЛС
CHANNEL_ID     = "-1002047105840"   # публикация в канал после тестов

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://tproger.ru/rss",
    "https://geekbrains.ru/posts/rss",
    "https://cnews.ru/xml/cnews.rss",
    "https://www.ixbt.com/export/news.xml",
    "https://proglib.io/rss",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/machine-learning/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://habr.com/ru/rss/hub/data-science/",
    # ... добавьте остальные до ~100 лент
]

KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация", "тренд",
    "нейро", "промпт", "инференс", "компьютерное зрение",
    "nlp", "stable diffusion", "midjourney", "claude",
    "чат-бот", "чатбот", "qwen", "gemini", "перплекс"
]

SEEN_FILE = "seen_links.json"


# ============================
# Загрузка/сохранение просмотренных ссылок
# ============================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)


# ============================
# Парсинг RSS-ленты с фильтрацией
# ============================
def parse_rss(feed_url, seen):
    new_items = []
    try:
        resp = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:10]:
            link = item.findtext("link", "").strip()
            if not link or link in seen:
                continue
            title = item.findtext("title", "Без заголовка").strip()
            desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
            text = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                new_items.append({"title": title, "link": link})
    except Exception as e:
        print(f"[ERROR] RSS parse {feed_url}: {e}")
    return new_items


# ============================
# Сбор всех новых новостей
# ============================
def collect_fresh_news():
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Parsing {feed}")
        fresh += parse_rss(feed, seen)
    return fresh, seen


# ============================
# Формирование текста сообщения
# ============================
def format_message(item):
    title = item["title"]
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    link = item["link"]
    msg = f"{html.escape(link)}\n\n"
    msg += f"🔍 {html.escape(title)}\n\n"
    # Краткая структура без AI-генерации
    msg += "💡 Подробнее по ссылке выше.\n\n"
    msg += (
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>'
    )
    return msg


# ============================
# Отправка в Telegram через HTTP API
# ============================
def send_to_telegram(text, to_channel=False):
    chat_id = CHANNEL_ID if to_channel else CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code == 200:
        print("[SUCCESS] Sent")
    else:
        print(f"[ERROR] Telegram {r.status_code}: {r.text}")


# ============================
# Задача автопостинга: отправить все новые новости
# ============================
def job():
    fresh, seen = collect_fresh_news()
    if not fresh:
        print("[INFO] No fresh AI/tech news")
        return
    for item in fresh:
        msg = format_message(item)
        send_to_telegram(msg, to_channel=False)  # тест в ЛС
        seen.add(item["link"])
        time.sleep(1)
    save_seen(seen)
    print(f"[INFO] Posted {len(fresh)} items")


# ============================
# Основной цикл: выполнять job() каждый час
# ============================
def main():
    print("[INFO] Auto-post scheduler started: every hour")
    while True:
        job()
        time.sleep(3600)


if __name__ == "__main__":
    main()
