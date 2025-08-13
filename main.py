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

# Обновленный список RSS-фидов на основе указанных источников
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",  # Habr
    "https://vc.ru/rss/all",  # VC.ru
    "https://ria.ru/export/rss2/archive/index.xml",  # Ria (Hi-Tech Mail.ru related)
    "https://lenta.ru/rss",  # Lenta (general news, AI coverage)
    "https://3dnews.ru/news/rss",  # 3dnews
    "https://habr.com/ru/rss/hub/artificial_intelligence/",  # Habr AI hub
    "https://neuro-ai.ru/rss",  # Neuro-AI (assuming standard RSS)
    "https://hi-tech.mail.ru/rss/all/",  # Hi-Tech Mail.ru
    "https://forbes.ru/rss",  # Forbes.ru (general, AI articles)
    "https://neurohive.io/en/rss/",  # Neurohive
    "https://www.aimagazine.com/rss",  # AI Magazine
    "https://spectrum.ieee.org/topic/neural-networks/rss",  # IEEE Spectrum Neural Networks
    "https://www.technology.org/category/artificial-intelligence/feed/",  # Technology.org AI & Neural Networks
    "https://artificialintelligence-news.com/feed/"  # ArtificialIntelligence-News
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
# Fallback пост (адаптированный под новую роль)
# ============================
def fallback_post(news):
    return (
        f"🔍 {news['title']}\n\n"
        f"{news['desc'][:200]}...\n\n"
        f"Подробности читайте <a href='{news['link']}'>здесь</a>.\n\n"
        "💡 А нейросети уже знают, что будет завтра — главное, чтобы кофе не закончился! 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>'
    )


# ============================
# Генерация поста через OpenRouter API (обновленная роль)
# ============================
def generate_post(news):
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY не задан — fallback")
        return fallback_post(news)
    
    prompt = (
        "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Создай пост на основе новости: яркий заголовок с эмодзи, основной текст (введение в тему, объяснение ключевых аспектов простым языком с аналогиями, учитывая аудиторию от новичков до экспертов, 47% женская, 53% мужская), заверши уместной шуткой или острой фразой с эмодзи. Тон нейтрально-позитивный, естественный, без жаргона. Зашивай ссылку в предложение как HTML-гиперссылку (например: 'Подробности читайте <a href=\"{link}\">здесь</a>').\n\n"
        f"Формат:\n"
        f"🔍 [Яркий заголовок с эмодзи]\n\n"
        "[Основной текст: введение, объяснение, с эмодзи для акцентов]\n\n"
        "Подробности читайте <a href='{news['link']}'>здесь</a>.\n\n"
        "💡 [Шутка или острая фраза, связанная с темой, с эмодзи] 🚀\n\n"
        '<a href="https://t.me/BrainAid_bot">Бот</a>⚫️<a href="https://t.me/m/h5Kv1jd9MWMy">PerplexityPro</a>⚫️<a href="https://brainaid.ru/">Сайт</a>\n\n'
        f"---\n"
        f"Заголовок новости: {news['title']}\n"
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
            {"role": "system", "content": "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Пиши естественно, как для друзей, объясняй просто, заканчивай шуткой."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "max_tokens": 500  # Увеличено для более полного текста
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
# Функция для запуска постинга (три поста в час)
# ============================
def job():
    for _ in range(3):  # Три поста за один запуск
        news = get_one_news()
        if not news:
            print("[INFO] Нет свежих новостей для поста")
            continue
        print(f"[INFO] Генерация поста для: {news['title']}")
        post = generate_post(news)
        send_message(post)
        print("[DONE] Пост отправлен в ЛС")
        time.sleep(1)  # Небольшая пауза между постами


# ============================
# MAIN с расписанием (каждый час, три поста)
# ============================
def main():
    # Установка расписания: каждый час, запуск job (три поста)
    schedule.every(1).hours.do(job)

    print("[INFO] Бот запущен. Постинг трех новостей каждый час, круглосуточно, 365 дней в году.")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверка каждую минуту


if __name__ == "__main__":
    main()
