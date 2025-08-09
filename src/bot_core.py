from __future__ import annotations
import os, asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from .scrape import load_or_ingest
from .module_nlp import QAEngine
from .recom import recommend_courses

import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
load_dotenv()  # подхватит .env из корня проекта
TOKEN = os.getenv("TELEGRAM_TOKEN")

HELP = (
    "Привет! Я помогу сравнить две магистерские программы ITMO и ответить на вопросы по их содержимому.\n\n"
    "Команды:\n"
    "/start — начало\n"
    "/ask <вопрос> — задать вопрос по программам\n"
    "/recommend — рекомендации элективов\n"
    "/compare — краткое сравнение\n"
)

kb_programs = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="AI"), KeyboardButton(text="AI Product")]],
    resize_keyboard=True,
)

async def main():
    if not TOKEN:
        raise RuntimeError("Не найден TELEGRAM_TOKEN в окружении")
    bot = Bot(TOKEN)
    dp = Dispatcher()

    programs = load_or_ingest()
    qa = QAEngine.from_programs(programs)

    @dp.message(Command("start"))
    async def start(msg: Message):
        await msg.answer("Выберите программу: AI или AI Product", reply_markup=kb_programs)

    @dp.message(F.text.in_(["AI", "AI Product"]))
    async def chosen(msg: Message):
        await msg.answer(
            f"Ок, работаем с «{msg.text}». Задайте вопрос через /ask или получите рекомендации /recommend.\n\n" + HELP
        )

    @dp.message(Command("help"))
    async def help_cmd(msg: Message):
        await msg.answer(HELP)

    @dp.message(Command("compare"))
    async def compare(msg: Message):
        ai_len = len(programs["ai"]["text_chunks"])
        aip_len = len(programs["ai_product"]["text_chunks"])
        await msg.answer(
            f"Сравнение программ:\n"
            f"• AI: {ai_len} фрагментов, ~{len(programs['ai']['courses'])} дисциплин\n"
            f"• AI Product: {aip_len} фрагментов, ~{len(programs['ai_product']['courses'])} дисциплин"
        )

    @dp.message(Command("ask"))
    async def ask(msg: Message):
        q = msg.text.removeprefix("/ask").strip()
        if not q:
            await msg.answer("Напишите: /ask ваш вопрос")
            return
        ans, sc = qa.ask(q)
        await msg.answer(f"{ans}\n\n(relevance={sc:.2f})")

    @dp.message(Command("recommend"))
    async def rec(msg: Message):
        await msg.answer(
            "Укажи программу (ai/ai_product) и список навыков через запятую.\n"
            "Пример: ai, python, ml, math"
        )

    @dp.message()
    async def flow(msg: Message):
        # попытка распарсить строку вида: "ai, python, ml"
        text = msg.text.lower()
        if text.startswith("ai") or text.startswith("ai_product"):
            parts = [p.strip() for p in text.split(",")]
            prog_key = parts[0]
            skills = ",".join(parts[1:]) if len(parts) > 1 else ""
            if prog_key not in programs:
                await msg.answer("Не понял программу. Используйте ai или ai_product.")
                return
            top, _ = recommend_courses(programs[prog_key], skills or "python,ml,ds")
            if not top:
                await msg.answer("Не удалось подобрать элективы. Попробуйте указать навыки: python, ml, ds, math, nlp, cv, pm, se")
                return
            lines = "\n".join(f"{i+1}. {c}" for i,c in enumerate(top))
            await msg.answer(f"Рекомендую (программа: {prog_key}):\n{lines}")
            return

        # fallback: не отвечаем на нерелевантные темы
        await msg.answer("Я отвечаю только на вопросы об обучении в двух программах ITMO. Используйте /ask, /recommend или /compare.")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())