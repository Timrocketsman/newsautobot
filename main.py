import os
import requests
import xml.etree.ElementTree as ET
import re
import json
from bs4 import BeautifulSoup  # Для HTML-парсинга не-RSS сайтов
from html import escape  # Для экранирования HTML

# Подключаем dotenv для локального .env (если нужно)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TELEGRAM_TOKEN      = os.getenv("TELEGRAM_TOKEN")
CHAT_ID             = os.getenv("CHAT_ID")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Получатели сообщений
CHAT_IDS = [CHAT_ID, "5999167622"] if CHAT_ID else ["5999167622"]

# Новый список источников
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss",
    "https://3dnews.ru/news/rss",
    "https://neuro-ai.ru/news",  # HTML
    "https://hi-tech.mail.ru/tag/neyroseti/",  # HTML
    "https://vc.ru/tag/%D0%BD%D0%B5%D0%B9%D1%80%D0%BE%D1%81%D0%B5%D1%82%D0%B8",  # HTML
    "https://www.forbes.ru/tegi/neyroseti",  # HTML
    "https://neurohive.io/ru/novosti/",  # HTML
    "https://habr.com/ru/hubs/artificial_intelligence/",  # HTML
    "https://aimagazine.com/feed",  # RSS (если 403, пропустим)
    "https://spectrum.ieee.org/rss.xml?topic=neural-networks",  # Исправленный RSS для IEEE (альтернатива)
    "https://www.technology.org/feed/",  # Общий RSS Technology.org (альтернатива, так как оригинал 403)
    "https://www.artificialintelligence-news.com/feed/"  # RSS
]

KEYWORDS = [
    "ии", "искусственный интеллект", "нейросеть", "машинное обучение",
    "deep learning", "ai", "модель", "llm", "gpt", "генерация",
    "прорыв", "применение", "гаджет", "умный дом", "смартфон",
    "робот", "автопилот", "медицина", "искусство", "стартап"
]

SEEN_FILE = "seen_links.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)

# Функция очистки текста для Telegram HTML (закрывает теги, экранирует)
def clean_html_text(text):
    # Простая проверка на незакрытые теги (можно расширить)
    text = escape(text)  # Экранируем специальные символы
    # Добавляем закрытие для <a> если не закрыто
    if '<a href=' in text and '</a>' not in text:
        text += '</a>'
    return text

def get_one_news():
    seen = load_seen()
    candidates = []
    for url in RSS_FEEDS:
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            r.raise_for_status()
            # Проверяем тип контента
            if 'xml' in r.headers.get('Content-Type', ''):
                # RSS-парсинг
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:10]:
                    link = item.findtext("link", "").strip()
                    if not link or link in seen:
                        continue
                    title = item.findtext("title", "Без заголовка").strip()
                    desc = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()
                    txt = (title + " " + desc).lower()
                    score = sum(1 for kw in KEYWORDS if kw in txt)
                    if score > 1:
                        candidates.append({"title": title, "desc": desc, "link": link, "score": score})
            else:
                # HTML-парсинг с BeautifulSoup
                soup = BeautifulSoup(r.content, 'lxml')
                articles = soup.find_all(['article', 'div'], class_=[re.compile('post|article|news|item')])[:10]
                for article in articles:
                    title_tag = article.find(['h2', 'h3', 'a'])
                    desc_tag = article.find('p')
                    link_tag = article.find('a', href=True)
                    if not title_tag or not link_tag:
                        continue
                    link = link_tag['href'].strip()
                    if not link.startswith('http'):
                        link = url + link  # Абсолютная ссылка
                    if link in seen:
                        continue
                    title = title_tag.get_text().strip()
                    desc = desc_tag.get_text().strip() if desc_tag else ""
                    txt = (title + " " + desc).lower()
                    score = sum(1 for kw in KEYWORDS if kw in txt)
                    if score > 1:
                        candidates.append({"title": title, "desc": desc, "link": link, "score": score})
        except requests.exceptions.HTTPError as he:
            print(f"[ERROR] HTTP ошибка для {url}: {he} (код {r.status_code}) — пропускаем")
            continue
        except Exception as e:
            print(f"[ERROR] Парсинг {url}: {e} — пропускаем")
            continue

    if not candidates:
        return None
    best = max(candidates, key=lambda x: x["score"])
    seen.add(best["link"])
    save_seen(seen)
    return best

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
        "💡 P.S. Нейросети уже учат нас шутить — а я учусь у них! 😉\n\n"
        "🤖 Бот-ассистент @PerplexityPro\n"
        "🌐 Наш сайт [ссылка]"
    )

def generate_post(news):
    if not OPENROUTER_API_KEY:
        print("[WARN] OPENROUTER_API_KEY не задан — fallback")
        return fallback_post(news)

    prompt = (
        "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Создай пост строго в формате:\n\n"
        "🤖 [Яркий креативный заголовок с эмодзи]\n\n"
        "1️⃣ В чем суть?\n"
        "[Кратко, простыми словами, с аналогиями, 1-2 предложения]\n\n"
        "2️⃣ Почему это прорыв?\n"
        "[Пункты с преимуществами, эмодзи, акцент на пользу]\n\n"
        "3️⃣ Где уже применяется?\n"
        "[Примеры из жизни, гаджетов, бизнеса]\n\n"
        "4️⃣ Что это меняет?\n"
        "[Польза для пользователя, с эмодзи]\n\n"
        "---\n"
        "💡 P.S. [Уместная шутка или острая фраза с эмодзи, дружелюбно]\n\n"
        f"🔗 Читать подробнее: <a href='{news['link']}'>здесь</a>\n\n"
        "🤖 Бот-ассистент @PerplexityPro\n"
        "🌐 Наш сайт [ссылка]\n\n"
        "---\n"
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
            {"role": "system", "content": "Ты — автор Telegram-канала 'Нейросети: Просто о Сложном'. Пиши живо, понятно, с юмором, как рассказываешь друзьям. Не используй жаргон, делай информацию доступной для новичков и экспертов. Добавляй эмодзи для наглядности."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    try:
        resp = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            print(f"[ERROR] OpenRouter API {resp.status_code}: {resp.text}")
            return fallback_post(news)
        data = resp.json()
        generated = data["choices"][0]["message"]["content"].strip()
        # Очистка перед отправкой
        generated = clean_html_text(generated)
        return generated
    except Exception as e:
        print(f"[ERROR] OpenRouter API: {e}")
        return fallback_post(news)

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
