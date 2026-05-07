
# Мапы для технологии.
# Для проверки или же нормализации то что написал юзер.
SKILLS_DICT: dict[str, list[str]] = {
    # Languages
    "python": ["python", "python3", "питон", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "java": ["java", "джава"],
    "kotlin": ["kotlin"],
    "go": ["golang", "go"],
    "rust": ["rust"],
    "c++": ["c++", "cpp", "c plus plus"],
    "c#": ["c#", "csharp", "dotnet", ".net"],
    "php": ["php"],
    "ruby": ["ruby", "ruby on rails", "ror"],
    "swift": ["swift"],

    # Web frameworks
    "fastapi": ["fastapi", "fast api"],
    "django": ["django", "джанго"],
    "flask": ["flask"],
    "aiohttp": ["aiohttp"],
    "express": ["express", "expressjs", "express.js"],
    "react": ["react", "reactjs", "react.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "angular": ["angular", "angularjs"],
    "nextjs": ["next.js", "nextjs", "next js"],

    # Databases
    "postgresql": ["postgresql", "postgres", "pg", "постгрес"],
    "mysql": ["mysql"],
    "mongodb": ["mongodb", "mongo"],
    "redis": ["redis"],
    "elasticsearch": ["elasticsearch", "elastic", "es"],
    "clickhouse": ["clickhouse"],
    "sqlite": ["sqlite"],

    # Message brokers
    "kafka": ["kafka", "apache kafka", "кафка"],
    "rabbitmq": ["rabbitmq", "rabbit", "amqp"],
    "celery": ["celery"],
    "nats": ["nats"],

    # DevOps & infra
    "docker": ["docker", "докер"],
    "docker compose": ["docker compose", "docker-compose"],
    "kubernetes": ["kubernetes", "k8s", "кубернетес"],
    "terraform": ["terraform"],
    "ansible": ["ansible"],
    "nginx": ["nginx"],

    # CI/CD
    "github actions": ["github actions", "gh actions"],
    "gitlab ci": ["gitlab ci", "gitlab-ci", ".gitlab-ci"],
    "jenkins": ["jenkins"],

    # Cloud
    "aws": ["aws", "amazon web services", "amazon aws"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "azure": ["azure", "microsoft azure"],

    # Python libs
    "sqlalchemy": ["sqlalchemy"],
    "alembic": ["alembic"],
    "pydantic": ["pydantic"],
    "aiogram": ["aiogram"],
    "pytest": ["pytest"],
    "celery": ["celery"],
    "numpy": ["numpy"],
    "pandas": ["pandas"],

    # Concepts & practices
    "rest api": ["rest", "rest api", "restful", "restful api"],
    "graphql": ["graphql"],
    "grpc": ["grpc", "protobuf", "proto"],
    "websocket": ["websocket", "websockets", "ws"],
    "microservices": ["microservices", "микросервисы", "микросервисная"],
    "clean architecture": ["clean architecture", "чистая архитектура"],
    "solid": ["solid", "solid principles"],
    "tdd": ["tdd", "test driven", "test-driven"],
    "git": ["git"],
    "linux": ["linux", "unix"],
    "agile": ["agile", "scrum", "kanban"],
}

# Ключевые слова для определения приоритета скилла в вакансии
MUST_HAVE_KEYWORDS = [
    "обязательно", "обязателен", "обязательное", "требуется", "требования",
    "обязательные требования", "must have", "must", "required", "необходимо",
    "нужно знать", "знание", "опыт работы с", "уверенное"
]

NICE_TO_HAVE_KEYWORDS = [
    "желательно", "будет плюсом", "плюс", "преимущество", "будет преимуществом",
    "nice to have", "optional", "приветствуется", "рассматриваем",
    "не обязательно", "будет большим плюсом"
]
