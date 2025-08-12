import requests
import xml.etree.ElementTree as ET
import re
import html
import json
import os

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID        = "6983437462"  # тестирование в ЛС

# OpenAI HTTP API ключ
OPENAI_API_KEY = "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"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://tproger.ru/rss",
    "https://cnews.ru/xml/cnews.rss",
    "https://proglib.io/rss",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/machine-learning/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://habr.com/ru/rss/hub/data-science/"
]

KEYWORDS = [
    "ИИ","искусственный интеллект","нейросеть",
    "машинное обучение","deep learning","ai",
    "модель","llm","gpt","генерация","тренд",
    "нейро","промпт","инференс","компьютерное зрение",
    "nlp","stable diffusion","midjourney","claude",
    "чат-бот","чатбот","qwen","gemini","перплекс"
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
# Парсинг RSS-ленты
# ============================
def parse_rss(feed_url, seen):
    items = []
    try:
        resp = requests.get(feed_url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for node in root.findall(".//item")[:5]:
            link = node.findtext("link","").strip()
            if not link or link in seen:
                continue
            title = node.findtext("title","Без заголовка").strip()
            desc  = re.sub(r"<[^>]+>","", node.findtext("description","")).strip()
            text  = (title + " " + desc).lower()
            if any(kw.lower() in text for kw in KEYWORDS):
                items.append({"title": title, "desc": desc, "link": link})
    except Exception as e:
        print(f"[ERROR] Парсинг {feed_url}: {e}")
    return items

# ============================
# Выбор одной свежей новости
# ============================
def get_one_news():
    seen = load_seen()
    for feed in RSS_FEEDS:
        for item in parse_rss(feed, seen):
            seen.add(item["link"])
            save_seen(seen)
            return item
    return None

# ============================
# Генерация текста поста через OpenAI HTTP API
# ============================
def generate_post(item):
    prompt = (
        f"Ты — редактор новостей по ИИ. На основе заголовка и описания сформируй Telegram-пост:\n\n"
        f"🔍 {item['title']}\n\n"
        f"Описание: {item['desc']}\n\n"
        f"4️⃣ Подробности:\n🔗 {item['link']}\n\n"
        f"💡 P.S. Следите за обновлениями! 🚀\n\n"
        f"Внизу добавь:\n"
        f"<a href='https://t.me/BrainAid_bot'>Бот</a>⚫️"
        f"<a href='https://t.me/m/h5Kv1jd9MWMy'>PerplexityPro</a>⚫️"
        f"<a href='https://brainaid.ru/'>Сайт</a>"
    )
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Ты — профессиональный редактор."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    r = requests.post(OPENAI_URL, headers=headers, json=data, timeout=30)
    r.raise_for_status()
    resp = r.json()
    return resp["choices"][0]["message"]["content"]

# ============================
# Отправка сообщения в Telegram
# ============================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": html.escape(text, quote=False),
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code != 200:
        print(f"[ERROR] Telegram {r.status_code}: {r.text}")

# ============================
# Основная логика
# ============================
def main():
    item = get_one_news()
    if not item:
        print("[INFO] Новостей не найдено")
        return
    print(f"[INFO] Генерируем пост для: {item['title']}")
    post = generate_post(item)
    send_message(post)
    print("[DONE] Пост отправлен")

if __name__ == "__main__":
    main()
