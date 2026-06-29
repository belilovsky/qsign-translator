# QSign Translator 🧏 — Планировщик жестового языка для русского, казахского и английского языков

![Status](https://img.shields.io/badge/status-production-green)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
[![CI](https://github.com/belilovsky/qsign-translator/actions/workflows/ci.yml/badge.svg)](https://github.com/belilovsky/qsign-translator/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

**QSign Translator** — прототип системы перевода текста на русском, казахском и английском языках в план жестовой записи (sign plan). Проект создаёт черновики жестовой записи, поддерживает ревью-воркфлоу с участием носителей языка, формирует AI-брифы для внешних генераторов видео и управляет пайплайном публикации. Ядро продукта узкое и намеренно не включает ASR или генерацию аватаров — эти функции вынесены за адаптеры.

Система доступна как CLI-инструмент, браузерный UI и REST API. Встроенный рантайм-лексикон объединяет выверенный seed-набор с архивным глоссарием на основе корпуса «Слово» для русского языка, ручными KRSL-записями для казахского и базовым EN/ASL-oriented seed-слоем для английского. Для неизвестных слов используется дактильный (пальцевый) алфавит как прозрачный fallback. Проект не позиционируется как сертифицированный переводчик жестового языка — это инструмент для операторов, лингвистов и исследователей, позволяющий ускорить подготовку sign-контента.

Производственная инсталляция развёрнута на **[qsign.qdev.run](https://qsign.qdev.run)**. Серверная часть построена на FastAPI + uvicorn, данные хранятся в PostgreSQL, файловые артефакты — в MinIO (S3-совместимое хранилище). Контейнеризация через Docker Compose обеспечивает воспроизводимость окружения.

---

## Оглавление

- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [API](#api)
- [Развёртывание](#развёртывание)
- [Разработка](#разработка)
- [Связанные проекты](#связанные-проекты)
- [Лицензия](#лицензия)

---

## Возможности

| Функция | Описание |
|---------|----------|
| **Text-to-Sign-Plan** | Преобразование русского, казахского и английского текста в детерминированный план жестовой записи |
| **Дактильный fallback** | Прозрачный пальцевый алфавит для неизвестных слов вместо галлюцинаций |
| **Маршрутизация языков** | Явный выбор или автоматическое определение языка (RU / KZ / EN) и выбор соответствующего лексикона |
| **CLI-инструмент** | Консольная команда `qsign` для быстрого перевода без запуска сервера |
| **Браузерный UI** | Веб-интерфейс с просмотром, редактированием и ревью sign-планов |
| **Ревью-воркфлоу** | Защищённые ревью-сессии с оценками, заметками, блокирующими флагами и статусом |
| **Review Video** | Генерация MP4-превью черновика через ffmpeg для визуальной верификации |
| **AI-видео брифы** | Пакетный экспорт промптов, операторских заданий и чек-листов для внешних AI-генераторов |
| **Render-контракт** | Строгий контракт на рендеринг: имя файла, блокировщики публикации, порядок юнитов |
| **Публикационный конвейер** | Жизненный цикл: `draft` → `final_review_pending` → `publishable` / `rejected` |
| **Aудиторский след** | Полная история изменений для каждого задания на перевод |
| **Интеграция с S3** | Хранение видео-артефактов через MinIO (S3-совместимое хранилище) |
| **ASR-адаптер** | Опциональный интерфейс для распознавания речи (faster-whisper) |

---

## Архитектура

```
┌─────────────────────────────────────────────────────────────────────┐
│                        QSign Translator                             │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │   Browser    │  │    CLI       │  │   External AI Video       │  │
│  │     UI       │  │  (qsign)     │  │   Generators              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────────┘  │
│         │                 │                      │                   │
│         ▼                 ▼                      ▼                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    FastAPI (ASGI)                             │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐   │   │
│  │  │ Auth /  │ │ Translate│ │  Review  │ │ AI Video       │   │   │
│  │  │ Audit   │ │ API      │ │  API     │ │  Brief API     │   │   │
│  │  └─────────┘ └──────────┘ └──────────┘ └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Core Pipeline                              │   │
│  │                                                               │   │
│  │  Text → Normalize → Lang Detect → Lexicon Lookup →           │   │
│  │                          ↓                                    │   │
│  │  ┌────────────────────────────────────┐                      │   │
│  │  │  Found ? ──yes──→ Gloss mapping    │                      │   │
│  │  │  No    ─────────→ Dactyl fallback  │                      │   │
│  │  └────────────────────────────────────┘                      │   │
│  │                          ↓                                    │   │
│  │                     Sign Plan                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │    PostgreSQL 16     │  │    MinIO (S3)     │  │    ffmpeg     │  │
│  │  - Jobs              │  │  - Video assets   │  │  - Preview    │  │
│  │  - Review sessions   │  │  - Render output  │  │    MP4 gen    │  │
│  │  - Audit trail       │  │                   │  │              │  │
│  └──────────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| **Язык** | Python 3.12 |
| **Веб-фреймворк** | FastAPI 0.115+ |
| **ASGI-сервер** | Uvicorn 0.30+ |
| **База данных** | PostgreSQL 16 (через psycopg) |
| **Объектное хранилище** | MinIO (S3-совместимое) |
| **Валидация** | Pydantic v2 |
| **Медиа** | ffmpeg (ревью-видео) |
| **ASR (опционально)** | faster-whisper |
| **Контейнеризация** | Docker Compose |
| **CI/CD** | GitHub Actions |
| **Тестирование** | pytest, httpx |
| **Линтер** | Ruff |

---

## Быстрый старт

### 1. CLI (только базовая установка)

```bash
git clone https://github.com/belilovsky/qsign-translator.git
cd qsign-translator
python3 -m pip install -e ".[test]"
qsign "Привет, меня зовут Александр"
qsign "Сәлеметсіз бе, маған көмек керек"
```

CLI выводит JSON-план жестовой записи в stdout.

### 2. Браузерный UI и локальное API

```bash
python3 -m pip install -e ".[api,db,test]"
cp .env.example .env
docker compose up -d postgres minio
uvicorn qsign_translator.api:app --reload
```

После запуска откройте **http://127.0.0.1:8000/**.

### 3. API-only (минимальный запуск)

```bash
python3 -m pip install -e ".[api,db]"
uvicorn qsign_translator.api:app --reload
curl -X POST http://127.0.0.1:8000/v1/translate/text \
  -H 'content-type: application/json' \
  -d '{"text":"Привет, меня зовут Александр"}'
```

### 4. Проверка работоспособности

```bash
./scripts/check.sh                    # Быстрая проверка: компиляция, тесты, CLI smoke
python3 scripts/smoke_live.py --base-url https://qsign.qdev.run  # Live smoke
pytest -q                              # Модульные тесты
```

### 5. Лёгкий benchmark ядра

```bash
make benchmark
```

---

## Структура проекта

```
qsign-translator/
├── src/qsign_translator/
│   ├── __init__.py
│   ├── __main__.py          # Точка входа python -m
│   ├── api.py               # FastAPI-приложение и маршруты
│   ├── cli.py               # CLI-интерфейс (команда qsign)
│   ├── planner.py           # Ядро: text-to-sign-plan
│   ├── lexicon.py           # Рантайм-лексикон
│   ├── dactyl.py            # Дактильный fallback
│   ├── normalize.py         # Нормализация текста
│   ├── language.py          # Определение и маршрутизация языка
│   ├── asr.py               # ASR-адаптер (опционально)
│   ├── ai_video_brief.py    # Генерация AI-видео брифов
│   ├── video_plan.py        # План рендеринга видео
│   ├── preview_video.py     # Генерация ревью-MP4
│   ├── db.py                # Работа с PostgreSQL и MinIO
│   ├── settings.py          # Конфигурация через env-переменные
│   ├── risk.py              # Классификация рисков для доменов
├── public/
│   ├── index.html           # SPA-клиент
│   ├── static/
│   │   ├── app.js           # Клиентская логика
│   │   └── styles.css       # Стили
├── infra/db/migrations/     # SQL-миграции
├── scripts/                 # Вспомогательные скрипты
│   ├── check.sh             # Полная проверка проекта
│   ├── smoke_live.py        # Live smoke-тестирование
│   ├── build_runtime_lexicon.py  # Сборка лексикона
│   ├── seed_db.py           # Начальное заполнение БД
│   └── apply_migrations.py  # Применение миграций
├── tests/                   # Модульные и интеграционные тесты
├── docs/                    # Документация
├── data/                    # Рантайм-данные (лексиконы, оверрайды)
├── experiments/             # Экспериментальные наработки
├── docker-compose.yml       # Docker Compose (api + postgres + minio)
├── Dockerfile               # Docker-образ
└── pyproject.toml           # Конфигурация пакета
```

---

## API

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `GET /health` | GET | Проверка работоспособности сервиса |
| `POST /v1/translate/text` | POST | Перевод текста в sign-plan |
| `GET /v1/jobs/{job_id}` | GET | Получение сохранённого задания |
| `GET /v1/jobs/{job_id}/render-plan` | GET | План рендеринга видео |
| `GET /v1/jobs/{job_id}/review-video` | GET | Скачивание ревью-MP4 |
| `GET /v1/jobs/{job_id}/ai-video-brief` | GET | AI-бриф для внешнего генератора |
| `POST /v1/ai-video-batch-brief` | POST | Пакетный AI-бриф для нескольких заданий |
| `POST /v1/review/login` | POST | Открыть cookie-сессию ревью по токену |
| `GET /v1/review/me` | GET | Текущая роль и способ review-доступа |
| `GET /v1/review/jobs` | GET | Очередь ревью с фильтрами (защищённый) |
| `GET /v1/review/system-status` | GET | Снимок состояния БД, ffmpeg и очереди |
| `GET /v1/review/coverage-report` | GET | Сводка по fallback и покрытию |
| `GET /v1/review/lexicon-candidates` | GET | Кандидаты на пополнение словаря |
| `POST /v1/review/lexicon-candidates` | POST | Добавить словарный кандидат |
| `PATCH /v1/review/jobs/{job_id}/publish-status` | PATCH | Установка статуса публикации |
| `GET /v1/review/audit` | GET | Аудиторский след по заданиям |

---

## Развёртывание

### Docker Compose (рекомендованный способ)

```bash
docker compose up -d
```

Сервисы:
- **API**: порт 8080 (конфигурируется через `QSIGN_API_PORT`)
- **PostgreSQL 16**: порт 54329 (внешний), `qsign` database
- **MinIO**: порт 19000 (S3 API), 19001 (Web UI)

### Переменные окружения

Скопируйте `.env.example` в `.env` и настройте:

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `POSTGRES_DB` | Имя БД | `qsign` |
| `POSTGRES_USER` | Пользователь БД | `qsign` |
| `POSTGRES_PASSWORD` | Пароль БД | `change-me-local` |
| `S3_ENDPOINT` | URL MinIO | `http://minio:9000` |
| `S3_ACCESS_KEY` | Ключ доступа S3 | `qsign-local` |
| `S3_SECRET_KEY` | Секретный ключ S3 | `change-me-local-minio` |
| `QSIGN_API_PORT` | Порт API | `8080` |
| `QSIGN_REVIEW_TOKEN` | Общий bootstrap-token review API | `change-me-review-token` |
| `QSIGN_REVIEW_SESSION_SECRET` | Секрет подписи review cookie-сессии | не задан |

### Production

Для production-развёртывания используйте отдельный `.env` с надёжными паролями, включите HTTPS через reverse proxy (nginx/Caddy), настройте регулярное резервное копирование PostgreSQL и MinIO.

---

## Разработка

### Установка для разработки

```bash
git clone https://github.com/belilovsky/qsign-translator.git
cd qsign-translator
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -e ".[api,db,test]"
```

### Запуск тестов

```bash
pytest -q                       # Модульные тесты
./scripts/check.sh              # Полная проверка
```

### Сборка лексикона

```bash
python3 scripts/build_runtime_lexicon.py
```

Рантайм-лексикон строится из двух источников:
- `data/curated_overrides.json` — выверенные ручные фразы, алиасы, казахские и английские seed-записи
- `data/import_sources/slovo/` — архивный корпус для широкого покрытия RU

### Политика репозитория

- Активная разработка ведётся только в canonical checkout
- Утверждённые оверрайды отделены от импортированного корпуса
- Никакой сгенерированный sign не считается авторитетным без проверки носителем языка

### Правила проекта

1. Не выдавать сгенерированный перевод за авторитетный без ревью носителем жестового языка
2. Каждый датасет и модель должны иметь лицензию и статус согласия перед использованием в production
3. Для высокорисковых доменов (медицина, юриспруденция, экстренные службы, финансы) обязателен человеческий fallback
4. Неизвестные слова должны прозрачно деградировать до дактиля/субтитров, а не до галлюцинаций

---

## Связанные проекты

- [QazLake](https://github.com/belilovsky/qazlake) — конвейер сбора и обогащения новостного контента
- [QazCompute](https://github.com/belilovsky/qazcompute) — платформа AI-обогащения (NER, sentiment, classification)

---

## Лицензия

Проект распространяется под лицензией MIT. Подробнее — в файле [LICENSE](LICENSE).
