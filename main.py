import requests
import xml.etree.ElementTree as ET
import re
import random
import html
import json
import os

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID        = "6983437462"       # для тестирования в личные сообщения
CHANNEL_ID     = "-1002047105840"   # для публикации в канал после проверки

# Расширенный список русскоязычных тематических RSS-лент (~100 примеров).
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://tproger.ru/rss",
    "https://geekbrains.ru/posts/rss",
    "https://cnews.ru/xml/cnews.rss",
    "https://www.vedomosti.ru/rss/news.xml",
    "https://www.computerra.ru/rss.xml",
    "https://3dnews.ru/news/rss",
    "https://www.ixbt.com/export/news.xml",
    "https://www.securitylab.ru/_services/export/rss2/news/",
    "https://vc.ru/rss/technology",
    "https://dou.ua/feed/",
    "https://proglib.io/rss",
    "https://habr.com/ru/rss/hub/machine-learning/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://habr.com/ru/rss/hub/data-science/",
    # ... добавьте остальные ленты
]

# Ключевые слова для фильтрации
KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "ai", "deep learning",
    "модель", "llm", "gpt", "генерация", "тренд",
    "нейро", "промпт", "инференс", "компьютерное зрение",
    "nlp", "stable diffusion", "midjourney", "claude",
    "чат-бот", "чатбот", "qwen", "gemini", "перплекс"
]

SEEN_FILE = "seen_links.json"

# ============================
# Загрузка и сохранение просмотренных ссылок
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
# Парсер RSS с фильтрацией и учетом дублей
# ============================
def parse_rss(url, seen):
    articles = []
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:10]
        for item in items:
            link = item.findtext("link", default="").strip()
            if not link or link in seen:
                continue
            title = item.findtext("title", default="Без заголовка").strip()
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description", default="")).strip()
            text  = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                articles.append({"title": title, "link": link})
    except Exception as e:
        print(f"[ERROR] Ошибка парсинга {url}: {e}")
    return articles

# ============================
# Сбор новых новостей
# ============================
def collect_news():
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Парсинг {feed}")
        fresh += parse_rss(feed, seen)
    return fresh, seen

# ============================
# Формирование текста: ссылка сверху, текст снизу
# ============================
def format_message(article):
    title = article["title"]
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    link = article["link"]
    # Сначала ссылка, чтобы превью показывалось вверху
    msg = f"{html.escape(link)}\n\n"
    msg += f"🔍 {html.escape(title)}\n\n"
    msg += "💡 P.S. Следите за обновлениями! 🚀\n\n"
    msg += (
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>'
    )
    return msg

# ============================
# Отправка через Telegram HTTP API
# ============================
def send_message(text, to_channel=False):
    chat_id = CHANNEL_ID if to_channel else CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code == 200:
        print("[SUCCESS] Сообщение отправлено")
    else:
        print(f"[ERROR] Telegram API {resp.status_code}: {resp.text}")

# ============================
# Основная логика
# ============================
def main():
    fresh, seen = collect_news()
    if not fresh:
        print("[WARNING] Нет новых релевантных новостей")
        return
    article = random.choice(fresh)
    seen.add(article["link"])
    save_seen(seen)

    print(f"[INFO] Выбрана новость: {article['title'][:40]}")
    message = format_message(article)
    print("[INFO] Отправка тестового сообщения в ЛС...")
    send_message(message, to_channel=False)
    # Для публикации в канал после проверки:
    # send_message(message, to_channel=True)

if __name__ == "__main__":
    main()
