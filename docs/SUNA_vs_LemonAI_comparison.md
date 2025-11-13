# Детальное сравнение SUNA и LemonAI

**Дата:** 13 ноября 2025  
**Статус:** Полный анализ архитектуры и функциональности

---

## Краткое резюме

**SUNA** и **LemonAI** - оба проекта для AI агентов с похожей функциональностью, но **существенно отличаются** по архитектуре, стеку технологий и подходу к реализации.

### Ключевые различия

| Аспект | SUNA | LemonAI |
|--------|------|---------|
| **Backend язык** | Python (FastAPI) | Node.js (Koa) |
| **Frontend фреймворк** | Next.js (React) | Vue 3 + Ant Design |
| **База данных** | Supabase (PostgreSQL) | MySQL + Sequelize |
| **Sandbox** | Daytona SDK | Custom Docker Runtime |
| **Agent архитектура** | AgentPress (custom) | AgenticAgent (code-act) |
| **Стадия** | Production-ready | Development (v0.4.0) |
| **Сложность** | Высокая (enterprise) | Средняя (startup) |

---

## 1. Архитектура Backend

### SUNA Backend (Python + FastAPI)

**Стек:**
- **Framework:** FastAPI 0.115.12
- **ASGI Server:** Uvicorn 0.27.1
- **Database:** Prisma ORM + Supabase
- **Cache:** Redis + Upstash Redis
- **Queue:** Dramatiq
- **Monitoring:** Prometheus, Sentry, Langfuse
- **AI:** LiteLLM (multi-provider), OpenAI SDK

**Структура:**
```
backend/
├── api.py                    # Main FastAPI app
├── core/
│   ├── agentpress/           # Agent engine (124KB response_processor.py!)
│   │   ├── context_manager.py
│   │   ├── response_processor.py
│   │   ├── thread_manager.py
│   │   ├── tool_registry.py
│   │   └── xml_tool_parser.py
│   ├── sandbox/              # Daytona integration
│   │   ├── sandbox.py
│   │   └── tool_base.py
│   ├── tools/                # 28 tools
│   │   ├── browser_tool.py
│   │   ├── sb_files_tool.py
│   │   ├── sb_shell_tool.py
│   │   └── ...
│   ├── billing/              # Stripe integration
│   ├── mcp_module/           # MCP support
│   ├── composio_integration/ # Composio tools
│   └── triggers/             # Scheduled tasks
└── supabase/                 # Database migrations
```

**Особенности:**
- ✅ **Enterprise-grade** - production-ready с мониторингом
- ✅ **Модульная архитектура** - четкое разделение на модули
- ✅ **Async everywhere** - полностью асинхронный код
- ✅ **Type hints** - строгая типизация
- ❌ **Сложность** - высокий порог входа
- ❌ **Зависимость от Daytona** - vendor lock-in

### LemonAI Backend (Node.js + Koa)

**Стек:**
- **Framework:** Koa 2.7.0
- **Database:** Sequelize + MySQL2 / SQLite3
- **Docker:** Dockerode (custom runtime)
- **AI:** Axios для API вызовов
- **Testing:** Mocha + Chai + Sinon

**Структура:**
```
src/
├── app.js                    # Main Koa app
├── agent/
│   ├── AgenticAgent.js       # Main agent class
│   ├── TaskManager.js        # Task management
│   ├── code-act/             # Code execution agent
│   ├── planning/             # Planning module
│   ├── memory/               # Memory management
│   └── tools/                # Tool definitions
├── runtime/
│   ├── DockerRuntime.js      # Remote Docker
│   ├── DockerRuntime.local.js # Local Docker (RECOMMENDED)
│   ├── LocalRuntime.js       # No Docker
│   └── utils/
│       └── tools.js          # write_code, etc.
├── routers/                  # API routes
│   ├── agent/
│   ├── conversation/
│   ├── file/
│   └── ...
└── mcp/                      # MCP support
```

