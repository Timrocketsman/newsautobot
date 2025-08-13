import os
import requests

# Подхват переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID        = os.getenv("CHAT_ID")
AI_API_KEY     = os.getenv("AI_API_KEY")
AI_URL         = os.getenv("AI_URL", "https://api.deepseek.com/v1/chat/completions")

def test_telegram():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("[Telegram] Не заданы TELEGRAM_TOKEN или CHAT_ID")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        print("[Telegram] Авторизация успешна:", r.json()["result"]["username"])
    else:
        print(f"[Telegram] Ошибка авторизации {r.status_code}:", r.text)

def test_deepseek():
    if not AI_API_KEY:
        print("[DeepSeek] Не задан AI_API_KEY")
        return
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role":"user","content":"Hello"}],
        "max_tokens":10
    }
    r = requests.post(AI_URL, headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        print("[DeepSeek] Авторизация успешна, ответ модели получен")
    else:
        print(f"[DeepSeek] Ошибка авторизации {r.status_code}:", r.text)

if __name__ == "__main__":
    test_telegram()
    test_deepseek()
