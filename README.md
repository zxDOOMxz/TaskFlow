# TaskFlow

TaskFlow — единое рабочее пространство для команды, где задачи, проекты и документация живут вместе. MVP включает задачи, Kanban-доски, спринты, бэклог, вики-базу знаний и уведомления.

## Стек технологий

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend:** React 18, TypeScript, Vite, TailwindCSS, Zustand
- **База данных:** PostgreSQL 16 (локально или бесплатный Supabase PostgreSQL)
- **Файлы:** MinIO (S3-compatible)
- **Realtime:** WebSocket (FastAPI native) — доски и чаты
- **Формы/обратная связь:** Web3Forms
- **Контейнеризация:** Docker + docker-compose

## Структура проекта

```
01TaskFlow/
├── backend/          # FastAPI приложение
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── ...
│   ├── alembic/      # Миграции
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # React приложение
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   └── stores/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Быстрый старт

### Требования

- Docker Desktop или Docker Engine + docker-compose
- 4 GB RAM свободно

### Запуск всего стека

```bash
cd C:\Arhive\Project\01TaskFlow
docker-compose up --build
```

После успешного запуска:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- MinIO Console: http://localhost:9001 (login: `minioadmin` / `minioadmin`)

### Остановка

```bash
docker-compose down
```

Для удаления данных:

```bash
docker-compose down -v
```

## Локальная разработка без Docker

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
# Создай .env файл по примеру .env.example
cp .env.example .env
# Запусти PostgreSQL локально или через Docker
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Архитектура (гибридная)

```
Frontend (React + Supabase JS)
    ├── Supabase Auth — регистрация/вход/сессия
    ├── Supabase Storage — файлы (в разработке)
    ├── Supabase Realtime — чаты/live-обновления (в разработке)
    └── FastAPI Backend — сложная логика (mentions, notifications, поиск)
            └── Supabase PostgreSQL — данные
```

Авторизация происходит через **Supabase Auth**. Frontend получает JWT-токен и передаёт его в FastAPI-бэкенд в заголовке `Authorization: Bearer <token>`. Бэкенд верифицирует токен через Supabase JWKS.

## Интеграции

### Supabase Auth + PostgreSQL

1. Создай проект на [https://supabase.com](https://supabase.com).
2. В **Project Settings → API** скопируй:
   - Project URL
   - `anon` / `publishable` ключ (для фронтенда)
   - `service_role` / `secret` ключ (для бэкенда)
3. В **Authentication → URL Configuration** добавь:
   - Site URL: `http://localhost:5173`
   - Redirect URLs: `http://localhost:5173/**`
4. Заполни `.env` файлы (см. примеры ниже).

### Web3Forms