**Особенности:**
- ✅ **Простота** - легко понять и модифицировать
- ✅ **Гибкость** - 3 runtime режима (local, docker, local-docker)
- ✅ **Self-contained** - custom Docker runtime без внешних зависимостей
- ✅ **Быстрый старт** - легко запустить локально
- ❌ **Меньше функций** - нет billing, triggers, composio
- ❌ **Менее production-ready** - v0.4.0, development stage

---

## 2. Sandbox / Runtime

### SUNA: Daytona SDK

**Файлы:**
- `backend/core/sandbox/sandbox.py` (5KB)
- `backend/core/sandbox/tool_base.py` (6.5KB)

**Подход:**
```python
from daytona_sdk import Daytona

client = Daytona(api_key="...")
workspace = client.create_workspace()
result = workspace.execute_command("ls -la")
```

**Характеристики:**
- ✅ **Managed service** - не нужно управлять Docker
- ✅ **Безопасность** - изолированные workspace
- ✅ **Масштабируемость** - автоматическое масштабирование
- ❌ **Стоимость** - платный сервис
- ❌ **Vendor lock-in** - зависимость от Daytona
- ❌ **Ограниченная кастомизация**

### LemonAI: Custom Docker Runtime

**Файлы:**
- `src/runtime/DockerRuntime.local.js` (13KB) ⭐ **РЕКОМЕНДУЕТСЯ**
- `src/runtime/DockerRuntime.js` (10KB)
- `src/runtime/LocalRuntime.js` (5KB)

**Подход:**
```javascript
const Docker = require('dockerode');
const docker = new Docker({socketPath: '/var/run/docker.sock'});

// Create container
const container = await docker.createContainer({
  Image: 'hexdolemonai/lemon-runtime-sandbox:latest',
  name: 'lemon-runtime-sandbox',
  Cmd: ['node', 'action_execution_server.js', '--port', '30000'],
  HostConfig: {
    Binds: [`${workspace_dir}:/workspace:rw`],
    PortBindings: {'30000/tcp': [{HostPort: '30000'}]}
  }
});

await container.start();
```

**Характеристики:**
- ✅ **Бесплатно** - только стоимость Docker
- ✅ **Полный контроль** - можно кастомизировать image
- ✅ **Гибкость** - 3 режима (local, docker, local-docker)
- ✅ **Port management** - автоматическое выделение портов
- ✅ **VSCode integration** - встроенный VSCode server
- ❌ **Требует Docker** - нужно настраивать Docker
- ❌ **Ручное управление** - нужно управлять контейнерами

**Ключевые фичи LemonAI Runtime:**

1. **Автоматическое выделение портов:**
   ```javascript
   EXECUTION_SERVER_PORT_RANGE = [30000, 39999]
   VSCODE_PORT_RANGE = [40000, 49999]
   APP_PORT_RANGE_1 = [50000, 54999]
   APP_PORT_RANGE_2 = [55000, 59999]
   ```

2. **Переиспользование контейнера:**
   ```javascript
   // Проверка существующего контейнера
   container = docker.getContainer('lemon-runtime-sandbox')
   if (container_info.State.Status === 'exited') {
     await container.start();
   }
   ```

3. **Workspace mounting:**
   ```javascript
   Binds: [`${workspace_dir}:/workspace:rw`]
   ```

---

## 3. Agent Architecture

### SUNA: AgentPress

**Файлы:**
- `response_processor.py` (124KB!) - монолитный процессор
- `context_manager.py` (48KB)
- `thread_manager.py` (38KB)
- `tool_registry.py` (4KB)

**Подход:**
- **Streaming-first** - все через SSE streaming
- **XML tool calls** - custom XML парсинг
- **Native tool calls** - OpenAI function calling
- **Context caching** - prompt caching для экономии
- **Thread-based** - каждый conversation = thread

**Особенности:**
- ✅ **Production-ready** - обработка всех edge cases
- ✅ **Streaming** - real-time updates
- ✅ **Error handling** - детальная обработка ошибок
- ✅ **Caching** - оптимизация стоимости
- ❌ **Сложность** - 124KB в одном файле!
- ❌ **Монолитность** - сложно модифицировать

### LemonAI: AgenticAgent

