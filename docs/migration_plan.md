# План миграции с Daytona на альтернативное Sandbox решение

## Выбор решения: E2B

После анализа всех альтернатив, **E2B** является оптимальным выбором для замены Daytona в проекте SUNA по следующим причинам:

1. **Минимальные изменения кода** - E2B имеет похожий API на Daytona
2. **BYOC опция** - можно развернуть в собственной инфраструктуре
3. **Активная разработка** - 9.9K stars, регулярные обновления
4. **Enterprise support** - профессиональная поддержка
5. **Уже используется в Manus** - проверенное решение для AI агентов

---

## Архитектура миграции

### Текущая архитектура (Daytona)

```
┌─────────────────────────────────────────────────────────────┐
│                        SUNA Backend                          │
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Tool Base       │      │  Sandbox Manager │            │
│  │  (tool_base.py)  │─────▶│  (sandbox.py)    │            │
│  └──────────────────┘      └──────────────────┘            │
│                                      │                        │
│                                      ▼                        │
│                            ┌──────────────────┐              │
│                            │  Daytona SDK     │              │
│                            └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  Daytona Cloud   │
                            │  (External)      │
                            └──────────────────┘
```

### Целевая архитектура (E2B)

```
┌─────────────────────────────────────────────────────────────┐
│                        SUNA Backend                          │
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  Tool Base       │      │  Sandbox Manager │            │
│  │  (tool_base.py)  │─────▶│  (sandbox.py)    │            │
│  └──────────────────┘      └──────────────────┘            │
│                                      │                        │
│                                      ▼                        │
│                            ┌──────────────────┐              │
│                            │  E2B SDK         │              │
│                            └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │  E2B BYOC        │
                            │  (AWS VPC)       │
                            └──────────────────┘
```

---

## Фазы миграции

### Фаза 0: Подготовка (1 неделя)

#### Цели
- Исправить текущую проблему с tool calls
- Подготовить окружение для миграции
- Связаться с E2B enterprise team

#### Задачи

1. **Применить исправления на production**
   ```bash
   # На production сервере
   cd /path/to/suna
   git pull origin main
   # Перезапустить backend
   systemctl restart suna-backend  # или ваш метод
   ```

2. **Создать тестовое окружение**
   - Клонировать production database
   - Настроить staging сервер
   - Подготовить тестовые данные

3. **Связаться с E2B**
   - Email: enterprise@e2b.dev
   - Запросить pricing и technical details
   - Обсудить timeline для BYOC deployment

4. **Изучить E2B SDK**
   ```bash
   # Установить E2B SDK
   pip install e2b-code-interpreter
   
   # Изучить документацию
   # https://e2b.dev/docs
   ```

#### Критерии завершения
- ✅ Tool calls работают корректно на production
- ✅ Staging окружение готово
- ✅ Получен ответ от E2B enterprise team
- ✅ Команда изучила E2B SDK

---

### Фаза 1: Proof of Concept (2 недели)

#### Цели
- Создать E2B account и получить API key
- Протестировать E2B Cloud
- Разработать адаптер для совместимости

#### Задачи

1. **Создать E2B account**
   - Зарегистрироваться на https://e2b.dev
   - Получить API key
   - Настроить environment variables

2. **Создать адаптер слой**
   
   Создать файл `backend/core/sandbox/e2b_adapter.py`:
   
   ```python
   """
   Адаптер для E2B SDK, совместимый с текущим Daytona API
   """
   from e2b_code_interpreter import Sandbox as E2BSandbox
   from typing import Optional, List
   import asyncio
   
   class E2BAdapter:
       """Адаптер для E2B, имитирующий Daytona API"""
       
       def __init__(self, api_key: str):
           self.api_key = api_key
           self._sandbox = None
       
       async def create(self, **kwargs) -> 'E2BSandboxWrapper':
           """Создать новый sandbox"""
           sandbox = await E2BSandbox.create(api_key=self.api_key)
           return E2BSandboxWrapper(sandbox)
       
       async def get(self, sandbox_id: str) -> 'E2BSandboxWrapper':
           """Получить существующий sandbox"""
           # E2B не поддерживает получение по ID напрямую
           # Нужно хранить mapping в БД
           sandbox = await E2BSandbox.connect(sandbox_id, api_key=self.api_key)
           return E2BSandboxWrapper(sandbox)
   
   class E2BSandboxWrapper:
       """Обертка для E2B Sandbox, совместимая с Daytona API"""
       
       def __init__(self, sandbox: E2BSandbox):
           self._sandbox = sandbox
           self.id = sandbox.sandbox_id
           self.state = "STARTED"  # E2B всегда в STARTED состоянии
       
       @property
       def fs(self):
           """File system API"""
           return E2BFileSystemAPI(self._sandbox)
       
       @property
       def process(self):
           """Process execution API"""
           return E2BProcessAPI(self._sandbox)
       
       async def get_preview_link(self, port: int):
           """Получить preview link для порта"""
           # E2B автоматически создает preview links
           url = f"https://{self.id}-{port}.e2b.dev"
           return PreviewLink(url=url, token=None)
   
   class E2BFileSystemAPI:
       """File system API для E2B"""
       
       def __init__(self, sandbox: E2BSandbox):
           self._sandbox = sandbox
       
       async def list_files(self, path: str) -> List:
           """Список файлов в директории"""
           result = await self._sandbox.filesystem.list(path)
           return [FileInfo(name=f.name, is_dir=f.is_dir, size=f.size) for f in result]
       
       async def download_file(self, path: str) -> bytes:
           """Скачать файл"""
           content = await self._sandbox.filesystem.read(path)
           return content.encode() if isinstance(content, str) else content
       
       async def upload_file(self, path: str, content: bytes):
           """Загрузить файл"""
           await self._sandbox.filesystem.write(path, content.decode())
       
       async def get_file_info(self, path: str):
           """Информация о файле"""
           # E2B не имеет прямого метода для file info
           # Используем list на parent directory
           import os
           parent = os.path.dirname(path)
           filename = os.path.basename(path)
           files = await self.list_files(parent)
           for f in files:
               if f.name == filename:
                   return f
           raise FileNotFoundError(f"File not found: {path}")
   
   class E2BProcessAPI:
       """Process execution API для E2B"""
       
       def __init__(self, sandbox: E2BSandbox):
           self._sandbox = sandbox
           self._sessions = {}
       
       async def create_session(self, session_id: str):
           """Создать сессию"""
           self._sessions[session_id] = True
       
       async def execute_session_command(self, session_id: str, request):
           """Выполнить команду в сессии"""
           command = request.command
           result = await self._sandbox.commands.run(command)
           return result
   
   class PreviewLink:
       def __init__(self, url: str, token: Optional[str]):
           self.url = url
           self.token = token
   
   class FileInfo:
       def __init__(self, name: str, is_dir: bool, size: int):
           self.name = name
           self.is_dir = is_dir
           self.size = size
           self.mod_time = None
   ```

