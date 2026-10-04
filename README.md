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
```

## Проверка сайта

- Откройте  localhost:8000 — загрузите JPG/PNG, выберите операцию, скачайте результат.
- Проверка API: curl http://localhost:8000/api/health → {"status":"ok",...}.
- Метрики приложения: localhost:8000/metrics
- Сырые метрики Prometheus: localhost:9090

## Grafana
- Адрес: localhost:3000, логин/пароль: admin/admin.
- Дашборд «Image Converter» появится сам: источник данных и дашборд провиженятся из volumes при старте (папка monitoring/grafana/). Если вкладка не появилась — подождите ~30 секунд (updateIntervalSeconds).

## Нагрузочное тестирование
Требуется Python 3.11+ на хост-машине.
```bash
cd loadtest
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Лёгкий прогон: 10 пользователей, рост по 2/сек, 1 минута
locust -f locustfile.py --headless -u 10 -r 2 -t 1m --host http://localhost:8000

# Стресс-тест: 100 пользователей, рост по 10/сек, 5 минут
locust -f locustfile.py --headless -u 100 -r 10 -t 5m --host http://localhost:8000

```
Locust сам считает коды ответов и ошибки — итоговая статистика появится 
в терминале после прогона (или через localhost:8089, если запустить 
без --headless).

## Что смотреть в Grafana во время теста
- RPS по эндпоинтам — фактическая нагрузка; Locust может «просить» больше, 
чем сервер успевает (очередь растёт, RPS выходит на плато).
- Латентность p95/p99 — следите, на каком RPS p95 начинает расти. 
Резкий рост после стабильного плато — точка насыщения CPU 
(Pillow — CPU-bound, один uvicorn-воркер = одно ядро).
- Доля ошибок 5xx — когда появляются первые ошибки и как растут. 
Ошибки при росте нагрузки обычно означают таймауты или исчерпание ресурсов.
- Память (RSS) — обработка изображений «ест» RAM: каждая картинка 
1200×1200 RGB ≈ 4 МБ, плюс копии при операциях. 
Смотрите, выходит ли память на плато (норма) или растёт линейно 
(утечка — повод для аларма). Общий контейнерный лимит проверяйте 
командой docker stats img-converter-app.
- Время обработки по операциям — сравните resize/grayscale/rotate: 
разница покажет, какая операция самая дорогая, и поможет спланировать воркеры.