**Файлы:**
- `AgenticAgent.js` (12KB)
- `TaskManager.js` (8KB)
- `code-act/code-act.js`
- `planning/index.js`

**Подход:**
- **Task-based** - разбиение на задачи
- **Code-act pattern** - генерация и выполнение кода
- **Planning phase** - предварительное планирование
- **Memory management** - сохранение контекста
- **File versioning** - версионирование файлов

**Workflow:**
```javascript
async run() {
  await this._initialSetupAndAutoReply();  // Auto-reply
  await this._performPlanning();            // Planning
  await this._executeTasks();               // Execute tasks
  return await this._generateFinalOutput(); // Summary
}
```

**Особенности:**
- ✅ **Простота** - понятная структура
- ✅ **Модульность** - четкое разделение фаз
- ✅ **Гибкость** - легко добавлять новые фазы
- ✅ **Planning** - предварительное планирование задач
- ❌ **Меньше функций** - нет streaming, caching
- ❌ **Development stage** - не все edge cases обработаны

---

## 4. Tools / Функциональность

### SUNA Tools (28 tools)

**Категории:**

1. **Sandbox tools:**
   - `sb_files_tool.py` - file operations
   - `sb_shell_tool.py` - shell commands
   - `sb_python_tool.py` - Python execution
   - `sb_designer_tool.py` - UI design
   - `sb_docs_tool.py` - document processing

2. **Search tools:**
   - `image_search_tool.py` - Exa image search
   - `paper_search_tool.py` - academic papers
   - `company_search_tool.py` - company info
   - `people_search_tool.py` - people search

3. **Integration tools:**
   - `browser_tool.py` - web automation
   - `mcp_tool_wrapper.py` - MCP tools
   - `composio_integration/` - 100+ tools via Composio

4. **Special tools:**
   - `agent_creation_tool.py` - create sub-agents
   - `message_tool.py` - messaging
   - `presentation_tool.py` - create presentations

**Особенности:**
- ✅ **Много tools** - 28+ встроенных
- ✅ **Composio integration** - 100+ дополнительных
- ✅ **MCP support** - расширяемость
- ✅ **Production-ready** - хорошо протестированы

### LemonAI Tools

**Подход:**
- **Minimal built-in tools** - только базовые
- **Runtime-based** - tools через runtime
- **MCP support** - расширение через MCP
- **Code-act pattern** - генерация кода вместо tools

**Базовые tools:**
```javascript
// src/runtime/utils/tools.js
const write_code = async (action, uuid, user_id) => {
  let { path: filepath, content } = action.params;
  filepath = await restrictFilepath(filepath, user_id);
  await write_file(filepath, content);
  return {status: 'success', content: `File ${filepath} written`};
}
```

**Особенности:**
- ✅ **Простота** - минимум встроенных tools
- ✅ **Гибкость** - легко добавлять новые
- ✅ **MCP support** - расширяемость
- ❌ **Меньше функций** - нужно добавлять самому

---

## 5. Frontend

### SUNA Frontend (Next.js + React)

**Стек:**
- **Framework:** Next.js 15.3.1
- **UI Library:** Radix UI + shadcn/ui
- **State:** Zustand stores
- **Forms:** React Hook Form + Zod
- **Styling:** Tailwind CSS
- **Icons:** Radix Icons + Simple Icons
- **Rich features:** CodeMirror, DnD Kit, Emoji Mart

**Структура:**
```
frontend/
├── src/
│   ├── app/                  # Next.js app router
│   │   ├── (dashboard)/
│   │   │   ├── agents/
│   │   │   ├── threads/
│   │   │   └── settings/
│   │   └── (auth)/
│   ├── components/           # React components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── agents/
│   │   ├── threads/
│   │   └── ...
│   ├── hooks/               # Custom hooks
│   │   ├── threads/
│   │   ├── agents/
│   │   └── ...
│   ├── lib/                 # Utilities
│   │   ├── api/
│   │   └── utils/
│   └── stores/              # Zustand stores
└── public/
```

