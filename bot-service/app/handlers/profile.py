from aiogram import Router, F
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

# --------------------------------------------------------------------------

# Стопаем поиск вакансии или включаем.
@router.message(F.text == "🔔 Notifications")
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











