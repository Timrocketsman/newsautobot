import os
import requests
from telegram import Bot
from datetime import datetime

# ====== Конфигурация ======
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw")
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1002047105840")

# ====== Шаблон промпта для генерации текста ======
ROLE_PROMPT = """
# Role: Редактор-Ассистент "Ясный Текст"
Ваша цель — помогать пользователю улучшать тексты на русском языке...
"""  # Можно вставить полный текст роли из ТЗ

# ====== Шаблон поста ======
POST_TEMPLATE = """🔍 {title}

1️⃣ Что случилось?
{what}

2️⃣ Как это работает?
{how}

3️⃣ Чем лучше аналогов?
{better}

4️⃣ Как включить?
{how_to}

5️⃣ Когда ждать всем?
{when}

💡 P.S. {ps}

#ИИ #Новости
"""

# ====== Функция генерации текста ======
def generate_text(news_text):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": ROLE_PROMPT},
            {"role": "user", "content": f"Сформируй новость по шаблону:\n{POST_TEMPLATE}\nВот данные:\n{news_text}"}
        ]
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]

# ====== Функция генерации изображения ======
def generate_image(description):
    url = "https://openrouter.ai/api/v1/images"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": OPENROUTER_MODEL,  # Если DeepSeek умеет в image, иначе заменить на image-модель
        "prompt": description
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["url"]  # Возвращает ссылку на сгенерированное изображение

# ====== Публикация в Telegram ======
def post_to_telegram(text, image_url=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    if image_url:
        bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text, parse_mode="HTML")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")

# ====== Основная логика ======
if __name__ == "__main__":
    # Пример входных данных (можно заменить на парсер новостей)
    raw_news = """
    Claude теперь умеет искать ваши старые диалоги...
    """

    print("[INFO] Генерирую текст...")
    final_text = generate_text(raw_news)

    print("[INFO] Генерирую изображение...")
    image_url = generate_image("иллюстрация к новости про нейросети и поиск по чату")

    print("[INFO] Отправляю в Telegram...")
    post_to_telegram(final_text, image_url)

    print("[DONE] Публикация завершена!")