**Особенности:**
- ✅ **Modern stack** - Next.js 15, React 19
- ✅ **Type-safe** - TypeScript everywhere
- ✅ **Beautiful UI** - shadcn/ui components
- ✅ **SSR/SSG** - Next.js optimization
- ✅ **Mobile app** - React Native в apps/mobile/
- ❌ **Сложность** - высокий порог входа

### LemonAI Frontend (Vue 3)

**Стек:**
- **Framework:** Vue 3 + Vite
- **UI Library:** Ant Design Vue 4.2.6
- **State:** Pinia
- **Editor:** CodeMirror
- **Terminal:** xterm.js
- **Office:** @vue-office (docx, excel, pdf, pptx)

**Структура:**
```
frontend/
├── src/
│   ├── view/                 # Vue pages
│   │   ├── conversation/
│   │   ├── agent/
│   │   └── ...
│   ├── components/           # Vue components
│   ├── router/               # Vue Router
│   ├── store/                # Pinia stores
│   ├── services/             # API services
│   └── utils/
└── public/
```

**Особенности:**
- ✅ **Простота** - Vue 3 проще React
- ✅ **Ant Design** - готовые компоненты
- ✅ **Office support** - встроенный просмотр документов
- ✅ **Terminal** - встроенный xterm.js
- ❌ **Меньше функций** - базовый UI
- ❌ **Нет mobile app**

---

## 6. Database & Storage

### SUNA

**Database:**
- **Primary:** Supabase (PostgreSQL)
- **ORM:** Prisma
- **Migrations:** Supabase migrations
- **Auth:** Supabase Auth
- **Storage:** Supabase Storage

**Schema:**
- `agents` - agent configurations
- `threads` - conversation threads
- `messages` - chat messages
- `users` - user accounts
- `billing` - subscription data
- `triggers` - scheduled tasks

**Особенности:**
- ✅ **Managed** - Supabase handles everything
- ✅ **Auth** - built-in authentication
- ✅ **Storage** - file storage included
- ✅ **Real-time** - real-time subscriptions
- ❌ **Vendor lock-in** - зависимость от Supabase

### LemonAI

**Database:**
- **Primary:** MySQL2 / SQLite3
- **ORM:** Sequelize
- **Migrations:** Sequelize migrations

**Models:**
- `Conversation` - conversations
- `Message` - messages
- `File` - file metadata
- `User` - users
- `Agent` - agent configs

**Особенности:**
- ✅ **Гибкость** - MySQL или SQLite
- ✅ **Self-hosted** - полный контроль
- ✅ **Простота** - Sequelize ORM
- ❌ **Ручное управление** - нужно настраивать
- ❌ **Нет auth** - нужно добавлять самому

---

## 7. Deployment & DevOps

### SUNA

**Production:**
- **Backend:** Gunicorn + Uvicorn workers
- **Frontend:** Next.js (Vercel или self-hosted)
- **Queue:** Dramatiq + Redis
- **Monitoring:** Prometheus + Sentry + Langfuse
- **Logs:** Structlog

**Docker:**
- Нет официального Dockerfile
- Требует Daytona для sandbox

**Особенности:**
- ✅ **Production-ready** - мониторинг, логи, метрики
- ✅ **Scalable** - queue workers, Redis cache
- ✅ **Observability** - Prometheus, Sentry, Langfuse
- ❌ **Сложность** - много компонентов

### LemonAI

**Production:**
- **Backend:** PM2 или Node.js
- **Frontend:** Vite build
- **Docker:** docker-compose.yml included
- **Electron:** Desktop app support

**Docker:**
```yaml
services:
  lemon-runtime-sandbox:
    image: hexdolemonai/lemon-runtime-sandbox:latest
    volumes:
      - ./workspace:/workspace
    ports:
      - "30000-39999:30000-39999"
```

**Особенности:**
- ✅ **Docker-compose** - легко запустить
- ✅ **Electron** - desktop app
- ✅ **Простота** - минимум зависимостей
- ❌ **Базовый мониторинг** - нет Prometheus
- ❌ **Development stage** - не production-ready

---

