import requests
from telegram import Bot

# --------------------------
# Конфигурация
# --------------------------
HF_TOKEN = "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"
HF_MODEL = "microsoft/DialoGPT-medium"  # ОТКРЫТАЯ модель
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

IMAGE_API_URL = "https://image.pollinations.ai/prompt/"

# --------------------------
# Генерация текста
# --------------------------
def generate_text(news_text):
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    prompt = f"Напиши краткую новость по шаблону:\n🔍 Заголовок\n\n1️⃣ Что случилось?\n2️⃣ Как это работает?\n3️⃣ Чем лучше аналогов?\n\nДанные: {news_text}"
    
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 300, "temperature": 0.7}
    }
    
    r = requests.post(HF_API_URL, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()
    
    if isinstance(data, list) and len(data) > 0:
        return data[0].get("generated_text", str(data))
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
        bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text[:1024])
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=text)

# --------------------------
# Основная логика
# --------------------------
if __name__ == "__main__":
    raw_news = """
Claude теперь умеет искать ваши старые диалоги.
Anthropic добавила функцию поиска по истории чатов.
Пока только для платных пользователей.
"""

    print("[INFO] Генерирую текст...")
    final_text = generate_text(raw_news)

    print("[INFO] Генерирую изображение...")
    image_url = generate_image("новость про нейросети, чат-боты, AI, минимализм")

    print("[INFO] Отправляю в Telegram...")
    post_to_telegram(final_text, image_url)

    print("[DONE] Готово!")
