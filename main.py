import requests
import xml.etree.ElementTree as ET
import re
import html
import json
import os

# ============================
# Конфигурация (через переменные окружения!)
# ============================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
AI_API_KEY     = os.getenv("AI_API_KEY")        # DeepSeek ключ
AI_MODEL       = os.getenv("AI_MODEL", "deepseek-chat")
AI_URL         = os.getenv("AI_URL", "https://api.deepseek.com/v1/chat/completions")

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/artificial_intelligence/"
]

KEYWORDS = [
    "ИИ", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация"
]

SEEN_FILE = "seen_links.json"

# ============================
# Работа с просмотренными ссылками
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
# Поиск одной свежей новости
# ============================
def get_one_news():
    seen = load_seen()
    for feed_url in RSS_FEEDS:
        try:
            resp = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:5]:
                link = item.findtext("link", "").strip()
                if not link or link in seen:
                    continue
                title = item.findtext("title", "Без заголовка").strip()
                desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
                combined = (title + " " + desc).lower()
                if any(kw.lower() in combined for kw in KEYWORDS):
                    seen.add(link)
                    save_seen(seen)
                    return {"title": title, "desc": desc, "link": link}
        except Exception as e:
            print(f"[ERROR] Парсинг RSS {feed_url}: {e}")
    return None

# ============================
# Генерация поста через DeepSeek API
# ============================
def generate_post(news):
    if not AI_API_KEY:
        print("[WARN] AI_API_KEY не задан — используем шаблон")
        return fallback_post(news)

    prompt = f"""
Ты — редактор новостей по ИИ. Составь Telegram-пост:

🔍 {news['title']}

1️⃣ Что случилось?
[1-2 предложения по сути]

2️⃣ Почему это важно?
[значимость для ИИ и технологий]

4️⃣ Подробности:
🔗 {news['link']}

💡 P.S. Следите за обновлениями! 🚀

<a href="https://t.me/BrainAid_bot">Бот</a>⚫️
<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️
<a href="https://brainaid.ru/">Сайт</a>

---
Краткое описание: {news['desc']}
"""

    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    data = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 400
    }
    try:
        response = requests.post(AI_URL, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            print(f"[ERROR] AI API {response.status_code}: {response.text}")
            return fallback_post(news)
        content = response.json()
        return content["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[ERROR] AI API Error: {e}")
        return fallback_post(news)

# ============================
# Fallback пост без AI
# ============================
def fallback_post(news):
    return f"""🔍 {news['title']}

4️⃣ Подробности:
🔗 {news['link']}

💡 P.S. Следите за обновлениями! 🚀

<a href="https://t.me/BrainAid_bot">Бот</a>⚫️
<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️
<a href="https://brainaid.ru/">Сайт</a>"""

# ============================
# Отправка сообщения через Telegram API
# ============================
def send_message(text):
    if not TELEGRAM_TOKEN:
        print("[ERROR] TELEGRAM_TOKEN не задан")
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
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code != 200:
        print(f"[ERROR] Telegram API {r.status_code}: {r.text}")
    else:
        print("[OK] Пост отправлен")

# ============================
# MAIN
# ============================
def main():
    news = get_one_news()
    if not news:
        print("[INFO] Нет свежих новостей")
        return
    print(f"[INFO] Генерация поста для: {news['title']}")
    post_text = generate_post(news)
    send_message(post_text)

if __name__ == "__main__":
    main()
