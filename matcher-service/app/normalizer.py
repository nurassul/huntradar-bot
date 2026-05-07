import re
import unicodedata


# Приводит сырой текст вакансии к чистому виду для дальнейшей обработки.
# Шаги:
#     1. Unicode нормализация (убираем диакритику и хитрые символы)
#     2. Lowercase
#     3. Убираем HTML-теги если hh.kz вернул разметку
#     4. Заменяем спецсимволы на пробелы (кроме + и # — важны для C++, C#)
#     5. Схлопываем множественные пробелы
def normalize_text(text: str) -> str:
    if not text:
        return " "

    # Unicode NFC нормализация
    text = unicodedata.normalize("NFC", text)

    # Убираем HTML теги
    text = re.sub(r"<[^>]+>", " ", text)

    # Lowercase
    text = text.lower()

    # Заменяем переносы строк и табы на пробел
    text = re.sub(r"[\n\r\t]+", " ", text)

    # Убираем все кроме букв, цифр, пробелов, +,#,.,-
    text = re.sub(r"[^\w\s#+.\-]", " ", text, flags=re.UNICODE)

    # Схлопываем пробелы
    text = re.sub(r"\s+", " ", text).strip()

    return text

# Нормализует одно слово
def normalize_skill(skill: str) -> str:
    return normalize_text(skill).strip()

# Разбивает текст вакансии на предложения/строки.
# Нужно для weighted scoring — определяем контекст (must/nice).
# Разбиваем по точке, точке с запятой, переносу строки, буллетам
def split_into_sentences(text: str) -> list[str]:
    parts = re.split(r"[.;•·\-–—]", text)
    return [p.strip() for p in parts if len(p.strip()) > 3]

















