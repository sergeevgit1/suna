# Анализ интеграции Daytona в проекте SUNA

## Текущая архитектура

### Компоненты Daytona

1. **backend/core/sandbox/sandbox.py**
   - Использует `AsyncDaytona` и `AsyncSandbox` из `daytona_sdk`
   - Конфигурация через environment variables:
     - `DAYTONA_API_KEY`
     - `DAYTONA_SERVER_URL`
     - `DAYTONA_TARGET`
   - Функции:
     - `get_or_start_sandbox()` - получение/запуск существующего sandbox
     - `create_sandbox()` - создание нового sandbox из snapshot
     - `delete_sandbox()` - удаление sandbox
     - `start_supervisord_session()` - запуск supervisord внутри sandbox

2. **backend/core/sandbox/tool_base.py**
   - Базовый класс `SandboxToolsBase` для всех инструментов
   - Управление жизненным циклом sandbox на уровне проекта
   - Хранение метаданных sandbox в таблице `projects`:
     ```json
     {
       "sandbox": {
         "id": "sandbox-id",
         "pass": "uuid",
         "vnc_preview": "https://...",
         "sandbox_url": "https://...",
         "token": "..."
       }
     }
     ```

3. **backend/core/sandbox/api.py**
   - API endpoints для работы с sandbox
   - Использует `AsyncSandbox` для операций

### Функциональность Daytona Sandbox

1. **Файловая система**
   - `sandbox.fs.list_files(path)` - список файлов
   - `sandbox.fs.download_file(path)` - скачивание файла
   - `sandbox.fs.upload_file(path, content)` - загрузка файла
   - `sandbox.fs.get_file_info(path)` - информация о файле

2. **Процессы**
   - `sandbox.process.create_session(session_id)` - создание сессии
   - `sandbox.process.execute_session_command(session_id, command)` - выполнение команды
   - Поддержка асинхронных команд

3. **Превью и доступ**
   - `sandbox.get_preview_link(port)` - получение публичной ссылки на порт
   - VNC доступ на порту 6080
   - Web preview на порту 8080
   - Chrome DevTools Protocol на порту 9222

4. **Управление состоянием**
   - `SandboxState.STARTED` - запущен
   - `SandboxState.STOPPED` - остановлен
   - `SandboxState.ARCHIVED` - архивирован
   - `SandboxState.ARCHIVING` - архивируется
   - Auto-stop через 15 минут
   - Auto-archive через 30 минут

5. **Snapshot**
   - Создание sandbox из snapshot
   - Snapshot содержит предустановленное окружение:
     - Python, Node.js
     - Chrome browser
     - Supervisord
     - VNC server
     - Workspace директория `/workspace`

## Зависимости от Daytona

### Критические зависимости
1. **Управление жизненным циклом** - создание, запуск, остановка, удаление
2. **Файловая система** - все операции с файлами через Daytona API
3. **Выполнение команд** - shell, Python, Node.js через Daytona sessions
4. **Публичный доступ** - preview links для VNC и web
5. **Изоляция** - каждый проект имеет свой изолированный sandbox

### Инструменты, использующие Daytona
- `sb_files_tool.py` - файловые операции
- `sb_upload_file_tool.py` - загрузка файлов
- `browser_tool.py` - управление браузером
- Все инструменты, наследующие `SandboxToolsBase`

## Проблемы с текущей интеграцией

1. **Vendor lock-in** - полная зависимость от Daytona API
2. **Стоимость** - Daytona может быть платным сервисом
3. **Производительность** - задержки при создании/запуске sandbox
4. **Ограничения** - auto-stop/archive могут прерывать работу
5. **Отладка** - сложно отлаживать проблемы внутри Daytona sandbox

## Требования к альтернативному решению

### Функциональные требования
1. **Изолированное окружение** - каждый проект в отдельном контейнере
2. **Файловая система** - API для работы с файлами
3. **Выполнение команд** - shell, Python, Node.js
4. **Публичный доступ** - HTTP endpoints для preview
5. **VNC доступ** - для визуального взаимодействия
6. **Chrome DevTools** - для автоматизации браузера
7. **Persistence** - сохранение состояния между сессиями
8. **Auto-cleanup** - автоматическое удаление неактивных sandbox

### Нефункциональные требования
1. **Open-source** - бесплатное решение
2. **Self-hosted** - развертывание на собственных серверах
3. **Масштабируемость** - поддержка множества одновременных sandbox
4. **Производительность** - быстрое создание/запуск
5. **Надежность** - восстановление после сбоев
6. **Безопасность** - изоляция между sandbox
7. **Простота интеграции** - минимальные изменения в коде

## Интерфейс для замены

Для минимизации изменений в коде, альтернативное решение должно предоставить:

```python
class AsyncSandbox:
    # Файловая система
    fs: FileSystemAPI
    
    # Процессы
    process: ProcessAPI
    
    # Состояние
    state: SandboxState
    id: str
    
    # Методы
    async def get_preview_link(port: int) -> PreviewLink
```

```python
class FileSystemAPI:
    async def list_files(path: str) -> List[FileInfo]
    async def download_file(path: str) -> bytes
    async def upload_file(path: str, content: bytes)
    async def get_file_info(path: str) -> FileInfo
```

```python
class ProcessAPI:
    async def create_session(session_id: str)
    async def execute_session_command(session_id: str, request: SessionExecuteRequest)
```

## Следующие шаги

1. Исследовать open-source альтернативы для замены Daytona
2. Выбрать наиболее подходящее решение
3. Разработать план миграции
4. Реализовать адаптер для совместимости с текущим API
5. Постепенная миграция инструментов
