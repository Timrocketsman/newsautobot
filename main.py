import requests
import xml.etree.ElementTree as ET
import re
import random
import html

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID        = "6983437462"         # для тестирования в ЛС
CHANNEL_ID     = "-1002047105840"     # в готовом виде в канал

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss"
]

KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "AI",
    "модель", "LLM", "GPT", "генерация", "тренд"
]

# ============================
# Парсер RSS без сторонних библиотек
# ============================
def parse_rss(url):
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:10]
        result = []
        for item in items:
            title = item.findtext("title", default="Без заголовка")
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description", default=""))
            link  = item.findtext("link", default="")
            text  = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                result.append({"title": title, "link": link})
        return result
    except:
        return []

# ============================
# Сбор всех новостей
# ============================
def collect_news():
    all_articles = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Парсинг {feed}")
        all_articles += parse_rss(feed)
    return all_articles

# ============================
# Форматирование поста по шаблону
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
        f"<a href=\"https://t.me/BrainAid_bot\">Бот</a>⚫️PerplexityPro⚫️"
        f"<a href=\"https://brainaid.ru/\">Сайт</a>"
    )

# ============================
# Отправка через HTTP API с HTML-разметкой
# ============================
def send(text, to_channel=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID if to_channel else CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code == 200:
        print("[SUCCESS] Сообщение отправлено")
    else:
        print(f"[ERROR] Telegram API {r.status_code}: {r.text}")

# ============================
# Основная логика
# ============================
def main():
    news = collect_news()
    if not news:
        print("[WARNING] Нет новостей по теме ИИ/технологий")
        return
    article = random.choice(news)
    print(f"[INFO] Выбрана новость: {article['title'][:40]}")
    post = format_post(article)
    print("[INFO] Отправка тестового сообщения в ЛС...")
    send(post, to_channel=False)
    # После проверки включите публикацию в канал:
    # send(post, to_channel=True)

if __name__ == "__main__":
    main()
