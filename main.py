import requests
import xml.etree.ElementTree as ET
import re
import random
import html

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID = "6983437462"        # для тестирования — личные сообщения
CHANNEL_ID = "-1002047105840" # после настройки — в канал

# Русскоязычные RSS-ленты
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss"
]

# ============================
# Парсер RSS без сторонних библиотек
# ============================
def parse_rss(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        lst = []
        for item in items:
            title = item.findtext("title", default="Без заголовка")
            desc  = item.findtext("description", default="Без описания")
            # очистка HTML-тегов
            desc = re.sub(r"<[^>]+>", "", desc)
            link  = item.findtext("link", default="")
            lst.append({"title": title, "description": desc, "link": link})
        return lst
    except Exception as e:
        print(f"[ERROR] Парсинг {url}: {e}")
        return []

# ============================
# Сбор новостей
# ============================
def collect_news():
    all_articles = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Чтение {feed}")
        all_articles.extend(parse_rss(feed))
    return all_articles

# ============================
# Форматирование поста по шаблону
# ============================
def format_post(a):
    title = a["title"]
    if len(title) > 80:
        title = title[:77].rstrip() + "..."
    description = a["description"]
    if len(description) > 300:
        description = description[:297].rstrip() + "..."
    return (
        f"🔍 {title}\n\n"
        f"1️⃣ Что случилось?\n{description}\n\n"
        f"2️⃣ Как это работает?\n"
        "Сбор данных из RSS-лент и автоматическая публикация.\n\n"
        f"3️⃣ Чем лучше аналогов?\n"
        "✅ Автоматическая работа 24/7\n"
        "\n✅ Только русскоязычные источники\n\n"
        f"4️⃣ Подробности:\n🔗 {a['link']}\n\n"
        f"5️⃣ Источник:\n📌 RSS-лента\n\n"
        "💡 P.S. Следите за обновлениями! 🚀\n\n"
        "Бот⚫️PerplexityPro⚫️Сайт\n"
    )

# ============================
# Отправка сообщения через HTTP API с экранированием HTML
# ============================
def send(text, to_channel=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    safe_text = html.escape(text)
    payload = {
        "chat_id": CHANNEL_ID if to_channel else CHAT_ID,
        "text": safe_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code != 200:
        print(f"[ERROR] Telegram {resp.status_code}: {resp.text}")
    else:
        print("[SUCCESS] Отправлено")

# ============================
# Основная логика
# ============================
def main():
    news = collect_news()
    if not news:
        print("[WARNING] Нет новостей")
        return
    article = random.choice(news)
    print(f"[INFO] Выбрана: {article['title'][:40]}")
    post = format_post(article)
    print("[INFO] Отправка тестового сообщения в ЛС...")
    send(post, to_channel=False)
    # после проверки отправить в канал:
    # send(post, to_channel=True)

if __name__ == "__main__":
    main()
