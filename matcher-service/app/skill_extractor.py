import re
from dataclasses import dataclass, field

from app.skills_dict import NICE_TO_HAVE_KEYWORDS, SKILLS_DICT

from app.normalizer import normalize_text, split_into_sentences


@dataclass
class ExtractedSkill:
    name: str
    weight: float
    context: str = ""


# Определяет вес скилла по контексту предложения.
# Если предложение содержит must-have маркеры → 1.0
# Если nice-to-have маркеры → 0.5
# По умолчанию → 1.0 (считаем обязательным)
def _detect_weight(sentence: str) -> float:
    for keyword in NICE_TO_HAVE_KEYWORDS:
        if keyword in sentence:
            return 0.5
    return 1.0

# Извлекает скиллы из текста вакансии с их весами.
#  Алгоритм:
#  1. Нормализуем весь текст
#  2. Разбиваем на предложения (для определения контекста must/nice)
#  3. В каждом предложении ищем алиасы из словаря
#  4. Возвращаем уникальные скиллы (дубли мержим, берём макс вес)
def extract_skills_from_vacancy(raw_text: str) -> list[ExtractedSkill]:
    normalized = normalize_text(raw_text)
    sentences = split_into_sentences(normalized)

    found: dict[str, ExtractedSkill] = {}
    for sentence in sentences:
        weight = _detect_weight(sentence)

        for cannonical_name, aliases in SKILLS_DICT.items():
            if cannonical_name in found and found[cannonical_name].weight >= weight:
                continue # Уже нашли с таким же или выше весом

            for alias in aliases:
                # Только одно слово без коллизии как отдельное слово.
                pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
                if re.search(pattern, sentence):
                    # Опять проверка может мы до этого находили, но веса разные.
                    if cannonical_name not in found or found[cannonical_name].weight < weight:
                        found[cannonical_name] = ExtractedSkill(
                            name=cannonical_name,
                            weight=weight,
                            context=sentence[:80]
                        )
                    break
    return list(found.values())


















