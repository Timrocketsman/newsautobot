import requests
import xml.etree.ElementTree as ET
import re
import html
import json
import os
from openai import OpenAI

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID = "6983437462"  # тест в ЛС

OPENAI_KEY = "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"
client = OpenAI(api_key=OPENAI_KEY)

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
# Работа с уже опубликованными ссылками
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
# Парсер RSS
# ============================
def parse_rss(url, seen):
    news = []
    try:
        resp = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        for item in root.findall(".//item")[:5]:
            link = item.findtext("link", "").strip()
            if not link or link in seen:
                continue
            title = item.findtext("title", "Без заголовка").strip()
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
            text  = (title + " " + desc).lower()
            if any(kw in text for kw in KEYWORDS):
                news.append({"title": title, "link": link, "desc": desc})
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
    return news

# ============================
# Генерация текста поста с помощью OpenAI
# ============================
def generate_post(title, desc, link):
    prompt = f"""
Ты — редактор новостей по ИИ. На основе заголовка и краткого описания составь красивый, цепляющий пост для Telegram. 
Сделай его в формате:
🔍 {title}

1️⃣ Что случилось?  
[Кратко, 1-2 предложения]

2️⃣ Почему это важно?  
[Почему это значимо, с фокусом на ИИ и технологиях]

4️⃣ Подробности:
🔗 {link}

💡 P.S. Следите за обновлениями! 🚀

Внизу добавь:
<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>

---
Заголовок: {title}
Описание: {desc}
    """
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # быстрая и дешевая генерация
        messages=[
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ и технологиям."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return completion.choices[0].message.content.strip()

# ============================
# Отправка сообщения в Telegram
# ============================
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,  # только тебе в ЛС
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        print("[SUCCESS] Сообщение отправлено")
    else:
        print(f"[ERROR] Telegram {r.status_code}: {r.text}")

# ============================
# Основная логика
# ============================
def main():
    seen = load_seen()
    fresh = []
    for feed in RSS_FEEDS:
        fresh += parse_rss(feed, seen)
        if fresh:  # берём только первую подходящую новость
            break

    if not fresh:
        print("[INFO] Нет новых новостей")
        return

    article = fresh[0]
    seen.add(article["link"])
    save_seen(seen)

    print(f"[INFO] Генерация поста для: {article['title']}")
    post_text = generate_post(article["title"], article["desc"], article["link"])
    send_message(post_text)

if __name__ == "__main__":
    main()