## 8. Ключевые различия в подходе

### Философия

| Аспект | SUNA | LemonAI |
|--------|------|---------|
| **Целевая аудитория** | Enterprise, SaaS | Developers, Self-hosted |
| **Приоритет** | Stability, Features | Simplicity, Flexibility |
| **Стадия** | Production | Development |
| **Monetization** | Billing, Subscriptions | Open-source |
| **Complexity** | High | Medium |

### Архитектурные решения

**SUNA:**
- **Managed services** - Daytona, Supabase
- **Vendor lock-in** - зависимость от сервисов
- **Enterprise features** - billing, monitoring, triggers
- **Monolithic agent** - большой response_processor.py
- **Type-safe** - Python type hints, TypeScript

**LemonAI:**
- **Self-hosted** - custom Docker runtime
- **Independence** - минимум внешних зависимостей
- **Modular agent** - четкое разделение фаз
- **Code-act pattern** - генерация кода вместо tools
- **Simplicity** - легко понять и модифицировать

---

## 9. Что можно взять из LemonAI для SUNA

### 1. Custom Docker Runtime ⭐ **ГЛАВНОЕ**

**Проблема в SUNA:**
- Зависимость от платного Daytona
- Нет контроля над sandbox окружением
- Vendor lock-in

**Решение из LemonAI:**
```javascript
// DockerRuntime.local.js - 13KB самодостаточного кода
class DockerRuntime {
  async connect_container() {
    // Переиспользование существующего контейнера
    let container = docker.getContainer('lemon-runtime-sandbox')
    if (container_info.State.Status === 'exited') {
      await container.start();
    }
  }
  
  async init_container() {
    // Автоматическое выделение портов
    const host_port = await this.find_available_port([30000, 39999]);
    
    // Создание контейнера с workspace mounting
    const container = await docker.createContainer({
      Image: 'hexdolemonai/lemon-runtime-sandbox:latest',
      HostConfig: {
        Binds: [`${workspace_dir}:/workspace:rw`],
        PortBindings: {[`${host_port}/tcp`]: [{HostPort: `${host_port}`}]}
      }
    });
  }
}
```

**Адаптация для SUNA:**
- Создать `backend/core/sandbox/docker_runtime.py`
- Использовать `docker-py` вместо `dockerode`
- Сохранить совместимость с существующим API
- Добавить в `sandboxai_adapter.py` (уже создан!)

**Преимущества:**
- ✅ Бесплатно
- ✅ Полный контроль
- ✅ Нет vendor lock-in
- ✅ Легко кастомизировать

### 2. Task-based Planning

**Проблема в SUNA:**
- Монолитный response processor (124KB)
- Сложно добавлять новые фазы
- Нет явного планирования

**Решение из LemonAI:**
```javascript
class AgenticAgent {
  async run() {
    await this._initialSetupAndAutoReply();  // 1. Auto-reply
    await this._performPlanning();            // 2. Planning
    await this._executeTasks();               // 3. Execute
    return await this._generateFinalOutput(); // 4. Summary
  }
}

class TaskManager {
  addTask(description, dependencies) {
    this.tasks.push({id, description, status: 'pending', dependencies});
  }
  
  getNextTask() {
    return this.tasks.find(t => 
      t.status === 'pending' && 
      t.dependencies.every(d => this.isCompleted(d))
    );
  }
}
```

**Адаптация для SUNA:**
- Разбить `response_processor.py` на фазы
- Добавить `TaskManager` класс
- Добавить planning phase перед execution

**Преимущества:**
- ✅ Модульность
- ✅ Понятная структура
- ✅ Легко добавлять фазы
- ✅ Лучший UX (показывать план)

### 3. File Versioning

**Проблема в SUNA:**
- Нет версионирования файлов
- Сложно откатить изменения
- Нет истории изменений

**Решение из LemonAI:**
```javascript
// utils/versionManager.js
async function createFilesVersion(conversation_id, files, extension, state) {
  const version = {
    conversation_id,
    files: files.map(f => ({
      path: f.path,
      content: f.content,
      hash: md5(f.content)
    })),
    timestamp: Date.now()
  };
  
  await saveVersion(version);
  return version;
}
```

