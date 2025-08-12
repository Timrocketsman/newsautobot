import requests
import xml.etree.ElementTree as ET
import re
import random

# --------------------------
# Конфигурация
# --------------------------
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"  # Обязательно строка с '-' для приватного канала

# RSS источники
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://vc.ru/rss/all",
    "https://feeds.feedburner.com/oreilly/radar",
    "https://www.wired.com/feed/rss"
]

# --------------------------
# Простой RSS парсер
# --------------------------
def parse_rss_simple(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0'
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall('.//item')[:5]
        articles = []
        for item in items:
            title = item.findtext('title', 'Без заголовка')
            desc = item.findtext('description', 'Без описания')
            link = item.findtext('link', '')
            articles.append({
                'title': title,
                'description': desc,
                'link': link
            })
        return articles
    except Exception as e:
        print(f"[ERROR] Парсинг {url}: {e}")
        return []

# --------------------------
# Получение новостей
# --------------------------
def get_all_news():
    all_articles = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Парсинг: {feed}")
        all_articles += parse_rss_simple(feed)
    return all_articles

# --------------------------
# Очистка HTML
# --------------------------
def clean_html(text):
    return re.sub(r'<[^>]+>', '', text)

# --------------------------
# Форматирование
# --------------------------
def format_news(article):
    title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
    desc = clean_html(article['description'])[:200] + "..."
    return (
        f"🔍 {title}\n\n"
        f"1️⃣ Что случилось?\n{desc}\n\n"
        "2️⃣ Как это работает?\n"
        "📰 Свежая информация из мира технологий и ИИ\n\n"
        "3️⃣ Чем важно?\n"
        "✅ Актуальные технологические тренды\n"
        "✅ Новости индустрии\n\n"
        f"4️⃣ Подробности:\n🔗 {article['link']}\n\n"
        "💡 P.S. Оставайтесь в курсе последних новостей! 🚀"
    )

# --------------------------
# Публикация через HTTP API
# --------------------------
def post_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHANNEL_ID,
        'text': text,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code == 200:
        print("[SUCCESS] Отправлено в канал")
        return True
    else:
        print(f"[ERROR] Telegram API {resp.status_code}: {resp.text}")
        return False

# --------------------------
# Основная логика
# --------------------------
def main():
    print("[INFO] Запуск бота...")
    articles = get_all_news()
    if not articles:
        print("[WARNING] Нет новостей")
        return
    article = random.choice(articles)
    print(f"[INFO] Выбрана новость: {article['title'][:40]}")
    text = format_news(article)
    post_to_telegram(text)

if __name__ == "__main__":
    main()
