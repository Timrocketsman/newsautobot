import requests
import xml.etree.ElementTree as ET
import re
import random
import html
import json
import os
import schedule
import time

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"

# Для тестирования — отправка в ЛС
CHAT_ID        = "6983437462"       
# Для публикации в канал после тестов
CHANNEL_ID     = "-1002047105840"   

# RSS-ленты
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
    "https://habr.com/ru/rss/hub/data-science/"
]

# Ключевые слова (фильтрация)
KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация", "тренд",
    "нейро", "промпт", "инференс", "компьютерное зрение",
    "nlp", "stable diffusion", "midjourney", "claude",
    "чат-бот", "чатбот", "qwen", "gemini", "перплекс"
]

# Файл для хранения уже отправленных новостей
SEEN_FILE = "seen_links.json"

# ============================
# Функции
# ============================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

def parse_rss(url, seen):
    articles = []
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:10]:
            link = item.findtext("link", "").strip()
            if not link or link in seen:
                continue
            title = item.findtext("title", "").strip()
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
            text  = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                articles.append({"title": title, "link": link})
    except Exception as e:
        print(f"[ERROR] RSS {url}: {e}")
    return articles

def collect_news():
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Чтение: {feed}")
        fresh += parse_rss(feed, seen)
    return fresh, seen

def format_message(article):
    title = article["title"]
    if len(title) > 80:
        title = title[:77] + "..."
    link = article["link"]
    msg = f"{html.escape(link)}\n\n"
    msg += f"🔍 {html.escape(title)}\n\n"
    msg += "💡 P.S. Следите за обновлениями! 🚀\n\n"
    msg += (
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>'
    )
    return msg

def send_message(text, to_channel=False):
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
        print("[SUCCESS] Отправлено")
    else:
        print(f"[ERROR] {r.status_code}: {r.text}")

# ============================
# Основная задача автопостинга
# ============================
def job():
    fresh, seen = collect_news()
    if not fresh:
        print("[WARNING] Нет новых новостей")
        return
    article = random.choice(fresh)
    seen.add(article["link"])
    save_seen(seen)
    msg = format_message(article)
    send_message(msg, to_channel=False)  # сейчас только в ЛС
    # Для канала: send_message(msg, to_channel=True)

# ============================
# Планировщик (каждый час)
# ============================
def main():
    print("[INFO] Режим автопостинга запущен (каждый час)")
    schedule.every(1).hours.do(job)
    
    # Выполним сразу при старте
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