3. **Обновить sandbox.py**
   
   Добавить feature flag для переключения между Daytona и E2B:
   
   ```python
   # backend/core/sandbox/sandbox.py
   import os
   from core.utils.config import config
   
   USE_E2B = os.getenv('USE_E2B', 'false').lower() == 'true'
   
   if USE_E2B:
       from core.sandbox.e2b_adapter import E2BAdapter
       sandbox_client = E2BAdapter(api_key=config.E2B_API_KEY)
   else:
       from daytona_sdk import AsyncDaytona, DaytonaConfig
       daytona_config = DaytonaConfig(
           api_key=config.DAYTONA_API_KEY,
           api_url=config.DAYTONA_SERVER_URL,
           target=config.DAYTONA_TARGET,
       )
       sandbox_client = AsyncDaytona(daytona_config)
   ```

4. **Тестирование**
   - Создать unit tests для адаптера
   - Протестировать file operations
   - Протестировать process execution
   - Сравнить производительность с Daytona

#### Критерии завершения
- ✅ E2B адаптер работает
- ✅ Все тесты проходят
- ✅ Производительность приемлема
- ✅ Нет критических проблем

---

### Фаза 2: E2B BYOC Deployment (2-3 недели)

#### Цели
- Развернуть E2B BYOC в AWS
- Настроить VPC и networking
- Интегрировать с SUNA backend

#### Задачи

1. **Подготовка AWS**
   - Создать dedicated AWS account (или использовать существующий)
   - Создать IAM role для E2B
   - Увеличить quota limits (если нужно)
   - Выбрать регион (например, us-east-1)

2. **Deployment через Terraform**
   ```bash
   # Получить Terraform конфигурацию от E2B
   # Настроить variables.tf
   
   terraform init
   terraform plan
   terraform apply
   ```

3. **Настройка networking**
   - Настроить VPC peering (если нужно)
   - Настроить security groups
   - Настроить load balancer (internal или public)
   - Настроить DNS

4. **Интеграция с SUNA**
   - Обновить E2B API endpoint в конфигурации
   - Настроить authentication
   - Обновить environment variables:
     ```bash
     E2B_API_KEY=your_byoc_api_key
     E2B_API_URL=https://your-byoc-cluster.example.com
     USE_E2B=true
     ```

5. **Мониторинг и логирование**
   - Настроить CloudWatch для логов
   - Настроить метрики и алерты
   - Интегрировать с существующим мониторингом

#### Критерии завершения
- ✅ E2B BYOC кластер запущен
- ✅ SUNA может создавать sandbox в BYOC
- ✅ Мониторинг настроен
- ✅ Документация обновлена

---

### Фаза 3: Постепенная миграция (3-4 недели)

#### Цели
- Постепенно мигрировать инструменты на E2B
- Мониторить стабильность и производительность
- Исправлять проблемы по мере обнаружения

#### Задачи

1. **Миграция инструментов по приоритету**
   
   **Неделя 1: Files Tool**
   - Мигрировать `sb_files_tool.py`
   - Тестировать file operations
   - Мониторить ошибки
   
   **Неделя 2: Upload File Tool**
   - Мигрировать `sb_upload_file_tool.py`
   - Тестировать загрузку файлов
   
   **Неделя 3: Browser Tool**
   - Мигрировать `browser_tool.py`
   - Тестировать Chrome DevTools integration
   - Проверить VNC доступ
   
   **Неделя 4: Остальные инструменты**
   - Мигрировать все оставшиеся инструменты
   - Финальное тестирование

