import requests
from telegram import Bot

# ====== Конфигурация (захардкожено) ======
OPENROUTER_API_KEY = "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"
OPENROUTER_MODEL = "deepseek/deepseek-chat-v3-0324"

TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

# ====== Шаблон роли ======
ROLE_PROMPT = """# Role: Редактор-Ассистент "Ясный Текст"
Ваша цель — помогать пользователю улучшать тексты на русском языке. 
Повышайте читабельность, ясность изложения, исправляйте ошибки, убирайте излишне формальные фразы.
Не меняйте смысл текста и не добавляйте лишнюю информацию.
"""

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

# ====== Генерация текста ======
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

# ====== Генерация изображения ======
def generate_image(description):
    # В OpenRouter сейчас нет универсального image API, поэтому пример сделан для Stable Diffusion через OpenRouter.
    url = "https://openrouter.ai/api/v1/images"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "stabilityai/stable-diffusion-xl",
        "prompt": description
    }
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["url"]

# ====== Публикация в Telegram ======
def post_to_telegram(text, image_url=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    if image_url:
        bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text, parse_mode="HTML")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")

# ====== Основная логика ======
if __name__ == "__main__":
    raw_news = """
Claude теперь умеет искать ваши старые диалоги...
Anthropic добавила функцию поиска по истории чатов для Claude.
Пока работает только для платных подписчиков, но будет доступно для всех.
"""

    print("[INFO] Генерирую текст...")
    final_text = generate_text(raw_news)

    print("[INFO] Генерирую изображение...")
    image_url = generate_image("иллюстрация новости про Claude и поиск по чатам, в стиле минимализма, нейросети")

    print("[INFO] Отправляю в Telegram...")
    post_to_telegram(final_text, image_url)

    print("[DONE] Публикация завершена!")
