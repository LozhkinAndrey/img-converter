FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /srv

RUN pip install --no-cache-dir "poetry>=1.8,<2"

# Копируем с масками: poetry.lock может ещё не существовать
COPY pyproject.toml* poetry.lock* ./
RUN poetry install --no-root --without dev

COPY app ./app
COPY static ./static

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