1. Получи access key на [https://web3forms.com](https://web3forms.com).
2. Добавь в `.env`:
   ```
   WEB3FORMS_ENABLED=true
   WEB3FORMS_ACCESS_KEY=your-access-key
   ```
3. Используй эндпоинт `POST /api/v1/contact` для отправки форм.

## Переменные окружения

### Backend (`backend/.env`)

```env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres?sslmode=require
SECRET_KEY=any-random-string

SUPABASE_ENABLED=true
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_SECRET_KEY=your-service-role-key
SUPABASE_PUBLISHABLE_KEY=your-anon-key
SUPABASE_JWKS_URL=https://YOUR_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=/api/v1
VITE_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Деплой на свой сервер (VPS)

### Подготовка сервера

1. Установи Docker и Docker Compose.
2. Склонируй репозиторий:
   ```bash
   git clone https://github.com/zxDOOMxz/TaskFlow.git /opt/taskflow
   cd /opt/taskflow
   ```
3. Создай файл `.env` по примеру `.env.example` и заполни свои значения Supabase.

### DNS-записи

Для домена `task-flow.work.gd` (или твоего домена) создай в панели регистратора/управления DNS:

| Тип | Имя | Значение | TTL |
|-----|-----|----------|-----|
| A | `@` | IP-адрес твоего сервера | 300/600 |
| A | `www` | IP-адрес твоего сервера | 300/600 |

Если используешь поддомен (например, `app.task-flow.work.gd`), создай A-запись для `app` вместо `@`.

### SSL-сертификат (Let's Encrypt)

Перед первым запуском получи SSL-сертификат:

```bash
cd /opt/taskflow
chmod +x init-ssl.sh
./init-ssl.sh
```

Скрипт использует Certbot в standalone-режиме (должен быть свободен порт 80).

### Запуск

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

После запуска:
- Сайт: `https://task-flow.work.gd`
- API: `https://task-flow.work.gd/api/v1/`
- WebSocket: `wss://task-flow.work.gd/ws/`

Бэкенд на порту `8000` больше не открыт наружу — все запросы идут через nginx.

### Автодеплой через GitHub Actions

1. В настройках репозитория (Settings → Secrets and variables → Actions):
   - **Secrets** → `DEPLOY_SSH_KEY`: приватный SSH-ключ сервера.
   - **Variables** → `DEPLOY_HOST`: IP или домен сервера.
   - **Variables** → `DEPLOY_USER`: имя пользователя на сервере (например, `root` или `ubuntu`).
   - **Variables** → `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
2. На сервере добавь публичный ключ в `~/.ssh/authorized_keys`.
3. При каждом пуше в `master` GitHub Actions соберёт образы и выполнит деплой.

### Альтернативные хостинги

- **Фронтенд**: Vercel, Netlify, GitHub Pages, Cloudflare Pages.
- **Бэкенд**: Render, Railway, Fly.io, любой VPS с Docker.

## Основные API эндпоинты

| Метод | Эндпоинт | Описание |
|-------|----------|----------|
| POST | `/api/v1/auth/register` | Регистрация |
| POST | `/api/v1/auth/login` | Вход |
| GET | `/api/v1/auth/me` | Текущий пользователь |
| GET | `/api/v1/workspaces` | Список workspace |
| POST | `/api/v1/workspaces` | Создать workspace |
| GET | `/api/v1/workspaces/{slug}/projects` | Проекты workspace |
| POST | `/api/v1/workspaces/{slug}/projects` | Создать проект |
| GET | `/api/v1/projects/{key}/issues` | Задачи проекта |
| POST | `/api/v1/projects/{key}/issues` | Создать задачу |
| GET | `/api/v1/projects/{key}/boards` | Доски проекта |
| GET | `/api/v1/projects/{key}/sprints` | Спринты проекта |
| GET | `/api/v1/workspaces/{slug}/wiki/pages` | Wiki-страницы |
| POST | `/api/v1/workspaces/{slug}/wiki/pages` | Создать страницу |
| GET | `/api/v1/workspaces/{slug}/chat/rooms` | Комнаты чата |
| POST | `/api/v1/workspaces/{slug}/chat/rooms` | Создать комнату |
| GET | `/api/v1/workspaces/{slug}/files` | Файлы |
| POST | `/api/v1/workspaces/{slug}/files/upload` | Загрузить файл |
| POST | `/api/v1/contact` | Отправить форму через Web3Forms |
| WS | `/ws/{room_id}?token=...` | WebSocket для чатов и live-обновлений |

## MVP-скоуп

### Этап 1 — Must Have (реализовано)
- Авторизация JWT + refresh tokens
- Workspaces и роли
- Проекты с ключами
- Задачи: Epic, Story, Task, Bug, Subtask
- Статусы: To Do, In Progress, Review, Done
- Приоритеты: Blocker, Critical, Major, Minor, Trivial
- Kanban-доски с drag-and-drop
- Бэклог и спринты
- Комментарии и логирование времени
- Связи между задачами
- Wiki с Markdown и упоминаниями
- Глобальный поиск
- Уведомления
- Чаты через WebSocket
- Загрузка файлов в MinIO
- Упоминания `@user`, `#task`, `[[page]]`
- Backend-тесты

### Этап 2 — Should Have
- Email-уведомления
- Интеграция с Supabase Auth / Storage
- Интеграция с внешними календарями

### Этап 3 — Nice to Have
- Видеозвонки (Jitsi)
- SSO
- Автоматизации

## Дальнейшие шаги

1. Подключить реальную Supabase PostgreSQL базу
2. Настроить Web3Forms access key для форм обратной связи
3. Добавить frontend-тесты
4. Настроить CI/CD (GitHub Actions)
5. Добавить email-уведомления

## Лицензия

MIT
