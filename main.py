import requests
import xml.etree.ElementTree as ET
import re
import random

# ============================
# Конфигурация
# ============================
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHAT_ID = "6983437462"        # для тестирования — ваше личное сообщение
CHANNEL_ID = "-1002047105840" # вернем после настройки

# Русскоязычные RSS-ленты
RSS_FEEDS = [
    "https://habr.com/ru/rss/all/all/",
    "https://vc.ru/rss/all",
    "https://ria.ru/export/rss2/archive/index.xml",
    "https://lenta.ru/rss"
]

# ============================
# JSON-шаблон поста
# ============================
ROLE_JSON = {
    "role": "Редактор-Ассистент \"Ясный Текст\"",
    "task": (
        "Ваша цель — помогать пользователю улучшать тексты на русском языке. "
        "Сосредоточьтесь на ясности, грамотности и лаконичности без потери смысла."
    ),
    "constraints": [
        "НЕ изменять смысл",
        "НЕ добавлять новую информацию",
        "НЕ делать оценки",
        "НЕ использовать канцелярит"
    ],
    "workflow": [
        "Шаг 1: Запрос контекста",
        "Шаг 2: Предложение стиля",
        "Шаг 3: Анализ и предложения"
    ]
}

# ============================
# Парсер RSS без сторонних библиотек
# ============================
def parse_rss(url):
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")[:5]
        lst = []
        for i in items:
            title = i.findtext("title", default="Без заголовка")
            desc  = re.sub(r"<[^>]+>", "", i.findtext("description", default="Без описания"))
            link  = i.findtext("link", default="")
            lst.append({"title": title, "description": desc, "link": link})
        return lst
    except:
        return []

# ============================
# Сбор новостей
# ============================
def collect_news():
    art = []
    for feed in RSS_FEEDS:
        print(f"[INFO] Чтение {feed}")
        art += parse_rss(feed)
    return art

# ============================
# Форматирование поста
# ============================
def format_post(a):
    title = a["title"][:80].rstrip("…") + ("…" if len(a["title"])>80 else "")
    desc  = a["description"][:300].rstrip("…") + ("…" if len(a["description"])>300 else "")
    return (
        f"🔍 {title}\n\n"
        f"1️⃣ Что случилось?\n{desc}\n\n"
        f"2️⃣ Как это работает?\n"
        f"Сбор данных из RSS-лент и автоматическая публикация.\n\n"
        f"3️⃣ Чем лучше аналогов?\n"
        f"✅ Автоматическая работа 24/7\n"
        f"\n✅ Только русскоязычные источники\n\n"
        f"4️⃣ Подробности:\n🔗 {a['link']}\n\n"
        f"5️⃣ Источник:\n📌 RSS-лента\n\n"
        f"💡 P.S. Следите за обновлениями!\n\n"
        f"Бот⚫️PerplexityPro⚫️Сайт\n"
        f"Ваш запрос: [введите задачу]"
    )

# ============================
# Отправка сообщения
# ============================
def send(text, to_channel=False):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID if to_channel else CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    r = requests.post(url, data=payload, timeout=10)
    if r.status_code!=200:
        print(f"[ERROR] Telegram {r.status_code}: {r.text}")
    else:
        print("[SUCCESS] Отправлено")

# ============================
# Main
# ============================
def main():
    news = collect_news()
    if not news:
        print("[WARNING] Нет новостей")
        return
    a = random.choice(news)
    post = format_post(a)
    send(post, to_channel=False)  # пока в ЛС
    # после теста: send(post, to_channel=True)

if __name__=="__main__":
    main()
