import numpy as np
from dataclasses import dataclass

from app.skill_extractor import ExtractedSkill

from app.embedder import get_cached_embedding

MATCH_THRESHOLD = 0.75       # косинусное сходство ≥ этого = скилл засчитан
SEND_THRESHOLD = 0.75        # итоговый score ≥ этого = отправляем вакансию без оговорок
PARTIAL_SEND_THRESHOLD = 0.2 # ниже 20% = вакансия совсем не подходит, не отправляем


@dataclass
class SkillMatch:
    vacancy_skill: str
    user_skill: str | None
    similarity: float
    weight: float
    matched: bool

@dataclass
class ScoringResult:
    final_score: float
    matched_skills: list[SkillMatch]
    missing_skills: list[str]       # скиллы вакансии которых нет у юзера
    verdict: str                    # "full_match" | "partial_match" | "no_match"

# Косинусное сходство двух L2-нормализованных векторов = просто dot product.
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a,b))


# Считает насколько вакансия подходит пользователю.
# Алгоритм:
# 1. Для каждого скилла вакансии ищем лучший матч среди скиллов юзера
# 2. Если cosine similarity ≥ MATCH_THRESHOLD → скилл засчитан
# 3. Итоговый score = сумма весов засчитанных скиллов / сумма всех весов
# 4. Взвешивание: must-have скиллы (weight=1.0) важнее nice-to-have (weight=0.5)
def score_vacancy(
        vacancy_skills: list[ExtractedSkill],
        user_skills: list[str]
) -> ScoringResult:
    if not vacancy_skills:
        return ScoringResult(0.0, [], [], "no_match")

    if not user_skills:
        missing = [s.name for s in vacancy_skills]
        return ScoringResult(0.0,[], missing,"no_match")

    # Заранее берем эмбеддинги юзера
    user_embeddings = {skill: get_cached_embedding(skill) for skill in user_skills}

    matches: list[SkillMatch] = []
    total_weight = 0.0
    matched_weight = 0.0

    for vs in vacancy_skills:
        total_weight += vs.weight
        vacancy_vec = get_cached_embedding(vs.name)

        best_skill = None
        best_sim = 0.0

        for user_skill, user_vec in user_embeddings.items():
            sim = cosine_similarity(vacancy_vec, user_vec)
            if sim > best_sim:
                best_sim = sim
                best_skill = user_skill


        is_matched = best_sim >= MATCH_THRESHOLD

        if is_matched:
            matched_weight += vs.weight

        matches.append(SkillMatch(
            vacancy_skill=vs.name,
            user_skill=best_skill,
            similarity=round(best_sim, 3),
            weight=vs.weight,
            matched=is_matched,
        ))

    final_score = matched_weight / total_weight if total_weight > 0 else 0.0
    missing = [m.vacancy_skill for m in matches if not m.matched and m.weight == 1.0]

    if final_score >= SEND_THRESHOLD:
        verdict = "full_match"
    elif final_score >= PARTIAL_SEND_THRESHOLD:
        verdict = "partial_match"
    else:
        verdict = "no_match"

    return ScoringResult(
        final_score=round(final_score, 3),
        matched_skills=matches,
        missing_skills=missing,
        verdict=verdict,
    )

















