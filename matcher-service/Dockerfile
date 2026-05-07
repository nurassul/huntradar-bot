FROM python:3.11-slim

WORKDIR /service

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu

# Зависимости отдельным слоем для кэша
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скачиваем модель при билде (не при запуске)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY app/ app/

CMD ["python", "-m", "app.main"]
