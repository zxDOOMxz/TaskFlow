-- TaskFlow Supabase schema (гибридная версия)
--
-- В гибридной архитектуре основные таблицы приложения (workspaces, projects,
-- issues, wiki и т.д.) создаются через SQLAlchemy/Alembic в бэкенде.
-- Этот файл содержит вспомогательные объекты Supabase:
--   - расширение профилей пользователей (profiles)
--   - RLS-политики для прямого доступа фронтенда к профилям
--   - триггер для автосоздания профиля при регистрации
--
-- Как применить:
--   Supabase Dashboard → SQL Editor → New query → вставить этот файл → Run

-- ============================================================
-- 1. Profiles: публичные/внутренние данные пользователя
-- ============================================================
create table if not exists public.profiles (
  id uuid primary key references auth.users on delete cascade,
  email text not null,
  first_name text,
  last_name text,
  avatar_url text,
  timezone text default 'UTC',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

comment on table public.profiles is 'Расширение профиля для Supabase Auth users';

-- Обновление updated_at
 create or replace function public.set_updated_at()
 returns trigger as $$
 begin
   new.updated_at = now();
   return new;
 end;
 $$ language plpgsql security definer;

 drop trigger if exists profiles_updated_at on public.profiles;
 create trigger profiles_updated_at
   before update on public.profiles
   for each row execute function public.set_updated_at();

-- ============================================================
-- 2. RLS для profiles
-- ============================================================
alter table public.profiles enable row level security;

-- Пользователь видит свой профиль
create policy if not exists "Users can read own profile"
  on public.profiles for select
  using (auth.uid() = id);

-- Пользователь обновляет свой профиль
create policy if not exists "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

-- ============================================================
-- 3. Автосоздание профиля при регистрации
-- ============================================================
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email, first_name, last_name)
  values (
    new.id,
    new.email,
    new.raw_user_meta_data->>'first_name',
    new.raw_user_meta_data->>'last_name'
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============================================================
-- 4. Примечания по полной миграции на Supabase
-- ============================================================
-- Если в будущем вы решите полностью отказаться от FastAPI-бэкенда
-- и ходить в БД напрямую из фронтенда, сюда нужно добавить таблицы:
--   workspaces, workspace_members, projects, project_members,
--   issue_types, issue_statuses, issue_priorities, issues,
--   issue_comments, issue_time_logs, issue_links, sprints,
--   boards, board_columns, board_column_issues,
--   wiki_pages, wiki_page_versions, files, chat_rooms, chat_messages.
--
-- Для каждой таблицы необходимо настроить RLS-политики в соответствии
-- с бизнес-правилами TaskFlow.
