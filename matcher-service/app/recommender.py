from app.scorer import ScoringResult

LEARNING_TIPS: dict[str, str] = {
    "kafka": "Apache Kafka — Official Documentation + Confluent Course (Free)",
    "kubernetes": "Kubernetes—Start with minikube locally.",
    "docker": "Docker — Official Tutorial docker.com/get-started",
    "postgresql": "PostgreSQL — postgresqltutorial.com + practice on supabase",
    "redis": "Redis — redis.io/docs/getting-started",
    "fastapi": "FastAPI — fastapi.tiangolo.com/tutorial (the best doc in the universe)",
    "django": "Django — djangoproject.com/start",
    "react": "React — react.dev/learn (new doc)",
    "typescript": "TypeScript — typescriptlang.org/docs/handbook",
    "grpc": "gRPC — grpc.io/docs/languages/python/quickstart",
    "elasticsearch": "Elasticsearch — elastic.co/guide/en/elasticsearch/client/python-api",
    "microservices": "Microservices patterns — book 'Microservices Patterns' Chris Richardson",
    "clean architecture": "Clean Architecture — Uncle Bob's book",
    "terraform": "Terraform — developer.hashicorp.com/terraform/tutorials",
    "aws": "AWS — aws.amazon.com/free (Free Tier) + acloudguru",
}


def build_recommendation_message(
        result: ScoringResult,
        vacancy_title: str,
        employer: str = "",
        area: str = "",
        salary_from: int | None = None,
        salary_to: int | None = None,
        currency: str | None = None,
        key_skills: list[str] | None = None
) -> str:
    score_pct = int(result.final_score * 100)

    salary_text = _build_salary(salary_from, salary_to, currency)

    meta_parts = []
    if employer:
        meta_parts.append(f"🏢 {employer}")
    if area:
        meta_parts.append(f"📍 {area}")
    if salary_text:
        meta_parts.append(f"💰 {salary_text}")
    meta_block = "\n".join(meta_parts)

    skills_block = ""
    if key_skills:
        skills_block = "🛠 <b>Required skills:</b> " + ", ".join(key_skills[:10])

    if result.verdict == "full_match":
        return (
            f"✅ <b>Great match — {score_pct}%</b>\n\n"
            f"<b>{vacancy_title}</b>\n"
            f"{meta_block}\n\n"
            f"{skills_block}"
        ).strip()

    if result.verdict == "partial_match":
        missing_block = _build_missing_block(result.missing_skills)
        return (
            f"⚡ <b>Partial match — {score_pct}%</b>\n\n"
            f"<b>{vacancy_title}</b>\n"
            f"{meta_block}\n\n"
            f"{skills_block}\n\n"
            f"{missing_block}"
        ).strip()

    return ""

def _build_salary(
        salary_from: int | None,
        salary_to: int | None,
        currency: str | None
) -> str:
    cur = currency or ""
    if salary_from and salary_to:
        return f"{salary_from:,} – {salary_to:,} {cur}".replace(",", " ")
    if salary_from:
        return f"from {salary_from:,} {cur}".replace(",", " ")
    if salary_to:
        return f"up to {salary_to:,} {cur}".replace(",", " ")
    return "Salary not specified."

def _build_missing_block(missing_skills: list[str]) -> str:
    if not missing_skills:
        return ""

    lines = ["📚 <b>Learning tips:</b>"]
    for skill in missing_skills[:5]:
        tip = LEARNING_TIPS.get(skill)
        if tip:
            lines.append(f"• <b>{skill}</b> — {tip}")
        else:
            lines.append(f"• <b>{skill}</b>")

    return "\n".join(lines)












