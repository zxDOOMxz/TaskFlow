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

### Бесплатный хостинг без сервера (Vercel + Render)

Если у тебя нет VPS, можно развернуть всё бесплатно:

#### 1. Бэкенд на Render

1. Зарегистрируйся на https://render.com (через GitHub).
2. New → Blueprint → выбери репозиторий `zxDOOMxz/TaskFlow`.
3. Render найдёт `render.yaml` и создаст сервис `taskflow-api`.
4. В настройках сервиса добавь переменные окружения:
   - `DATABASE_URL` — строка подключения Supabase PostgreSQL.
   - `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_JWKS_URL`.
   - `CORS_ORIGINS` — `https://task-flow.work.gd,https://www.task-flow.work.gd`.
5. Деплой произойдёт автоматически. Запомни URL бэкенда, например `https://taskflow-api.onrender.com`.

#### 2. Фронтенд на Vercel

1. Зарегистрируйся на https://vercel.com (через GitHub).
2. Add New Project → импортируй `zxDOOMxz/TaskFlow`.
3. Root Directory: `frontend`.
4. Environment Variables:
   - `VITE_API_URL=/api/v1`
   - `VITE_WS_HOST=taskflow-api.onrender.com` (твой URL Render)
   - `VITE_SUPABASE_URL` и `VITE_SUPABASE_ANON_KEY`.
5. В `frontend/vercel.json` замени `taskflow-api.onrender.com` на реальный URL бэкенда.
6. Деплой.

#### 3. Подключение домена

1. В Vercel → Project Settings → Domains → добавь `task-flow.work.gd`.
2. Vercel покажет DNS-записи (обычно A-запись или CNAME).
3. Добавь эти записи в панели freedomain.one.
4. Жди обновления DNS (до 24 часов, обычно быстрее).

> Бесплатный Render «засыпает» при неактивности (~15 мин), поэтому первый запрос после паузы может занять 30–60 секунд.

### Деплой фронтенда на Timeweb (shared-хостинг)

Если Netlify/Vercel не отдаёт статические файлы в вашем регионе, фронтенд можно разместить на Timeweb, оставив бэкенд на Render и базу на Supabase.

#### 1. Сборка

В папке `frontend` выполните:

```powershell
$env:VITE_SUPABASE_URL="https://emsmevtccyvujrtwnlym.supabase.co"
$env:VITE_SUPABASE_ANON_KEY="sb_publishable_Rx5b3syJj3gOpvOt3IthlQ_ffA38Kq2"
$env:VITE_API_URL="https://taskflow-zcib.onrender.com"
npm run build
```

После сборки в `frontend/dist/` будут файлы:
- `index.html`
- `.htaccess`

#### 2. Загрузка на Timeweb

1. В панели Timeweb откройте **Файлы** или **Файловый менеджер**.
2. Перейдите в корень сайта (обычно `public_html` или папка домена).
3. Удалите стандартные `index.html`, `index.php` и т.п.
4. Загрузите `index.html` и `.htaccess` из `frontend/dist/`.

`.htaccess` настроит Apache так, чтобы SPA-роутинг работал при прямом переходе по ссылкам (`/w/...`, `/projects/...`).

#### 3. DNS

В панели управления доменом (Selectel) измените A-записи:

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `@` | `92.53.96.201` |
| A | `www` | `92.53.96.201` |

Если NS-записи сейчас указывают на Netlify (`dns*.p03.nsone.net`), верните их на NS сервера регистратора/Selectel, иначе DNS не будет управляться из панели Selectel.

#### 4. CORS

После смены домена обновите `CORS_ORIGINS` в Render (см. раздел ниже).

### Альтернативные хостинги

- **Фронтенд**: Vercel, Netlify, GitHub Pages, Cloudflare Pages, Timeweb.
- **Бэкенд**: Render, Railway, Fly.io, Koyeb.

## Обновление CORS в Render

После смены домена фронтенда обнови `CORS_ORIGINS` в настройках бэкенда на Render:

1. Открой [dashboard.render.com](https://dashboard.render.com) → выбери сервис `TaskFlow`.
2. Слева нажми **Environment**.
3. Найди переменную `CORS_ORIGINS`.
4. Измени значение на новый домен (домены разделяй запятыми, без пробелов):
   ```
   https://itaskflow.ru,https://www.itaskflow.ru
   ```
5. Нажми **Save Changes**.
6. Перейди в **Deploys** и нажми **Manual Deploy → Deploy latest commit**.

Без этого браузер будет блокировать запросы с нового домена к бэкенду.

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
