import os
import requests
import xml.etree.ElementTree as ET
import re
import html
import json

# ============================
# КОНФИГУРАЦИЯ через переменные окружения
# ============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # 8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw
CHAT_ID        = os.getenv("CHAT_ID")        # 6983437462
AI_API_KEY     = os.getenv("AI_API_KEY")     # sk-or-v1-...
AI_MODEL       = os.getenv("AI_MODEL", "deepseek-chat")
AI_URL         = os.getenv("AI_URL", "https://api.deepseek.com/v1/chat/completions")

# RSS-ленты для парсинга
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/artificial_intelligence/"
]

# Ключевые слова для фильтрации
KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация"
]

SEEN_FILE = "seen_links.json"


# ============================
# Работа с файлом seen_links.json
# ============================
def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(links):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(links), f, ensure_ascii=False, indent=2)


# ============================
# Получить одну свежую новость
# ============================
def get_one_news():
    seen = load_seen()
    for url in RSS_FEEDS:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:5]:
                link = item.findtext("link", "").strip()
                if not link or link in seen:
                    continue
                title = item.findtext("title", "Без заголовка").strip()
                desc  = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
                text = (title + " " + desc).lower()
                if any(kw.lower() in text for kw in KEYWORDS):
                    seen.add(link)
                    save_seen(seen)
                    return {"title": title, "desc": desc, "link": link}
        except Exception:
            continue
    return None


# ============================
# Fallback-пост без AI
# ============================
def fallback_post(news):
    return (
        f"🔍 {news['title']}\n\n"
        f"4️⃣ Подробности:\n🔗 {news['link']}\n\n"
        "💡 P.S. Следите за обновлениями! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>'
    )


# ============================
# Сгенерировать пост через DeepSeek API
# ============================
def generate_post(news):
    if not AI_API_KEY:
        return fallback_post(news)

    prompt = (
        f"Ты — редактор новостей по ИИ. Составь Telegram-пост:\n\n"
        f"🔍 {news['title']}\n\n"
        "1️⃣ Что случилось?\n"
        "[1–2 предложения по сути]\n\n"
        "2️⃣ Почему это важно?\n"
        "[значимость для сферы ИИ]\n\n"
        "4️⃣ Подробности:\n"
        f"🔗 {news['link']}\n\n"
        "💡 P.S. Следите за обновлениями! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️'
        '<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️'
        '<a href="https://brainaid.ru/">Сайт</a>\n\n'
        f"Описание: {news['desc']}"
    )

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }

    try:
        resp = requests.post(AI_URL, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            return fallback_post(news)
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return fallback_post(news)


# ============================
# Отправить сообщение через Telegram API
# ============================
def send_message(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("ERROR: TELEGRAM_TOKEN или CHAT_ID не заданы")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "link_preview_options": json.dumps({
            "is_disabled": False,
            "show_above_text": True
        })
    }
    resp = requests.post(url, data=payload, timeout=10)
    if resp.status_code != 200:
        print(f"Telegram API Error {resp.status_code}: {resp.text}")


# ============================
# MAIN
# ============================
def main():
    news = get_one_news()
    if not news:
        print("INFO: Нет свежих новостей по ИИ")
        return

    print(f"INFO: Генерация поста для: {news['title']}")
    post = generate_post(news)
    send_message(post)
    print("DONE: Пост отправлен")


if __name__ == "__main__":
    main()
