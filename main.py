import requests
import xml.etree.ElementTree as ET
import re
import html
import json
import os
import base64

# ============================
# Конфигурация (зашифрованная)
# ============================
def get_config():
    # Зашифрованные конфиги (base64 + простое смещение)
    encrypted_data = {
        'tg': 'ODI0Mjg2MDg4MjpBQUdfazEzUmQyV0lTREwyV0w5VzJDLXpDb1F2ZlVSVWtmUXc=',
        'chat': 'Njk4MzQzNzQ2Mg==',
        'ai_key': 'c2stb3ItdjEtZDMyNDc3OWQyMDk3OTE0NGFjNGI5ODcxZDUyMDk3NTJkYzM4MTBkYjg3N2E3YTQ5NDMzNzEwNWVjNmU1Zjlh',
        'ai_model': 'ZGVlcHNlZWsvZGVlcHNlZWstY2hhdC12My0=',
        'ai_url': 'aHR0cHM6Ly9hcGkuZGVlcHNlZWsuY29tL3YxL2NoYXQvY29tcGxldGlvbnM='
    }
    
    def decode(s):
        return base64.b64decode(s).decode('utf-8')
    
    return {
        'TELEGRAM_TOKEN': decode(encrypted_data['tg']),
        'CHAT_ID': decode(encrypted_data['chat']),
        'AI_API_KEY': decode(encrypted_data['ai_key']),
        'AI_MODEL': decode(encrypted_data['ai_model']),
        'AI_URL': decode(encrypted_data['ai_url'])
    }

# Получаем конфиг
CONFIG = get_config()

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/artificial_intelligence/"
]

KEYWORDS = [
    "ИИ","искусственный интеллект","нейросеть",
    "машинное обучение","deep learning","ai",
    "модель","llm","gpt","генерация"
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
                desc  = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
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
    prompt = f"""
Ты — редактор новостей по ИИ. Составь привлекательный Telegram-пост:

🔍 {news['title']}

1️⃣ Что случилось?
[1-2 предложения по сути]

2️⃣ Почему это важно?
[значимость для сферы ИИ/технологий]

4️⃣ Подробности:
🔗 {news['link']}

💡 P.S. Следите за обновлениями! 🚀

<a href="https://t.me/BrainAid_bot">Бот</a>⚫️
<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️
<a href="https://brainaid.ru/">Сайт</a>

---
Описание новости: {news['desc']}
"""
    headers = {
        "Authorization": f"Bearer {CONFIG['AI_API_KEY']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": CONFIG['AI_MODEL'],
        "messages": [
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ и технологиям."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    response = requests.post(CONFIG['AI_URL'], headers=headers, json=data, timeout=30)
    response.raise_for_status()
    content = response.json()
    return content["choices"][0]["message"]["content"]


# ============================
# Отправка сообщения через Telegram API
# ============================
def send_message(text):
    url = f"https://api.telegram.org/bot{CONFIG['TELEGRAM_TOKEN']}/sendMessage"
    payload = {
        "chat_id": CONFIG['CHAT_ID'],
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
        print(f"[ERROR] Telegram API {resp.status_code}: {resp.text}")
    else:
        print("[SUCCESS] Сообщение отправлено")


# ============================
# Главная функция
# ============================
def main():
    news = get_one_news()
    if not news:
        print("[INFO] Новостей по теме ИИ не найдено")
        return

    print(f"[INFO] Генерация поста для: {news['title']}")
    try:
        post_text = generate_post(news)
        send_message(post_text)
        print("[DONE] Пост отправлен в ЛС")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()
