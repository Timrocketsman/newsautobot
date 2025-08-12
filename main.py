import requests
import xml.etree.ElementTree as ET
import re
import random

# ——————————————————————————
#  Конфигурация
# ——————————————————————————
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID      = "-1002047105840"

# Берём только русскоязычные RSS
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss"
]

# ——————————————————————————
#  Простой RSS-парсер без сторонних библиотек
# ——————————————————————————
def parse_rss(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        articles = []
        for item in items:
            title = item.findtext("title", default="Без заголовка")
            desc  = item.findtext("description", default="Без описания")
            link  = item.findtext("link", default="")
            articles.append({
                "title": title,
                "description": re.sub(r"<[^>]+>", "", desc),
                "link": link
            })
        return articles

    except Exception as e:
        print(f"[ERROR] Парсинг {url}: {e}")
        return []

# ——————————————————————————
#  Сбор всех новостей
# ——————————————————————————
def collect_news():
    result = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Чтение RSS: {feed}")
        result.extend(parse_rss(feed))
    return result

# ——————————————————————————
#  Форматирование по вашему шаблону
# ——————————————————————————
def format_post(article):
    t = article["title"]
    summary = article["description"][:200].rstrip(" .") + "..."
    return (
        f"🔍 {t}\n\n"
        f"1️⃣ Что случилось?\n{summary}\n\n"
        f"2️⃣ Как это работает?\n"
        f"Сбор и анализ информации из источников RSS.\n\n"
        f"3️⃣ Чем лучше аналогов?\n"
        f"✅ Автоматизация публикаций\n"
        f"\n✅ Только актуальные новости\n\n"
        f"4️⃣ Подробности:\n🔗 {article['link']}\n\n"
        f"5️⃣ Источник:\n"
        f"📌 RSS-лента\n\n"
        f"💡 P.S. Следите за обновлениями! 🚀\n\n"
        f"[Бот](https://t.me/BrainAid_bot) | [Сайт](https://brainaid.ru/)"
    )

# ——————————————————————————
#  Отправка в Telegram через HTTP API
# ——————————————————————————
def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code == 200:
        print("[SUCCESS] Опубликовано")
    else:
        print(f"[ERROR] Telegram API {resp.status_code}: {resp.text}")

# ——————————————————————————
#  Главная логика
# ——————————————————————————
def main():
    articles = collect_news()
    if not articles:
        print("[WARNING] Нет новостей")
        return

    article = random.choice(articles)
    print(f"[INFO] Выбрана: {article['title'][:50]}")
    post = format_post(article)
    print("[INFO] Публикация...")
    post_to_telegram(post)

if __name__ == "__main__":
    main()
