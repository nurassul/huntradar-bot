from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# Просто главное меню.
def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="👤 My profile"),
        KeyboardButton(text="✏️ Change skills")
    )
    builder.row(
        KeyboardButton(text="🔍 Change query"),
        KeyboardButton(text="🔔 Notifications")
    )
    builder.row(
        KeyboardButton(text="📄 Last vacancies"),
    )

    return builder.as_markup(resize_keyboard=True)

# Кнопки над сообщением про регионы.
def area_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Kazakhstan", callback_data="area:40"),
        InlineKeyboardButton(text="🌍 Whole world", callback_data="area:all"),
    )
    builder.row(
        InlineKeyboardButton(text="Russia", callback_data="area:113"),
    )
    return builder.as_markup()


#  Кнопки над сообщением про вакансии.
def vacancy_keyboard(url: str, vacancy_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📄 Open vacancy", url=url)
    )
    builder.row(
        InlineKeyboardButton(text="👍 Good", callback_data=f"vfb:good:{vacancy_id}"),
        InlineKeyboardButton(text="👎 Bad", callback_data=f"vfb:bad:{vacancy_id}")
    )

    return builder.as_markup()


# Кнопки над сообщением про уведомления.
def notifications_keyboard(is_active: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    label = "🔕 Mute" if is_active else "🔔 Turn on"
    callback = "notif:off" if is_active else "notif:on"
    builder.row(InlineKeyboardButton(text=label, callback_data=callback))
    return builder.as_markup()
