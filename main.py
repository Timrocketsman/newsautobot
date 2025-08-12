import requests
from telegram import Bot
import xml.etree.ElementTree as ET
import re
from datetime import datetime
import random

# --------------------------
# Конфигурация
# --------------------------
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

# RSS источники новостей
RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://vc.ru/rss/all"
]

# --------------------------
# Простой RSS парсер без feedparser
# --------------------------
def parse_rss_simple(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Парсим XML
        root = ET.fromstring(response.content)
        
        articles = []
        items = root.findall('.//item')[:5]  # Берём первые 5 статей
        
        for item in items:
            title = item.find('title')
            description = item.find('description')
            link = item.find('link')
            
            article = {
                'title': title.text if title is not None else 'Без заголовка',
                'description': description.text if description is not None else 'Без описания',
                'link': link.text if link is not None else ''
            }
            articles.append(article)
            
        return articles
        
    except Exception as e:
        print(f"[ERROR] Ошибка парсинга {url}: {e}")
        return []

# --------------------------
# Получение всех новостей
# --------------------------
def get_all_news():
    all_articles = []
    
    for feed_url in RSS_FEEDS:
        print(f"[INFO] Парсинг: {feed_url}")
        articles = parse_rss_simple(feed_url)
        all_articles.extend(articles)
        
    return all_articles

# --------------------------
# Очистка HTML тегов из текста
# --------------------------
def clean_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)[:300] + "..." if len(text) > 300 else text

# --------------------------
# Форматирование новости
# --------------------------
def format_news(article):
    title = article['title'][:60] + "..." if len(article['title']) > 60 else article['title']
    description = clean_html(article['description'])
    
    formatted_post = f"""🔍 {title}

1️⃣ Что случилось?
{description[:200]}...

2️⃣ Как это работает?
📰 Свежая информация из мира технологий и ИИ

3️⃣ Чем важно?
✅ Актуальные технологические тренды
✅ Новости индустрии
✅ Полезная информация для IT-сообщества

4️⃣ Подробности:
🔗 [Читать полностью]({article['link']})

💡 P.S. Оставайтесь в курсе последних новостей! 🚀

#Новости #ИИ #Технологии

Бот⚫️Сайт

[Бот](https://t.me/BrainAid_bot) | [Сайт](https://brainaid.ru/)"""

    return formatted_post

# --------------------------
# Публикация в Telegram
# --------------------------
def post_to_telegram(text):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(
            chat_id=CHANNEL_ID, 
            text=text, 
            parse_mode="Markdown",
            disable_web_page_preview=False
        )
        print("[SUCCESS] Сообщение отправлено!")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка отправки: {e}")
        return False

# --------------------------
# Основная логика
# --------------------------
def main():
    print("[INFO] Запуск новостного бота...")
    
    # Получаем новости
    print("[INFO] Сбор новостей...")
    articles = get_all_news()
    
    if not articles:
        print("[WARNING] Новости не найдены!")
        return
        
    # Выбираем случайную новость
    selected_article = random.choice(articles)
    print(f"[INFO] Выбрана: {selected_article['title'][:40]}...")
    
    # Форматируем и отправляем
    formatted_post = format_news(selected_article)
    
    print("[INFO] Отправка в канал...")
    if post_to_telegram(formatted_post):
        print("[DONE] Новость опубликована!")
    else:
        print("[ERROR] Ошибка публикации!")

# --------------------------
# Запуск
# --------------------------
if __name__ == "__main__":
    main()
