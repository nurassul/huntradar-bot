from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from ..keyboards.kb import main_menu, area_keyboard
from app.handlers.states import OnboardingFSM, EditFSM
from ..skill_normalizer import extract_skills_from_user_input

from app.db import register_user, save_user_query, save_user_skills, get_user_query, get_user_skills, \
    get_user_query_area
from ..rd_cache import get_history

router = Router()


# Command:
# ───────────────────────── /start ─────────────────────────

# Когда команда /start - регистрируем нового юзера или же welcoming и т.д.
# В начале сначала проверка типо существует ли такой пользователь.
# Если существует тогда перекидываем в main_menu()
# Если нету тогда ждем ввода скиллов
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await register_user(msg.from_user.id, msg.from_user.username)

    skills = await get_user_skills(msg.from_user.id)
    if skills:
        # Юзер уже регался и написал свои скиллы
        await msg.answer(
            f"👋 Welcome back!\n\nYour skills: {', '.join(skills)}",
            reply_markup=main_menu()
        )
        return

    await msg.answer(
        "👋 Hello! I am <b>HuntRadar Bot</b> - I will be finding suitable IT vacancies on hh.kz\n\n"
        "At first write your skills, separated by commas. (,)\n\n"
        "<i>For example: Python, FastAPI, Postgresql, Docker</i>",
    )
    # Ждем ввода скиллов
    await state.set_state(OnboardingFSM.waiting_skills)


# Тут ждем пока юзер введет свои скиллы и также проверка правильно ли ввел юзер свои скиллы.
# Когда уже ввел идем дальше и просим написать ЗАПРОС.
@router.message(OnboardingFSM.waiting_skills)
async def onboarding_skills(msg: Message, state: FSMContext):
    if "," not in msg.text and " " in msg.text:
        await msg.answer(
            "😅 It seems you simply listed the skills separated by spaces.\n\n"
            "Please use <b>commas!!!!!!</b> Do not break me!"
            "Rewrite the list again, separated by <b>COMMAS (,) </b>"
        )

    raw_skills = [s.strip() for s in msg.text.split(",") if s.strip()]

    if len(raw_skills) < 2:
        await msg.answer("Please enter at least 2 skills separated by commas 🙏")
        return

    normalized = extract_skills_from_user_input(raw_skills)
    await state.update_data(skills=normalized)

    await msg.answer(
        f"✅ I've saved the skills: <b>{','.join(normalized)}</b>\n\n"
        "Now write a search query - how you will search for vacancies.\n\n"
        "<i>For example: Python backend developer</i>"
    )

    await state.set_state(OnboardingFSM.waiting_query)


# Тут ждем пока юзер введет запрос по которому мы будем искать вакансий.
# Когда юзер уэе ввел запрос ждем выбора региона.
@router.message(OnboardingFSM.waiting_query)
async def onboarding_query(msg: Message, state: FSMContext):
    query = msg.text.strip()

    if len(query) < 3:
        await msg.answer("Query too short, please enter again.")
        return

    await state.update_data(query=query)

    await msg.answer(
        f"🔍 Query: <b>{query}</b>\n\nChoose region:",
        reply_markup=area_keyboard()
    )

    await state.set_state(OnboardingFSM.waiting_area)


# Тут ждем выбора региона поиска.
# Берем инфу с callback_data с началом area:
# Если все норм тогда сохраняем скиллы юзера и его запрос.
# Выводим конечный результат и перекидываем юзера в main_menu()
@router.callback_query(OnboardingFSM.waiting_area, F.data.startswith("area:"))
async def onboarding_area(callback: CallbackQuery, state: FSMContext):
    area = callback.data.split(":")[1]
    data = await state.get_data()

    await save_user_skills(callback.from_user.id, data["skills"])
    await save_user_query(callback.from_user.id, data["query"], area)
    await state.clear()

    area_names = {"40": "Kazakhstan", "113": "Russia"}
    await callback.message.edit_text(
        f"🚀 <b>Everything is ready!</b>\n\n"
        f"Skills: {', '.join(data['skills'])}\n"
        f"Query: {data['query']}\n"
        f"Region: {area_names.get(area, area)}\n\n"
        f"I will send you suitable vacancies. Parcing every 15 minutes 🔍"
    )

    await callback.message.answer("Main menu", reply_markup=main_menu())
    await callback.answer()