2. **A/B тестирование**
   - 10% пользователей на E2B
   - 90% на Daytona
   - Постепенно увеличивать до 100%

3. **Мониторинг метрик**
   - Latency создания sandbox
   - Количество ошибок
   - Производительность file operations
   - Использование ресурсов

4. **Rollback план**
   - Если критические проблемы:
     ```bash
     # Откатиться на Daytona
     export USE_E2B=false
     systemctl restart suna-backend
     ```

#### Критерии завершения
- ✅ Все инструменты работают на E2B
- ✅ Метрики в пределах нормы
- ✅ Нет критических ошибок
- ✅ Пользователи не замечают разницы

---

### Фаза 4: Decommission Daytona (1 неделя)

#### Цели
- Полностью отключить Daytona
- Удалить зависимости
- Обновить документацию

#### Задачи

1. **Отключить Daytona**
   - Удалить Daytona API keys
   - Удалить environment variables
   - Остановить все Daytona sandbox

2. **Очистить код**
   - Удалить `daytona_sdk` из requirements.txt
   - Удалить Daytona-specific код
   - Упростить sandbox.py

3. **Обновить документацию**
   - Обновить README
   - Обновить deployment guide
   - Обновить troubleshooting guide

4. **Финальное тестирование**
   - Полный regression test
   - Load testing
   - Security audit

#### Критерии завершения
- ✅ Daytona полностью удален
- ✅ Код очищен
- ✅ Документация обновлена
- ✅ Все тесты проходят

---

## Риски и митигация

### Риск 1: E2B BYOC слишком дорогой
**Вероятность:** Средняя  
**Влияние:** Высокое  
**Митигация:** Подготовить план B с Microsandbox

### Риск 2: Проблемы с производительностью
**Вероятность:** Низкая  
**Влияние:** Среднее  
**Митигация:** Тщательное тестирование в Фазе 1, A/B testing в Фазе 3

### Риск 3: Несовместимость API
**Вероятность:** Средняя  
**Влияние:** Среднее  
**Митигация:** Адаптер слой, постепенная миграция

### Риск 4: Проблемы с AWS deployment
**Вероятность:** Низкая  
**Влияние:** Высокое  
**Митигация:** Помощь от E2B enterprise support

---

## Оценка ресурсов

### Время
- **Общее время:** 8-10 недель
- **Критический путь:** Фаза 2 (BYOC deployment)

### Команда
- **Backend разработчик:** 1 человек, full-time
- **DevOps инженер:** 1 человек, part-time (Фаза 2)
- **QA инженер:** 1 человек, part-time (все фазы)

### Инфраструктура
- **AWS account** для E2B BYOC
- **Staging сервер** для тестирования
- **Мониторинг** (CloudWatch, Grafana)

---

## Чеклист миграции

### Подготовка
- [ ] Исправить проблему с tool calls на production
- [ ] Создать staging окружение
- [ ] Связаться с E2B enterprise team
- [ ] Получить pricing и technical details
- [ ] Изучить E2B SDK

### Proof of Concept
- [ ] Создать E2B account
- [ ] Разработать адаптер слой
- [ ] Написать unit tests
- [ ] Протестировать производительность
- [ ] Принять решение: продолжать или rollback

### BYOC Deployment
- [ ] Подготовить AWS account
- [ ] Создать IAM role
- [ ] Развернуть через Terraform
- [ ] Настроить networking
- [ ] Настроить мониторинг

### Миграция
- [ ] Мигрировать Files Tool
- [ ] Мигрировать Upload File Tool
- [ ] Мигрировать Browser Tool
- [ ] Мигрировать остальные инструменты
- [ ] A/B тестирование
- [ ] Постепенное увеличение трафика на E2B

### Завершение
- [ ] Отключить Daytona
- [ ] Удалить зависимости
- [ ] Обновить документацию
- [ ] Финальное тестирование
- [ ] Объявить о завершении миграции

---

## Контакты и ресурсы

### E2B
- **Website:** https://e2b.dev
- **Docs:** https://e2b.dev/docs
- **GitHub:** https://github.com/e2b-dev/e2b
- **Enterprise:** enterprise@e2b.dev

### Внутренние
- **Slack channel:** #suna-sandbox-migration
- **Confluence:** [Migration Plan Page]
- **Jira:** [SUNA-XXX] Migrate from Daytona to E2B

---

## Следующие шаги

1. **Немедленно:**
   - Применить исправления tool calls на production
   - Создать Slack channel для миграции

2. **Эта неделя:**
   - Связаться с E2B enterprise team
   - Создать staging окружение
   - Начать изучение E2B SDK

3. **Следующая неделя:**
   - Получить ответ от E2B
   - Принять решение: E2B vs. альтернативы
   - Начать Фазу 1 (Proof of Concept)

4. **Следующий месяц:**
   - Завершить PoC
   - Начать BYOC deployment
   - Подготовить команду к миграции
