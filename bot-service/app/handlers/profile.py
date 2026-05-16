from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..keyboards.kb import main_menu, notifications_keyboard
from app.db import get_user_skills, get_user_query, toggle_notifications

# Обработчик для кнопки Profile and etc.

# Наш обработчик. Типо как контроллер like in a Spring.
# Будет обрабатывать сообщения или команды юзера
router = Router()

# --------------------------------------------------------------------------

# Выводим общую инфу про юзера.
# Его скиллы и запрос все такое
@router.message(F.text == "👤 My profile")
@router.message(Command("profile"))
async def profile(msg: Message):
    skills = await get_user_skills(msg.from_user.id)
    query = await get_user_query(msg.from_user.id)

    skills_text = ", ".join(skills) if skills else "not found - write /start"
    query_text = query or "not found - write /start"

    await msg.answer(
        f"👤 <b>Your profile</b>\n\n"
        f"🛠 Skills: {skills_text}\n"
        f"🔍 Query: {query_text}",
        reply_markup=main_menu()
    )

@router.message(Command("help"))
async def show_help(msg: Message):
    help_text = (
        "🤖 <b>Welcome to HuntRadar! Your Personal AI-Recruiter.</b>\n\n"
        "Unlike standard job boards that spam you with irrelevant offers based on simple keywords, HuntRadar uses a smart matching algorithm to find vacancies that truly fit your exact tech stack. 🎯\n\n"
        "<b>⚙️ How the Magic Works:</b>\n"
        "1. <b>Build your stack:</b> Add your specific hard skills (e.g., <i>Java 17, PostgreSQL, Docker, Kafka</i>).\n"
        "2. <b>Set your target:</b> Tell me your desired job title (e.g., <i>Java Backend Developer</i>).\n"
        "3. <b>Background parsing:</b> I continuously monitor job boards for fresh postings.\n"
        "4. <b>AI Scoring:</b> My internal system reads the job description and calculates a <b>Match Score (%)</b> against your profile.\n"
        "5. <b>Smart Delivery:</b> I filter out the \"noise\" (like Senior roles if you are a Junior) and instantly message you only the highly relevant matches!\n\n"
        "<b>📌 Bot Commands:</b>\n"
        "/start — Restart the bot and initialize your profile.\n"
        "/profile — View, update, or add new technical skills to your stack.\n"
        "/notify — Turn on or off notifications about vacancies\n"
        "/help — Show this help message.\n\n"
        "<b>❓ FAQ: Why am I not receiving any job alerts?</b>\n"
        "👉 <i>Don't worry, the bot is not broken! I am strictly filtering out irrelevant jobs to protect your time. If you haven't received anything, it means there are currently no fresh vacancies on the market with a high enough Match Score for your specific profile.\n\n"
        "💡 <b>Pro Tip:</b> Go to /profile and add more specific hard skills. The more skills you provide, the more accurate the matching algorithm becomes!</i>"
    )
    await msg.answer(help_text)

# --------------------------------------------------------------------------

# Стопаем поиск вакансии или включаем.
@router.message(F.text == "🔔 Notifications")
@router.message(Command("notify"))
async def notifications_menu(msg: Message):
    query = await get_user_query(msg.from_user.id)
    is_active = query is not None

    status = "turn on ✅" if is_active else "off ❌"
    await msg.answer(
        f"Notification about vacancies now <b>{status}</b>",
        reply_markup=notifications_keyboard(is_active)
    )


@router.callback_query(F.data.startswith("notif:"))
async def toggle_notif(callback: CallbackQuery):
    action = callback.data.split(":")[1]
    active = action == "on"
    await toggle_notifications(callback.from_user.id, active)

    status = "turn on ✅" if active else "off ❌"
    await callback.message.edit_text(
        f"Notifications <b>{status}</b>",
        reply_markup=notifications_keyboard(active)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("vfb:"))
async def vacancy_feedback(callback: CallbackQuery):
    _, verdict, vacancy_id= callback.data.split(":")

    reaction = "👍 Good!" if verdict == "good" else "Okay, I will filter more precisely"
    await callback.answer(reaction)

    await callback.message.edit_reply_markup(reply_markup=None)











