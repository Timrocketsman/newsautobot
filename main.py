import os
import requests
import xml.etree.ElementTree as ET
import re
import html
import json

# Подключаем dotenv для локального .env (если нужно)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # Если не установлен, игнорируем (для Railway)

# ============================
# КОНФИГУРАЦИЯ через переменные окружения
# ============================
TELEGRAM_TOKEN      = os.getenv("TELEGRAM_TOKEN")
CHAT_ID             = os.getenv("CHAT_ID")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://3dnews.ru/news/rss",
    "https://habr.com/ru/rss/hub/artificial_intelligence/"
]

KEYWORDS = [
    "ии", "искусственный интеллект", "нейросеть",
    "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация"
]

SEEN_FILE = "seen_links.json"


# ============================
# Работа с seen_links.json
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
# Получить одну свежую новость
# ============================
def get_one_news():
    seen = load_seen()
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:5]:
                link = item.findtext("link", "").strip()
                if not link or link in seen:
                    continue
                title = item.findtext("title", "Без заголовка").strip()
                desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
                txt = (title + " " + desc).lower()
                if any(kw in txt for kw in KEYWORDS):
                    seen.add(link)
                    save_seen(seen)
                    return {"title": title, "desc": desc, "link": link}
        except Exception as e:
            print(f"[ERROR] Парсинг {url}: {e}")
    return None


# ============================
# Fallback пост (без нумерации)
# ============================
def fallback_post(news):
    return (
        f"🔍 {news['title']}\n\n"
        "Что случилось?\n"
        f"{news['desc'][:200]}...\n\n"  # Кратко из описания
        "Почему это важно?\n"
        "Это значимо для развития ИИ и технологий.\n\n"
        f"Подробности:\n🔗 {news['link']}\n\n"
        "💡 P.S. Следите за обновлениями! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>'
    )


# ============================
# Генерация поста через OpenRouter API (без нумерации)
# ============================
def generate_post(news):
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY не задан — fallback")
        return fallback_post(news)
    
    prompt = (
        "Ты — редактор новостей по ИИ. Строго следуй этому формату для поста. Не меняй структуру, не добавляй лишний текст, не пропускай разделы. Без числовой нумерации разделов. Используй только предоставленные данные.\n\n"
        f"Формат:\n"
        f"🔍 {news['title']}\n\n"
        "Что случилось?\n"
        "[Кратко: 1-2 предложения по сути новости, основываясь на описании]\n\n"
        "Почему это важно?\n"
        "[Кратко: 1-2 предложения о значимости для сферы ИИ и технологий]\n\n"
        "Подробности:\n"
        f"🔗 {news['link']}\n\n"
        "💡 P.S. Следите за обновлениями! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>\n\n'
        f"---\n"
        f"Заголовок: {news['title']}\n"
        f"Описание: {news['desc']}\n"
        f"Ссылка: {news['link']}"
    )
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ. Строго следуй указанному формату без нумерации, не добавляй лишнего."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 400
    }
    
    try:
        resp = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            print(f"[ERROR] OpenRouter API {resp.status_code}: {resp.text}")
            return fallback_post(news)
        data = resp.json()
        generated = data["choices"][0]["message"]["content"].strip()
        # Пост-обработка: добавляем нижнюю строчку, если отсутствует
        if '<a href="https://t.me/BrainAid_bot">' not in generated:
            generated += '\n\n<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>'
        return generated
    except Exception as e:
        print(f"[ERROR] OpenRouter API: {e}")
        return fallback_post(news)


# ============================
# Отправка сообщения в Telegram
# ============================
def send_message(text):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[ERROR] TELEGRAM_TOKEN или CHAT_ID не заданы")
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
    post = generate_post(news)
    send_message(post)
    print("[DONE] Пост отправлен в ЛС")


if __name__ == "__main__":
    main()
