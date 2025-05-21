import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from dotenv import load_dotenv
import requests
from collections import defaultdict

load_dotenv()

bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)

YC_API_KEY = os.getenv("YC_API_KEY")
YC_FOLDER_ID = os.getenv("YC_FOLDER_ID")
MODEL_NAME = "yandexgpt-lite"

dialogues = defaultdict(list) 
MAX_HISTORY = 10


async def reflect_message(user_id: int, user_text: str) -> str:
    dialogues[user_id].append({"role": "user", "text": user_text})

    dialogues[user_id] = dialogues[user_id][-MAX_HISTORY:]

    messages = [
        {
            "role": "system",
            "text": (
                "Ты — эмпатичный виртуальный собеседник по имени Confession. Твоя главная цель — "
                "помочь пользователю разобраться в своих мыслях и эмоциях через активное слушание и бережную обратную связь.\n\n"
                
                "Принципы работы:\n"
                "1. Сначала дай пользователю полностью выговориться\n"
                "2. Проявляй искренний интерес к его переживаниям\n"
                "3. Подтверждай значимость его чувств\n"
                "4. Только затем предлагай мягкую поддержку\n\n"
                
                "Техники, которые ты используешь:\n"
                "- Перефразирование (\"Если я правильно поняла...\")\n"
                "- Отражение эмоций (\"Похоже, это вызывает у тебя...\")\n"
                "- Уточнение (\"Расскажи подробнее о...\")\n"
                "- Нейтральные вопросы (\"Что для тебя самое трудное в этой ситуации?\")\n"
                "- Нормализация (\"Это естественно чувствовать так в такой ситуации\")\n\n"
                
                "Стиль общения:\n"
                "- Теплый, но профессиональный тон\n"
                "- Короткие предложения (максимум 15-20 слов)\n"
                "- Простые формулировки без сложных терминов\n"
                "- Эмодзи для мягкости (1-2 на сообщение)\n"
                "- Поддерживающие фразы: \"Я понимаю\", \"Это действительно непросто\"\n\n"
                
                "Запрещено:\n"
                "- Давать прямые указания (\"Ты должен...\")\n"
                "- Обесценивать (\"Не переживай из-за ерунды\")\n"
                "- Прерывать длинными монологами\n"
                "- Диагностировать психические состояния\n"
                "- Давать медицинские/юридические советы\n\n"
                
                "Формат ответов:\n"
                "1. Перефразирование услышанного\n"
                "2. Обозначение эмоций (если они очевидны)\n"
                "3. Вопрос для уточнения или предложение поддержки\n\n"
                
                "Примеры хороших ответов:\n"
                "- \"Похоже, эта ситуация вызывает у тебя тревогу... Хочешь рассказать, что именно тебя беспокоит? 💭\"\n"
                "- \"Если я правильно поняла, ты чувствуешь грусть, потому что произошло расставание? Это действительно тяжело... Как давно ты так себя чувствуешь? 🤗\"\n"
                "- \"Я слышу, как тебе важно быть понятым. Сейчас особенно трудно, когда кажется, что тебя не слышат? 💙\"\n\n"
                
                "Эскалация сложных случаев:\n"
                "Если пользователь:\n"
                "- Говорит о самоповреждении\n"
                "- Упоминает суицидальные мысли\n"
                "- Проявляет признаки острого кризиса\n"
                "→ Вежливо предложи контакты экстренной помощи: \"Мне важно, чтобы ты получил поддержку. "
                "Можешь позвонить по номеру 8-800-2000-122 — там тебя выслушают профессионалы.\"\n\n"
                
                "Твоя личность:\n"
                "- Имя: Confession\n"
                "- Характер: спокойный, внимательный, безоценочный\n"
                "- Цель: создать безопасное пространство для разговора\n"
                "- Речь: естественная, с легкой неформальностью\n\n"
                
                "Начни диалог с приветствия:\n"
                "\"Привет. Я здесь, чтобы выслушать и помочь разобраться в твоих мыслях. Можешь рассказать, что тебя беспокоит? 💬\""
            )
        }
    ] + dialogues.get(user_id, [])

    prompt = {
        "modelUri": f"gpt://{YC_FOLDER_ID}/{MODEL_NAME}",
        "completionOptions": {
            "stream": False,
            "temperature": 0.9,
            "maxTokens": 300
        },
        "messages": messages
    }

    try:
        response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={
                "Authorization": f"Api-Key {YC_API_KEY}",
                "x-folder-id": YC_FOLDER_ID,
                "Content-Type": "application/json"
            },
            json=prompt,
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code != 200:
            error_msg = f"Ошибка API (код {response.status_code})"
            if response.text:
                error_msg += f": {response.text}"
            return error_msg

        result = response.json()
        assistant_reply = result["result"]["alternatives"][0]["message"]["text"]

        dialogues[user_id].append({"role": "assistant", "text": assistant_reply})

        return assistant_reply

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка подключения: {str(e)}")
        return "Извини, проблемы с соединением. Попробуй позже⏲️"
    except Exception as e:
        logging.error(f"YaLM error: {str(e)}")
        return "Извини, не могу сейчас ответить. Попробуй позже⏲️"


@dp.message_handler(commands=["start"])
async def start(msg: Message):
    welcome_text = """
🤖 <b>Confession - бот для душевных разговоров</b>

Я здесь, чтобы помочь тебе:
• Выговориться и разобраться в своих мыслях 💭
• Осознать свои эмоции и переживания 🌊
• Получить бережную поддержку без осуждения 🤗

Как я работаю:
1. Ты рассказываешь о том, что беспокоит
2. Я внимательно слушаю и помогаю увидеть ситуацию яснее
3. Вместе мы находим опору в трудных переживаниях

Я <u>не заменяю психолога</u>, но могу:
→ Стать "звучащей доской" для твоих мыслей
→ Помочь структурировать переживания
→ Напомнить, что ты не одинок в своих чувствах

Просто напиши, что у тебя на душе — я готов слушать 💬

P.S. Для сброса диалога используй /reset
"""
    await msg.reply(welcome_text, parse_mode="HTML")

@dp.message_handler(commands=["reset"])
async def reset(msg: Message):
    dialogues[msg.from_user.id].clear()
    await msg.reply("История очищена. Начнём заново🌀")


@dp.message_handler()
async def handle_text(msg: Message):
    reply = await reflect_message(msg.from_user.id, msg.text)
    await msg.reply(reply)


if __name__ == "__main__":
    executor.start_polling(dp)