# ───────────────────────── Последние вакансии─────────────────────────
# Когда юззер выбирает кнопку "📄 Last vacancies", получаем из Редиса то что сохранили.
# Выводим только последние 5 вакансии из кэша.
@router.message(F.text == "📄 Last vacancies")
async def send_last_vacancies(msg: Message):
    vacancies = await get_history(msg.from_user.id)

    if not vacancies:
        await msg.answer("Nothing yet! Either I haven't found anything yet, or the data is outdated")

    await msg.answer("Here last 5 vacancies from history")

    for vac in vacancies:
        text = (
            f"🔹 <b>{vac['title']}</b>\n"
            f"📄 Description:\n {vac.get('message_text', 'Not found')}\n\n"
            f"<a href='{vac['url']}'>Open vacancy</a>"
        )
        await msg.answer(text)


# ───────────────────────── Редактирование скиллов ─────────────────────────

# Когда вводит текст или выбирает кнопку - Edit skills даем юзеру поменять скиллы.
# Перекидываем статус в ожидании waiting_new_skills
@router.message(F.text == "✏️ Change skills")
async def edit_skills_start(msg: Message, state: FSMContext):
    current = await get_user_skills(msg.from_user.id)
    await msg.answer(
        f"Current skills: <b>{', '.join(current) if current else 'not found'}</b>\n\n"
        "Enter new skills <b>separated by commas</b>: "
    )
    await state.set_state(EditFSM.waiting_new_skills)


# Тут тоже самое как в добавлении скиллов.
@router.message(EditFSM.waiting_new_skills)
async def edit_skills_save(msg: Message, state: FSMContext):
    if ("," not in msg.text and " " in msg.text):
        await msg.answer(
            "😅 It seems you simply listed the skills separated by spaces.\n\n"
            "Please use <b>commas!!!!!!</b> Do not break me!\n"
            "Rewrite the list again, separated by <b>COMMAS (,) </b>"
        )

    raw_skills = [s.strip() for s in msg.text.split(",") if s.strip()]
    if len(raw_skills) < 2:
        await msg.answer("Please enter at least 2 skills separated by commas 🙏")
        return

    normalized = extract_skills_from_user_input(raw_skills)
    await save_user_skills(msg.from_user.id, normalized)
    await state.clear()
    await msg.answer(
        f"✅ Skills updated: <b>{', '.join(normalized)}</b>",
        reply_markup=main_menu()
    )


# ───────────────────────── Редактирование запроса ─────────────────────────

# То же самое как в скиллах
@router.message(F.text == "🔍 Change query & area")
async def edit_query_start(msg: Message, state: FSMContext):
    current = await get_user_query(msg.from_user.id)
    await msg.answer(
        f"Current query: <b>{current or 'not found'}</b>\n\nEnter new:"
    )

    await state.set_state(EditFSM.waiting_new_query)


@router.message(EditFSM.waiting_new_query)
async def edit_query_save(msg: Message, state: FSMContext):
    query = msg.text.strip()
    if len(query) < 3:
        await msg.answer("Too short query!")
        return

    current = await get_user_query_area(msg.from_user.id)
    area_names = {"40": "Kazakhstan", "113": "Russia"}

    await state.update_data(query=query)
    await msg.answer(
        f"✅ Query: <b>{query}</b>\n"
        f"Current area: <b>{area_names[current] or 'not found'}</b>\n\nSelect new:",
        reply_markup=area_keyboard()
    )
    await state.set_state(EditFSM.waiting_new_area)

@router.callback_query(EditFSM.waiting_new_area, F.data.startswith("area:"))
async def edit_area_save(callback: CallbackQuery, state: FSMContext):
    area = callback.data.split(":")[1]
    data = await state.get_data()
    query = data['query']

    await save_user_query(callback.from_user.id, query, area)
    await state.clear()

    area_names = {"40": "Kazakhstan", "113": "Russia"}
    await callback.message.answer(
        f"🚀 <b>Updated successfully</b>\n\n"
        f"Query: {query}\n"
        f"Region: {area_names.get(area, area)}\n\n",
        reply_markup=main_menu()
    )
    await callback.answer()
