import os
import requests
import xml.etree.ElementTree as ET
import re
import html
import json
import schedule
import time

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
CHAT_ID             = os.getenv("CHAT_ID")  # Основной ID (например, 6983437462)
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Список получателей (добавили второго)
CHAT_IDS = [CHAT_ID, "5999167622"] if CHAT_ID else ["5999167622"]

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
# Fallback пост (с зашитой ссылкой и юмористическим P.S.)
# ============================
def fallback_post(news):
    return (
        f"🔍 {news['title']}\n\n"
        "Что случилось?\n"
        f"{news['desc'][:200]}...\n\n"
        "Почему это важно?\n"
        "Это значимо для развития ИИ и технологий.\n\n"
        f"Подробности читайте <a href='{news['link']}'>здесь</a>.\n\n"
        "💡 P.S. А ИИ уже шутит лучше, чем мой кофе — бодро и без осадка! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>'
    )


# ============================
# Генерация поста через OpenRouter API
# ============================
def generate_post(news):
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY не задан — fallback")
        return fallback_post(news)
    
    prompt = (
        "Ты — редактор новостей по ИИ. Строго следуй этому формату для поста. Не меняй структуру, не добавляй лишний текст, не пропускай разделы. Без числовой нумерации. Зашивай ссылку в предложение раздела 'Подробности' как HTML-гиперссылку (например: 'Подробности читайте <a href=\"{link}\">здесь</a>'). Для P.S. придумай короткое юмористическое завершение (1 предложение), подходящее к теме новости (ИИ/технологии), с эмодзи 🚀.\n\n"
        f"Формат:\n"
        f"🔍 {news['title']}\n\n"
        "Что случилось?\n"
        "[Кратко: 1-2 предложения по сути новости, основываясь на описании]\n\n"
        "Почему это важно?\n"
        "[Кратко: 1-2 предложения о значимости для сферы ИИ и технологий]\n\n"
        "Подробности читайте <a href='{news['link']}'>здесь</a>.\n\n"
        "💡 P.S. [Юмористическое завершение, подходящее к теме, 1 предложение] 🚀\n\n"
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
            {"role": "system", "content": "Ты — профессиональный редактор новостей по ИИ с юмором. Строго следуй формату, зашивай ссылку в предложение, генерируй юмористический P.S."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
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
# Отправка сообщения в Telegram (несколько получателей)
# ============================
def send_message(text):
    if not TELEGRAM_TOKEN:
        print("[ERROR] TELEGRAM_TOKEN не задан")
        return
    for chat_id in CHAT_IDS:
        if not chat_id:
            continue
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": chat_id,
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
            print(f"[ERROR] Telegram API {r.status_code} для {chat_id}: {r.text}")
        else:
            print(f"[OK] Пост отправлен в {chat_id}")


# ============================
# Функция для запуска постинга
# ============================
def job():
    news = get_one_news()
    if not news:
        print("[INFO] Нет свежих новостей")
        return
    print(f"[INFO] Генерация поста для: {news['title']}")
    post = generate_post(news)
    send_message(post)
    print("[DONE] Пост отправлен в ЛС")


# ============================
# MAIN с расписанием (ежедневно по МСК)
# ============================
def main():
    # Установка расписания (время МСК, ежедневно)
    schedule.every().day.at("08:30").do(job)
    schedule.every().day.at("15:30").do(job)
    schedule.every().day.at("19:30").do(job)

    print("[INFO] Бот запущен. Ожидание расписания...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту


if __name__ == "__main__":
    main()
