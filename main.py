import requests
from telegram import Bot

# --------------------------
# Конфигурация
# --------------------------
HF_TOKEN = "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"  # твой токен Hugging Face
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

# API для картинок
IMAGE_API_URL = "https://image.pollinations.ai/prompt/"

# --------------------------
# Шаблон поста
# --------------------------
ROLE_PROMPT = """Ты — редактор новостей. Оформи полученную информацию по шаблону и сделай читаемый пост на русском:
🔍 {title}

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
"""

# --------------------------
# Генерация текста
# --------------------------
def generate_text(news_text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": f"{ROLE_PROMPT}\n\nДанные для новости:\n{news_text}",
        "parameters": {"max_new_tokens": 500, "temperature": 0.7}
    }
    r = requests.post(HF_API_URL, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    # HuggingFace может вернуть список или dict
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]
    return str(data)

# --------------------------
# Генерация картинки
# --------------------------
def generate_image(prompt):
    return IMAGE_API_URL + requests.utils.quote(prompt)

# --------------------------
# Публикация в Telegram
# --------------------------
def post_to_telegram(text, image_url=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    if image_url:
        bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text[:1024], parse_mode="HTML")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")

# --------------------------
# Основная логика
# --------------------------
if __name__ == "__main__":
    raw_news = """
Claude теперь умеет искать ваши старые диалоги.
Anthropic добавила функцию поиска по истории чатов для Claude.
Пока только для платных пользователей, но обещают скоро для всех.
"""

    print("[INFO] Генерирую текст...")
    final_text = generate_text(raw_news)

    print("[INFO] Генерирую изображение...")
    image_url = generate_image("новость про нейросети, чат-боты, AI, минимализм, современный UI")

    print("[INFO] Отправляю в Telegram...")
    post_to_telegram(final_text, image_url)

    print("[DONE] Публикация завершена!")
