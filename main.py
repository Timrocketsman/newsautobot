import requests
from telegram import Bot
import feedparser
from datetime import datetime, timedelta
import time
import random

# --------------------------
# Конфигурация
# --------------------------
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

# RSS источники новостей
RSS_FEEDS = [
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.bbci.co.uk/news/rss.xml", 
    "https://www.reuters.com/rssFeed/technologyNews",
    "https://techcrunch.com/feed/",
    "https://habr.com/ru/rss/hub/artificial_intelligence/",
    "https://vc.ru/rss/all",
    "https://www.theverge.com/rss/index.xml"
]

# --------------------------
# Парсинг новостей из RSS
# --------------------------
def parse_news():
    all_articles = []
    
    for feed_url in RSS_FEEDS:
        try:
            print(f"[INFO] Парсинг RSS: {feed_url}")
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:3]:  # Берём только 3 свежие статьи из каждого фида
                article = {
                    'title': entry.get('title', 'Без заголовка'),
                    'summary': entry.get('summary', entry.get('description', 'Без описания')),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed.feed.get('title', 'Неизвестный источник')
                }
                all_articles.append(article)
                
        except Exception as e:
            print(f"[ERROR] Ошибка парсинга {feed_url}: {e}")
            continue
    
    return all_articles

# --------------------------
# Форматирование новости по шаблону
# --------------------------
def format_news(article):
    title = article['title'][:80] + "..." if len(article['title']) > 80 else article['title']
    
    formatted_post = f"""🔍 {title}

1️⃣ Что случилось?
{article['summary'][:200]}...

2️⃣ Как это работает?
📰 Новая информация из сферы технологий и ИИ

3️⃣ Чем важно?
✅ Актуальные тенденции рынка
✅ Новые технологические решения  
✅ Влияние на индустрию

4️⃣ Подробности:
🔗 [Читать полностью]({article['link']})

5️⃣ Источник:
📌 {article['source']}

💡 P.S. Следите за трендами вместе с нами! 🚀

#Новости #ИИ #Технологии
"""
    return formatted_post

# --------------------------
# Публикация в Telegram
# --------------------------
def post_to_telegram(text):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown", disable_web_page_preview=False)
        print("[SUCCESS] Сообщение отправлено в канал")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка отправки в Telegram: {e}")
        return False

# --------------------------
# Основная логика
# --------------------------
def main():
    print("[INFO] Запуск новостного бота...")
    
    # Парсинг новостей
    print("[INFO] Получение новостей из RSS...")
    articles = parse_news()
    
    if not articles:
        print("[WARNING] Новости не найдены!")
        return
    
    # Выбираем случайную свежую новость
    selected_article = random.choice(articles[:10])  # Из первых 10 самых свежих
    
    print(f"[INFO] Выбрана новость: {selected_article['title'][:50]}...")
    
    # Форматируем пост
    formatted_post = format_news(selected_article)
    
    # Отправляем в канал
    print("[INFO] Отправка в Telegram...")
    success = post_to_telegram(formatted_post)
    
    if success:
        print("[DONE] Новость успешно опубликована!")
    else:
        print("[ERROR] Не удалось опубликовать новость")

# --------------------------
# Запуск
# --------------------------
if __name__ == "__main__":
    main()