**Адаптация для SUNA:**
- Добавить `file_versions` таблицу в Supabase
- Сохранять версию после каждого изменения
- Добавить UI для просмотра истории

**Преимущества:**
- ✅ История изменений
- ✅ Откат изменений
- ✅ Сравнение версий

### 4. Multiple Runtime Modes

**Проблема в SUNA:**
- Только Daytona
- Нельзя запустить локально без Daytona
- Нет fallback опций

**Решение из LemonAI:**
```javascript
const RUNTIME_TYPE = process.env.RUNTIME_TYPE || 'local-docker';
const runtimeMap = {
  'local': LocalRuntime,           // No Docker, direct execution
  'docker': DockerRuntime,         // Remote Docker
  'local-docker': LocalDockerRuntime // Local Docker (recommended)
}

const RunTime = runtimeMap[RUNTIME_TYPE];
this.runtime = new RunTime(context);
```

**Адаптация для SUNA:**
```python
SANDBOX_BACKEND = os.getenv('SANDBOX_BACKEND', 'sandboxai')

def get_sandbox_client(workspace_id: str):
    if SANDBOX_BACKEND == 'sandboxai':
        from .sandboxai_adapter import SandboxAIClient
        return SandboxAIClient(workspace_id)
    elif SANDBOX_BACKEND == 'daytona':
        from .sandbox import DaytonaClient
        return DaytonaClient(workspace_id)
    elif SANDBOX_BACKEND == 'local':
        from .local_runtime import LocalRuntime
        return LocalRuntime(workspace_id)
```

**Преимущества:**
- ✅ Гибкость
- ✅ Легко тестировать локально
- ✅ Fallback опции

### 5. Simplified Tool System

**Проблема в SUNA:**
- 28 встроенных tools
- Сложная регистрация
- Много boilerplate кода

**Решение из LemonAI:**
```javascript
// Минимальный tool
const write_code = async (action, uuid, user_id) => {
  let { path: filepath, content } = action.params;
  await write_file(filepath, content);
  return {
    status: 'success',
    content: `File ${filepath} written successfully.`
  };
}

// Регистрация через MCP
const tools = await mcp_client.listTools();
```

**Адаптация для SUNA:**
- Упростить базовые tools
- Больше полагаться на MCP
- Меньше встроенных tools

**Преимущества:**
- ✅ Простота
- ✅ Меньше кода
- ✅ Легче поддерживать

### 6. Port Management

**Проблема в SUNA:**
- Нет автоматического выделения портов
- Конфликты портов при multiple sandboxes

**Решение из LemonAI:**
```javascript
const EXECUTION_SERVER_PORT_RANGE = [30000, 39999]
const VSCODE_PORT_RANGE = [40000, 49999]
const APP_PORT_RANGE_1 = [50000, 54999]

async find_available_port(port_range) {
  for (let port = port_range[0]; port <= port_range[1]; port++) {
    if (await isPortAvailable(port)) return port;
  }
  throw new Error('No available ports');
}
```

**Адаптация для SUNA:**
- Добавить port manager
- Выделять порты автоматически
- Освобождать порты при завершении

**Преимущества:**
- ✅ Нет конфликтов
- ✅ Автоматическое управление
- ✅ Масштабируемость

### 7. Conversation Directory Structure

**Проблема в SUNA:**
- Файлы разбросаны
- Сложно найти файлы conversation

**Решение из LemonAI:**
```javascript
async _getConversationDirPath() {
  const dir_name = 'Conversation_' + this.context.conversation_id.slice(0, 6);
  const WORKSPACE_DIR = getDirpath('workspace', this.context.user_id);
  return path.join(WORKSPACE_DIR, dir_name);
}

// Структура:
// workspace/
//   user_123/
//     Conversation_abc123/
//       index.html
//       style.css
//       script.js
```

**Адаптация для SUNA:**
- Создавать отдельную папку для каждого thread
- Сохранять все файлы в одном месте
- Легко архивировать/экспортировать

