import requests
from telegram import Bot

# ====== Конфигурация ======
TELEGRAM_TOKEN = "8141858682:AAG_k13Rd2WClI1SDL9W7-zC0vFuRUUkfUw"
CHANNEL_ID = "-1002047105840"

# Бесплатный HuggingFace endpoint (Mistral 7B)
HF_TEXT_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
HF_TOKEN = ""  # Пусто — модель бесплатная, но можно вставить свой ключ HuggingFace для ускорения

# Публичное API для генерации изображений
IMAGE_API_URL = "https://image.pollinations.ai/prompt/"

# ====== Промпт роли ======
ROLE_PROMPT = """Ты — редактор новостей. Оформи полученную информацию по шаблону и сделай краткий, информативный и читаемый пост.
Шаблон:
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

# ====== Генерация текста ======
def generate_text(news_text):
    headers = {"Content-Type": "application/json"}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    payload = {
        "inputs": f"{ROLE_PROMPT}\n\nВот данные для новости:\n{news_text}",
        "parameters": {"max_new_tokens": 500, "temperature": 0.7}
    }

    r = requests.post(HF_TEXT_URL, headers=headers, json=payload)
    r.raise_for_status()
    data = r.json()

    if isinstance(data, list):
        return data[0]["generated_text"]
    return data

# ====== Генерация изображения ======
def generate_image(prompt):
    # Используем Pollinations — публичный API, картинка по URL
    return IMAGE_API_URL + requests.utils.quote(prompt)

# ====== Публикация в Telegram ======
def post_to_telegram(text, image_url=None):
    bot = Bot(token=TELEGRAM_TOKEN)
    if image_url:
        bot.send_photo(chat_id=CHANNEL_ID, photo=image_url, caption=text[:1024], parse_mode="HTML")
    else:
        bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")

# ====== Основной код ======
if __name__ == "__main__":
    raw_news = """
Claude теперь умеет искать ваши старые диалоги.
Пока только для платных пользователей, но будет доступно всем.
"""

    print("[INFO] Генерирую текст...")
    final_text = generate_text(raw_news)

    print("[INFO] Генерирую изображение...")
    image_url = generate_image("новость про нейросети, чат-боты, интерфейс поиска, минимализм")

    print("[INFO] Отправляю в Telegram...")
    post_to_telegram(final_text, image_url)

    print("[DONE] Публикация завершена!")
