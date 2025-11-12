# Kortix Frontend

## Quick Setup

The easiest way to get your frontend configured is to use the setup wizard from the project root:

```bash
cd .. # Navigate to project root if you're in the frontend directory
python setup.py
```

This will configure all necessary environment variables automatically.

## Environment Configuration

The setup wizard automatically creates a `.env.local` file with the following configuration:

```sh
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
NEXT_PUBLIC_ENV_MODE=LOCAL
```

## Getting Started

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Build for production:

```bash
npm run build
```

Run the production server:

```bash
npm run start
```

## Development Notes

- The frontend connects to the backend API at `http://localhost:8000/api`
- Supabase is used for authentication and database operations
- The app runs on `http://localhost:3000` by default
- Environment variables are automatically configured by the setup wizard

## Подключение к удалённому бэкенду (без локального запуска)

Если вы используете удалённый сервер backend и не хотите запускать его локально, убедитесь, что фронтенд настроен на правильную базовую URL с суффиксом `/api`:

- В `frontend/.env.local` задайте:
  - `NEXT_PUBLIC_BACKEND_URL=https://<ваш-бэкенд-хост>/api`
  - Пример: `https://staging.suna.so/api`

Почему нужен суффикс `/api`:
- В бэкенде все роуты подключаются под префиксом `/api` (см. `backend/api.py`: `app.include_router(api_router, prefix="/api")`).
- Эндпоинты, которые вызывает фронтенд, должны быть вида:
  - `/api/llm/models`
  - `/api/agents`
  - `/api/agents/generate-icon`

Проверка доступности удалённого бэкенда (macOS):
- Проверить здоровье сервиса: `curl -I https://<ваш-бэкенд-хост>/api/health`
- Проверить список моделей: `curl -I https://<ваш-бэкенд-хост>/api/llm/models`

Настройки CORS на бэкенде:
- Убедитесь, что фронтенд-оригин добавлен в разрешённые источники.
- Можно задать в backend `.env`:
  - `FRONTEND_URL=https://<ваш-фронтенд-хост>`
  - `CORS_ALLOWED_ORIGINS=https://<ваш-фронтенд-хост>` (несколько значений через запятую)
- В локальном режиме бэкенд автоматически разрешает `http://localhost:3000`, но в удалённой среде нужно явно указать домен.

Типичные причины 404 и как исправить:
- Неверный `NEXT_PUBLIC_BACKEND_URL` без `/api` → добавьте `/api` в конец базового URL.
- Неправильный домен или протокол (http/https) → используйте точный публичный адрес удалённого бэкенда.
- CORS блокирует запросы → добавьте фронтенд-оригин в `CORS_ALLOWED_ORIGINS` или `FRONTEND_URL` на бэкенде.

Примечания по UI:
- Во вкладке General диалога конфигурации агента есть фильтры провайдеров и выбор модели. Эти элементы используют `/llm/models` через базовый `NEXT_PUBLIC_BACKEND_URL` и зависят от корректной конфигурации выше.
