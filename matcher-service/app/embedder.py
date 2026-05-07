from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

# Превращаем список скиллов в матрицу эмбеддингов.
def embed_skills(skills: list[str]) -> np.ndarray:
    if not skills:
        return np.array([])

    # Превращает список текстовых скиллов (например, ['Python', 'Docker'])
    # в матрицу векторов (эмбеддингов).
    # Каждый скилл становится массивом из 384 чисел.
    # normalize_embeddings=True делает так, чтобы длина векторов была равна 1 —
    # это сильно ускоряет и упрощает дальнейший расчет косинусного сходства.
    model = get_model()
    embeddings = model.encode(skills, normalize_embeddings=True)
    return embeddings

# Эмбеддинг одного скилла. Для кэширования частых запросов.
def embed_single(skill: str) -> np.ndarray:
    return embed_skills([skill])[0]


# Кэшируем эмбеддинги частых скиллов.
@lru_cache(maxsize=512)
def cached_embed(skill: str) -> tuple:
    vec = embed_single(skill)
    return tuple(vec.tolist())

def get_cached_embedding(skill: str) -> np.ndarray:
    return np.array(cached_embed(skill))