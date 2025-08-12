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
CHAT_ID        = "6983437462"       # тестирование в ЛС
CHANNEL_ID     = "-1002047105840"   # после настройки — в канал

# Список из ~100 русскоязычных RSS-ленточек по ИИ и технологиям
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    # ... добавьте другие современные тематические ленты:
    "https://tproger.ru/rss",
    "https://geekbrains.ru/posts/rss",
    "https://function.python/rss",  # пример
    # заполняйте до 100 URL
]

KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "AI",
    "модель", "LLM", "GPT", "генерация", "тренд",
    "нейро", "промпт", "инференс", "компьютерное зрение",
    "NLP", "Stable Diffusion", "Midjourney", "Claude"
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
# RSS-парсер
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
        print(f"[ERROR] Парсинг {url}: {e}")
    return articles

# ============================
# Сбор новостей со всех лент
# ============================
def collect_news():
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Парсинг {feed}")
        fresh += parse_rss(feed, seen)
    return fresh, seen

# ============================
# Форматирование поста
# ============================
def format_post(article):
    title = article["title"]
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    link = article["link"]
    return (
        f"🔍 {html.escape(title)}\n\n"
        f"4️⃣ Подробности:\n"
        f"🔗 {html.escape(link)}\n\n"
        f"💡 P.S. Следите за обновлениями! 🚀\n\n"
        f"<a href=\"https://t.me/BrainAid_bot\">Бот</a>⚫️"
        f"<a href=\"https://t.me/m/h5Kv1jd9MWMy\">PerplexityPro</a>⚫️"
        f"<a href=\"https://brainaid.ru/\">Сайт</a>"
    )

# ============================
# Отправка сообщения
# ============================
def send(text, to_channel=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID if to_channel else CHAT_ID,
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
    print(f"[INFO] Выбрана новость: {article['title'][:40]}")
    # помечаем как увиденную
    seen.add(article["link"])
    save_seen(seen)
    post = format_post(article)
    print("[INFO] Отправка тестового сообщения в ЛС...")
    send(post, to_channel=False)
    # для публикации в канал включите:
    # send(post, to_channel=True)

if __name__ == "__main__":
    main()
