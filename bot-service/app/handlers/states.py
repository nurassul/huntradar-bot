from aiogram.fsm.state import StatesGroup, State


class OnboardingFSM(StatesGroup):
    waiting_skills = State() # юзер вводит свои скиллы
    waiting_query = State() # юзер вводит поисковый запрос
    waiting_area = State() # юзер выбирает регион


class EditFSM(StatesGroup):
    waiting_new_skills = State()
    waiting_new_query = State()