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

# Расширенные ключевые слова для отбора более интересных новостей (добавлены темы прорывов, применений, забавных случаев)
KEYWORDS = [
    "ии", "искусственный интеллект", "нейросеть", "машинное обучение", "deep learning", "ai",
    "модель", "llm", "gpt", "генерация", "прорыв", "применение", "гаджет", "умный дом",
    "смартфон", "робот", "автопилот", "медицина", "искусство", "игровой", "бизнес", "стартап"
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
# Получить одну свежую новость (улучшенный отбор: ищем более "интересные" по ключевым словам с приоритетом на прорывы/применения)
# ============================
def get_one_news():
    seen = load_seen()
    candidates = []  # Собираем кандидатов для выбора самого интересного
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:10]:  # Больше элементов для лучшего отбора
                link = item.findtext("link", "").strip()
                if not link or link in seen:
                    continue
                title = item.findtext("title", "Без заголовка").strip()
                desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
                txt = (title + " " + desc).lower()
                # Оценка "интересности": считаем совпадения с ключевыми словами
                score = sum(1 for kw in KEYWORDS if kw in txt)
                if score > 1:  # Только если минимум 2 совпадения для интересности
                    candidates.append({"title": title, "desc": desc, "link": link, "score": score})
        except Exception as e:
            print(f"[ERROR] Парсинг {url}: {e}")
    
    if not candidates:
        return None
    
    # Выбираем самую "интересную" по score
    best = max(candidates, key=lambda x: x["score"])
    seen.add(best["link"])
    save_seen(seen)
    return best


# ============================
# Fallback пост (адаптированный под желаемый стиль)
# ============================
def fallback_post(news):
    return (
        f"🤖 {news['title']}\n\n"
        "1️⃣ В чем суть?\n"
        f"{news['desc'][:150]}...\n\n"
        "2️⃣ Почему это прорыв?\n"
        "Это меняет игру в ИИ!\n\n"
        "3️⃣ Где уже применяется?\n"
        "В гаджетах и бизнесе.\n\n"
        "4️⃣ Что это меняет?\n"
        "Больше удобства для всех.\n\n"
        f"🔗 Читать подробнее: <a href='{news['link']}'>здесь</a>\n\n"
        "💡 P.S. А нейросети уже умнее, чем мой вчерашний кофе! 😉\n\n"
        "🤖 Бот-ассистент @PerplexityPro\n"
        "🌐 Наш сайт [ссылка]"
    )


# ============================
# Генерация поста через OpenRouter API (обновленный промпт для стиля: креативный, наглядный, с акцентом на пользу, легкая шутка)
# ============================
def generate_post(news):
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY не задан — fallback")
        return fallback_post(news)
    
    prompt = (
        "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Создай увлекательный пост в стиле: креативный заголовок с эмодзи, нумерованные разделы (1️⃣ В чем суть? с кратким объяснением, 2️⃣ Почему это прорыв? с преимуществами и эмодзи, 3️⃣ Где уже применяется?, 4️⃣ Что это меняет? с акцентом на пользу для пользователей), ссылка в конце, P.S. с легкой шуткой. Тон живой, естественный, как болтаешь с друзьями, доступный для новичков и экспертов (47% женская аудитория). Фокус на ясности, аналогиях, без жаргона. Делай наглядно, с эмодзи для акцентов.\n\n"
        f"Формат:\n"
        f"🤖 [Креативный заголовок с эмодзи]\n\n"
        "1️⃣ В чем суть?\n"
        "[Краткое объяснение, 1-2 предложения с аналогией]\n\n"
        "2️⃣ Почему это прорыв?\n"
        "[Пункты с преимуществами, эмодзи, акцент на скорость/приватность/удобство]\n\n"
        "3️⃣ Где уже применяется?\n"
        "[Примеры из жизни/гаджетов/бизнеса]\n\n"
        "4️⃣ Что это меняет?\n"
        "[Польза для пользователей, с эмодзи]\n\n"
        "---\n"
        "💡 P.S. [Легкая шутка, связанная с темой, с 😉]\n\n"
        f"🔗 Читать подробнее: <a href='{news['link']}'>здесь</a>\n\n"
        "🤖 Бот-ассистент @PerplexityPro\n"
        "🌐 Наш сайт [ссылка]\n\n"
        f"---\n"
        f"Основывайся на: Заголовок: {news['title']}\n"
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
            {"role": "system", "content": "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Пиши живо, креативно, с юмором, как для друзей — объясняй просто, фокусируйся на пользе, заканчивай шуткой."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,  # Чуть выше для креативности и живости
        "max_tokens": 500
    }
    
    try:
        resp = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            print(f"[ERROR] OpenRouter API {resp.status_code}: {resp.text}")
            return fallback_post(news)
        data = resp.json()
        generated = data["choices"][0]["message"]["content"].strip()
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
# MAIN (режим теста: без тайминга, однократный запуск)
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
