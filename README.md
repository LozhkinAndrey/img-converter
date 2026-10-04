# Image Converter — учебный проект

Сайт-конвертер изображений (FastAPI + Pillow) с метриками Prometheus,
дашбордом Grafana и нагрузочным тестом на Locust.

## Стек и минимальные версии

- Python 3.11+, FastAPI >= 0.111, Pillow >= 10.3, prometheus-fastapi-instrumentator >= 7.0
- Docker + Docker Compose (v2, команда `docker compose`)
- Prometheus 2.53, Grafana 11.1, Locust >= 2.24

## Допущения

- Порты: сайт и API — **8000**, Prometheus — **9090**, Grafana — **3000**.
  Если заняты — поменяйте левую часть пробросов в `docker-compose.yml`.
- Лимит загрузки: 10 МБ, форматы JPEG/PNG, максимум 40 млн пикселей.
- Grafana: логин `admin`, пароль `admin` (докер-переменные в compose).

## Запуск

```bash
docker compose up -d          # стартует app + prometheus + grafana
docker compose ps             # убедиться, что все три контейнера Up