**Преимущества:**
- ✅ Организация
- ✅ Легко найти файлы
- ✅ Легко экспортировать

---

## 10. Рекомендации по улучшению SUNA

### Приоритет 1: Замена Daytona на SandboxAI ⭐⭐⭐⭐⭐

**Что делать:**
1. Использовать готовый `sandboxai_adapter.py` (уже создан)
2. Добавить environment variable `SANDBOX_BACKEND`
3. Создать factory для выбора sandbox backend
4. Постепенная миграция с A/B тестированием

**Почему:**
- Бесплатно
- Полный контроль
- Нет vendor lock-in
- Легко кастомизировать

**Время:** 2-3 недели

### Приоритет 2: Рефакторинг response_processor.py ⭐⭐⭐⭐

**Что делать:**
1. Разбить 124KB файл на модули
2. Добавить TaskManager
3. Добавить planning phase
4. Четкое разделение на фазы

**Почему:**
- Легче поддерживать
- Легче добавлять функции
- Лучший UX

**Время:** 2-3 недели

### Приоритет 3: File Versioning ⭐⭐⭐

**Что делать:**
1. Добавить `file_versions` таблицу
2. Сохранять версии автоматически
3. Добавить UI для истории

**Почему:**
- История изменений
- Откат изменений
- Лучший UX

**Время:** 1 неделя

### Приоритет 4: Multiple Runtime Modes ⭐⭐⭐

**Что делать:**
1. Добавить LocalRuntime
2. Добавить environment variable
3. Добавить fallback логику

**Почему:**
- Легко тестировать
- Гибкость
- Fallback опции

**Время:** 1 неделя

### Приоритет 5: Conversation Directory Structure ⭐⭐

**Что делать:**
1. Создавать папку для каждого thread
2. Сохранять все файлы в одном месте
3. Добавить export функцию

**Почему:**
- Организация
- Легко экспортировать

**Время:** 3-5 дней

---

## 11. Заключение

### Что лучше в SUNA

✅ **Production-ready** - готово к production  
✅ **Enterprise features** - billing, monitoring, triggers  
✅ **Rich functionality** - 28+ tools, Composio, MCP  
✅ **Modern stack** - Next.js 15, FastAPI, TypeScript  
✅ **Mobile app** - React Native app included  
✅ **Observability** - Prometheus, Sentry, Langfuse  

### Что лучше в LemonAI

✅ **Simplicity** - легко понять и модифицировать  
✅ **Self-hosted** - полный контроль, бесплатно  
✅ **Custom Docker** - нет vendor lock-in  
✅ **Modular agent** - четкое разделение фаз  
✅ **Task planning** - предварительное планирование  
✅ **File versioning** - история изменений  

### Главные выводы

1. **SUNA** - enterprise-grade решение с множеством функций, но **зависимое от платных сервисов** (Daytona, Supabase)

2. **LemonAI** - simple и гибкое решение с **custom Docker runtime**, но **меньше функций** и в development стадии

3. **Лучшая стратегия для SUNA:**
   - Взять **custom Docker runtime** из LemonAI
   - Сохранить **enterprise features** SUNA
   - Добавить **task planning** из LemonAI
   - Рефакторить **response_processor.py**
   - Добавить **file versioning**

4. **Результат:**
   - ✅ Бесплатный sandbox (SandboxAI)
   - ✅ Полный контроль
   - ✅ Enterprise features
   - ✅ Лучшая архитектура
   - ✅ Легче поддерживать

---

## 12. Следующие шаги

### Немедленно

1. **Внедрить SandboxAI** (используя готовый адаптер)
2. **Протестировать** на dev окружении
3. **A/B тестирование** на production

### В течение месяца

1. **Рефакторинг** response_processor.py
2. **Добавить** TaskManager и planning
3. **Добавить** file versioning

### В течение квартала

1. **Полная миграция** на SandboxAI
2. **Удалить** Daytona зависимость
3. **Оптимизировать** архитектуру

---

**Готово! Детальное сравнение завершено. 🎉**
