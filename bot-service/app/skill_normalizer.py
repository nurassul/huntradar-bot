
# Для обработки и нормализации инпута юзера про скиллы.

from app.skills_dict import NICE_TO_HAVE_KEYWORDS, SKILLS_DICT

from app.normalizer import normalize_text, split_into_sentences


# Тут сначала нормализируем скиллы по алгоритму.
# Потом сравниваем скиллы через мапу наших скиллов.
# В мапе скиллов есть алиасы этих скиллов и по ним сравниваем затем добавляем базовые имя скиллов.
def extract_skills_from_user_input(raw_skills: list[str]) -> list[str]:
    result = []
    for raw in raw_skills:
        normalized = normalize_text(raw)
        matched = False

        for skill_name, aliases in SKILLS_DICT.items():
            for alias in aliases:
                if alias == normalized:
                    if skill_name not in result:
                        result.append(skill_name)
                    matched = True
                    break
            if matched:
                break

        # Если не нашли в словаре добавляем как есть
        if not matched and normalized:
            result.append(normalized)

    return result

















