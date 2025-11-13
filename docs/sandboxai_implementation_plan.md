# План внедрения SandboxAI в SUNA

**Дата:** 13 ноября 2025  
**Решение:** SandboxAI от Substratus  
**Timeline:** 2-3 недели  
**Цель:** Заменить Daytona на бесплатное self-hosted решение

---

## Архитектурное решение

### Текущая архитектура (Daytona)

```
SUNA Backend (Python)
    ↓
sandbox/sandbox.py (DaytonaClient)
    ↓
Daytona API (External Service)
    ↓
Daytona Workspace (Container)
```

### Новая архитектура (SandboxAI)

```
SUNA Backend (Python)
    ↓
sandbox/sandboxai_adapter.py (SandboxAIClient)
    ↓
SandboxAI Server (Local/Self-hosted)
    ↓
Docker Containers (Managed by SandboxAI)
```

---

## Фаза 1: Подготовка и PoC (Неделя 1)

### День 1-2: Установка и тестирование SandboxAI

**Задачи:**

1. **Установить SandboxAI на dev сервере**
   ```bash
   # На dev сервере
   cd /home/ubuntu
   
   # Проверить Docker
   docker --version
   docker ps
   
   # Установить SandboxAI client
   pip3 install sandboxai-client
   
   # Клонировать SandboxAI для изучения
   git clone https://github.com/substratusai/sandboxai.git
   cd sandboxai
   ```

2. **Создать тестовый скрипт**
   ```python
   # test_sandboxai.py
   from sandboxai import Sandbox
   import time
   
   def test_basic_operations():
       """Тест базовых операций"""
       print("Testing SandboxAI basic operations...")
       
       with Sandbox(embedded=True) as box:
           # Test 1: Python code execution
           result = box.run_ipython_cell("print('Hello from SandboxAI')")
           print(f"Python test: {result.output}")
           assert "Hello from SandboxAI" in result.output
           
           # Test 2: Shell command
           result = box.run_shell_command("echo 'Shell test'")
           print(f"Shell test: {result.output}")
           assert "Shell test" in result.output
           
           # Test 3: File operations
           box.run_ipython_cell("with open('/tmp/test.txt', 'w') as f: f.write('test content')")
           result = box.run_shell_command("cat /tmp/test.txt")
           print(f"File test: {result.output}")
           assert "test content" in result.output
           
           print("✅ All tests passed!")
   
   def test_performance():
       """Тест производительности"""
       print("\nTesting performance...")
       
       start = time.time()
       with Sandbox(embedded=True) as box:
           box.run_ipython_cell("import numpy as np; print(np.array([1,2,3]))")
       elapsed = time.time() - start
       
       print(f"Sandbox creation + execution time: {elapsed:.2f}s")
   
   if __name__ == "__main__":
       test_basic_operations()
       test_performance()
   ```

3. **Запустить тесты**
   ```bash
   python3 test_sandboxai.py
   ```

4. **Оценить результаты**
   - ✅ Работает ли SandboxAI на сервере?
   - ✅ Какая производительность?
   - ✅ Есть ли проблемы с Docker?

### День 3-4: Разработка адаптера

**Создать файл:** `backend/core/sandbox/sandboxai_adapter.py`

```python
"""
SandboxAI Adapter for SUNA
Provides compatibility layer between SUNA and SandboxAI
"""

import os
import json
from typing import Dict, Any, Optional
from sandboxai import Sandbox
import logging

logger = logging.getLogger(__name__)


class SandboxAIClient:
    """
    Adapter class to interface with SandboxAI
    Provides API compatible with existing SUNA sandbox interface
    """
    
    def __init__(self, workspace_id: str, **kwargs):
        """
        Initialize SandboxAI client
        
        Args:
            workspace_id: Unique identifier for the workspace
            **kwargs: Additional configuration options
        """
        self.workspace_id = workspace_id
        self.workspace_dir = kwargs.get('workspace_dir', f'/workspace/{workspace_id}')
        self.sandbox = None
        self.embedded = kwargs.get('embedded', True)
        
        logger.info(f"Initialized SandboxAI client for workspace: {workspace_id}")
    
    def connect(self):
        """Connect to or create a sandbox"""
        try:
            self.sandbox = Sandbox(embedded=self.embedded)
            self.sandbox.__enter__()
            
            # Create workspace directory
            self.sandbox.run_shell_command(f"mkdir -p {self.workspace_dir}")
            
            logger.info(f"Connected to sandbox for workspace: {self.workspace_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to sandbox: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from sandbox"""
        if self.sandbox:
            try:
                self.sandbox.__exit__(None, None, None)
                logger.info(f"Disconnected from sandbox: {self.workspace_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from sandbox: {e}")
    
    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Execute code in the sandbox
        
        Args:
            code: Code to execute
            language: Programming language (python, bash, etc.)
            
        Returns:
            Dict with execution result
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected. Call connect() first.")
        
        try:
            if language == "python":
                result = self.sandbox.run_ipython_cell(code)
            elif language in ["bash", "shell"]:
                result = self.sandbox.run_shell_command(code)
            else:
                raise ValueError(f"Unsupported language: {language}")
            
            return {
                "success": True,
                "output": result.output,
                "error": result.error if hasattr(result, 'error') else None
            }
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file in the sandbox
        
        Args:
            file_path: Path to the file (relative to workspace)
            content: File content
            
        Returns:
            Dict with operation result
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected. Call connect() first.")
        
        try:
            # Escape content for shell
            escaped_content = content.replace("'", "'\\''")
            full_path = os.path.join(self.workspace_dir, file_path)
            
            # Create directory if needed
            dir_path = os.path.dirname(full_path)
            if dir_path:
                self.sandbox.run_shell_command(f"mkdir -p {dir_path}")
            
            # Write file
            code = f"echo '{escaped_content}' > {full_path}"
            result = self.sandbox.run_shell_command(code)
            
            return {
                "success": True,
                "path": full_path,
                "message": f"File written: {file_path}"
            }
        except Exception as e:
            logger.error(f"File write failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file in the sandbox
        
        Args:
            file_path: Path to the file (relative to workspace)
            
        Returns:
            Dict with file content
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected. Call connect() first.")
        
        try:
            full_path = os.path.join(self.workspace_dir, file_path)
            result = self.sandbox.run_shell_command(f"cat {full_path}")
            
            return {
                "success": True,
                "content": result.output,
                "path": full_path
            }
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_files(self, directory: str = ".") -> Dict[str, Any]:
        """
        List files in a directory
        
        Args:
            directory: Directory path (relative to workspace)
            
        Returns:
            Dict with file list
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected. Call connect() first.")
        
        try:
            full_path = os.path.join(self.workspace_dir, directory)
            result = self.sandbox.run_shell_command(f"ls -la {full_path}")
            
            return {
                "success": True,
                "output": result.output,
                "files": result.output.split('\n')
            }
        except Exception as e:
            logger.error(f"List files failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def execute_shell_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command in the sandbox
        
        Args:
            command: Shell command to execute
            cwd: Working directory (relative to workspace)
            
        Returns:
            Dict with command result
        """
        if not self.sandbox:
            raise RuntimeError("Sandbox not connected. Call connect() first.")
        
        try:
            if cwd:
                full_cwd = os.path.join(self.workspace_dir, cwd)
                command = f"cd {full_cwd} && {command}"
            else:
                command = f"cd {self.workspace_dir} && {command}"
            
            result = self.sandbox.run_shell_command(command)
            
            return {
                "success": True,
                "output": result.output,
                "error": result.error if hasattr(result, 'error') else None
            }
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }


# Context manager support
class SandboxAIContext:
    """Context manager for SandboxAI client"""
    
    def __init__(self, workspace_id: str, **kwargs):
        self.client = SandboxAIClient(workspace_id, **kwargs)
    
    def __enter__(self):
        self.client.connect()
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
        return False


# Factory function
def create_sandbox_client(workspace_id: str, **kwargs) -> SandboxAIClient:
    """
    Factory function to create a sandbox client
    
    Args:
        workspace_id: Unique identifier for the workspace
        **kwargs: Additional configuration options
        
    Returns:
        SandboxAIClient instance
    """
    return SandboxAIClient(workspace_id, **kwargs)
```

### День 5-7: Интеграция с существующими tools

**Обновить:** `backend/core/tools/sb_files_tool.py`

```python
# В начале файла добавить:
from core.sandbox.sandboxai_adapter import create_sandbox_client

# В методе execute обновить создание sandbox:
def execute(self, params, context):
    workspace_id = context.get('workspace_id')
    
    # Используем SandboxAI вместо Daytona
    with SandboxAIContext(workspace_id) as sandbox:
        if action == "write":
            result = sandbox.write_file(file_path, content)
        elif action == "read":
            result = sandbox.read_file(file_path)
        elif action == "list":
            result = sandbox.list_files(directory)
        
        return result
```

**Аналогично обновить:**
- `sb_shell_tool.py`
- `sb_python_tool.py`
- Другие tools, использующие sandbox

---

## Фаза 2: Полная интеграция (Неделя 2)

### День 8-10: Замена Daytona на SandboxAI

**Задачи:**

1. **Обновить sandbox factory**
   
   Создать `backend/core/sandbox/__init__.py`:
   ```python
   """
   Sandbox factory module
   Provides unified interface for different sandbox backends
   """
   
   import os
   from typing import Optional
   
   SANDBOX_BACKEND = os.getenv('SANDBOX_BACKEND', 'sandboxai')  # 'daytona' or 'sandboxai'
   
   def get_sandbox_client(workspace_id: str, **kwargs):
       """
       Get sandbox client based on configuration
       
       Args:
           workspace_id: Unique identifier for the workspace
           **kwargs: Additional configuration options
           
       Returns:
           Sandbox client instance
       """
       if SANDBOX_BACKEND == 'sandboxai':
           from .sandboxai_adapter import create_sandbox_client
           return create_sandbox_client(workspace_id, **kwargs)
       elif SANDBOX_BACKEND == 'daytona':
           from .sandbox import DaytonaClient  # Old implementation
           return DaytonaClient(workspace_id, **kwargs)
       else:
           raise ValueError(f"Unknown sandbox backend: {SANDBOX_BACKEND}")
   ```

2. **Обновить все tools для использования factory**
   
   В каждом tool файле:
   ```python
   from core.sandbox import get_sandbox_client
   
   # Вместо:
   # from core.sandbox.sandbox import DaytonaClient
   # sandbox = DaytonaClient(workspace_id)
   
   # Использовать:
   sandbox = get_sandbox_client(workspace_id)
   ```

3. **Добавить environment variable**
   
   В `.env`:
   ```bash
   SANDBOX_BACKEND=sandboxai
   ```

4. **Тестирование**
   ```bash
   # Запустить backend с SandboxAI
   cd /path/to/suna/backend
   export SANDBOX_BACKEND=sandboxai
   python run.py
   
   # Протестировать все функции
   - Создание файлов
   - Чтение файлов
   - Выполнение кода
   - Shell команды
   ```

### День 11-12: Добавление недостающих функций

**1. Browser support (опционально)**

SandboxAI не поддерживает browser из коробки, но можно добавить через Playwright:

```python
# backend/core/sandbox/browser_support.py

from sandboxai import Sandbox

def setup_browser_in_sandbox(sandbox: Sandbox):
    """Install and setup Playwright in sandbox"""
    
    # Install Playwright
    sandbox.run_shell_command("pip install playwright")
    sandbox.run_shell_command("playwright install chromium")
    
    return True

def run_browser_script(sandbox: Sandbox, script: str):
    """Run Playwright script in sandbox"""
    
    code = f"""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    {script}
    browser.close()
"""
    
    result = sandbox.run_ipython_cell(code)
    return result
```

**2. File upload support**

```python
# backend/core/sandbox/file_upload.py

def upload_file_to_sandbox(sandbox: Sandbox, local_path: str, remote_path: str):
    """Upload file from local to sandbox"""
    
    # Read local file
    with open(local_path, 'r') as f:
        content = f.read()
    
    # Write to sandbox
    escaped_content = content.replace("'", "'\\''")
    sandbox.run_shell_command(f"echo '{escaped_content}' > {remote_path}")
    
    return True
```

### День 13-14: Мониторинг и логирование

**Добавить мониторинг:**

```python
# backend/core/sandbox/monitoring.py

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def monitor_sandbox_operation(func):
    """Decorator to monitor sandbox operations"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        operation_name = func.__name__
        
        try:
            logger.info(f"Starting sandbox operation: {operation_name}")
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            
            logger.info(f"Sandbox operation completed: {operation_name} ({elapsed:.2f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Sandbox operation failed: {operation_name} ({elapsed:.2f}s) - {e}")
            raise
    
    return wrapper
```

**Обновить adapter с мониторингом:**

```python
from .monitoring import monitor_sandbox_operation

class SandboxAIClient:
    @monitor_sandbox_operation
    def execute_code(self, code: str, language: str = "python"):
        # ... existing code ...
    
    @monitor_sandbox_operation
    def write_file(self, file_path: str, content: str):
        # ... existing code ...
```

---

## Фаза 3: Тестирование и деплой (Неделя 3)

### День 15-17: A/B тестирование

**1. Настроить feature flag**

```python
# backend/core/config.py

import os

class Config:
    SANDBOX_BACKEND = os.getenv('SANDBOX_BACKEND', 'sandboxai')
    SANDBOX_AB_TEST = os.getenv('SANDBOX_AB_TEST', 'false').lower() == 'true'
    SANDBOX_AB_PERCENTAGE = int(os.getenv('SANDBOX_AB_PERCENTAGE', '10'))
```

**2. Реализовать A/B логику**

```python
# backend/core/sandbox/__init__.py

import random
from .config import Config

def get_sandbox_client(workspace_id: str, **kwargs):
    """Get sandbox client with A/B testing support"""
    
    if Config.SANDBOX_AB_TEST:
        # A/B testing mode
        if random.randint(1, 100) <= Config.SANDBOX_AB_PERCENTAGE:
            backend = 'sandboxai'
        else:
            backend = 'daytona'
    else:
        backend = Config.SANDBOX_BACKEND
    
    if backend == 'sandboxai':
        from .sandboxai_adapter import create_sandbox_client
        return create_sandbox_client(workspace_id, **kwargs)
    elif backend == 'daytona':
        from .sandbox import DaytonaClient
        return DaytonaClient(workspace_id, **kwargs)
```

**3. Тестирование по этапам**

**Этап 1: 10% пользователей (День 15)**
```bash
export SANDBOX_AB_TEST=true
export SANDBOX_AB_PERCENTAGE=10
python run.py
```

Мониторить:
- Ошибки в логах
- Производительность
- Отзывы пользователей

**Этап 2: 50% пользователей (День 16)**
```bash
export SANDBOX_AB_PERCENTAGE=50
```

**Этап 3: 100% пользователей (День 17)**
```bash
export SANDBOX_AB_TEST=false
export SANDBOX_BACKEND=sandboxai
```

### День 18-19: Оптимизация

**1. Кеширование sandbox контейнеров**

```python
# backend/core/sandbox/cache.py

from typing import Dict
from .sandboxai_adapter import SandboxAIClient

class SandboxCache:
    """Cache for sandbox instances"""
    
    def __init__(self, max_size: int = 10):
        self._cache: Dict[str, SandboxAIClient] = {}
        self._max_size = max_size
    
    def get(self, workspace_id: str) -> Optional[SandboxAIClient]:
        """Get cached sandbox or None"""
        return self._cache.get(workspace_id)
    
    def set(self, workspace_id: str, sandbox: SandboxAIClient):
        """Cache sandbox instance"""
        if len(self._cache) >= self._max_size:
            # Remove oldest
            oldest_key = next(iter(self._cache))
            self._cache[oldest_key].disconnect()
            del self._cache[oldest_key]
        
        self._cache[workspace_id] = sandbox
    
    def clear(self):
        """Clear all cached sandboxes"""
        for sandbox in self._cache.values():
            sandbox.disconnect()
        self._cache.clear()

# Global cache instance
_sandbox_cache = SandboxCache()

def get_cached_sandbox(workspace_id: str) -> Optional[SandboxAIClient]:
    return _sandbox_cache.get(workspace_id)

def cache_sandbox(workspace_id: str, sandbox: SandboxAIClient):
    _sandbox_cache.set(workspace_id, sandbox)
```

**2. Настройка Docker для production**

```bash
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 64000,
      "Soft": 64000
    }
  }
}
```

### День 20-21: Decommission Daytona

**1. Удалить Daytona код**

```bash
cd /path/to/suna/backend

# Backup старого кода
git checkout -b backup/daytona-removal
cp -r core/sandbox core/sandbox.backup

# Удалить Daytona файлы
rm core/sandbox/sandbox.py  # Старый Daytona client
rm -rf core/sandbox/daytona_*  # Daytona-specific файлы
```

**2. Обновить dependencies**

```bash
# requirements.txt
# Удалить:
# daytona-sdk==x.x.x

# Добавить:
sandboxai-client>=0.1.0
```

**3. Обновить документацию**

```markdown
# docs/SANDBOX.md

## Sandbox Architecture

SUNA uses SandboxAI for secure code execution in isolated Docker containers.

### Setup

1. Install Docker
2. Install SandboxAI client: `pip install sandboxai-client`
3. Configure environment: `export SANDBOX_BACKEND=sandboxai`

### Usage

All sandbox operations are handled automatically through the sandbox factory.

### Troubleshooting

- Check Docker is running: `docker ps`
- Check logs: `tail -f logs/sandbox.log`
```

---

## Мониторинг и метрики

### Ключевые метрики для отслеживания

1. **Производительность**
   - Время создания sandbox
   - Время выполнения кода
   - Использование CPU/Memory

2. **Надежность**
   - Success rate операций
   - Количество ошибок
   - Uptime sandbox

3. **Использование**
   - Количество активных sandbox
   - Количество операций в день
   - Средняя продолжительность сессии

### Настройка мониторинга

```python
# backend/core/sandbox/metrics.py

import time
from prometheus_client import Counter, Histogram, Gauge

# Counters
sandbox_operations_total = Counter(
    'sandbox_operations_total',
    'Total number of sandbox operations',
    ['operation_type', 'status']
)

# Histograms
sandbox_operation_duration = Histogram(
    'sandbox_operation_duration_seconds',
    'Duration of sandbox operations',
    ['operation_type']
)

# Gauges
active_sandboxes = Gauge(
    'active_sandboxes',
    'Number of currently active sandboxes'
)

def record_operation(operation_type: str, duration: float, success: bool):
    """Record sandbox operation metrics"""
    status = 'success' if success else 'failure'
    sandbox_operations_total.labels(operation_type=operation_type, status=status).inc()
    sandbox_operation_duration.labels(operation_type=operation_type).observe(duration)
```

---

## Rollback план

Если что-то пойдет не так, можно быстро вернуться к Daytona:

```bash
# 1. Переключить environment variable
export SANDBOX_BACKEND=daytona

# 2. Перезапустить backend
systemctl restart suna-backend

# 3. Восстановить старый код (если удален)
git checkout backup/daytona-removal
cp -r core/sandbox.backup/* core/sandbox/

# 4. Восстановить dependencies
pip install daytona-sdk
```

---

## Чеклист готовности к деплою

### Перед началом миграции

- [ ] Docker установлен и работает
- [ ] SandboxAI протестирован локально
- [ ] Адаптер разработан и протестирован
- [ ] Все tools обновлены для использования factory
- [ ] Мониторинг настроен
- [ ] Rollback план готов

### Перед A/B тестированием

- [ ] Feature flag реализован
- [ ] Логирование настроено
- [ ] Метрики собираются
- [ ] Alerts настроены

### Перед полным переходом

- [ ] A/B тестирование успешно (10% → 50% → 100%)
- [ ] Нет критических ошибок
- [ ] Производительность приемлема
- [ ] Пользователи довольны

### После миграции

- [ ] Daytona код удален
- [ ] Dependencies обновлены
- [ ] Документация обновлена
- [ ] Команда обучена

---

## Риски и митигация

### Риск 1: SandboxAI нестабилен
**Вероятность:** Средняя  
**Влияние:** Высокое  
**Митигация:**
- Тщательное тестирование в PoC фазе
- A/B тестирование с постепенным увеличением %
- Готовый rollback план

### Риск 2: Производительность хуже Daytona
**Вероятность:** Низкая  
**Влияние:** Среднее  
**Митигация:**
- Benchmark тесты в PoC фазе
- Оптимизация (кеширование, connection pooling)
- Мониторинг метрик

### Риск 3: Недостающие функции
**Вероятность:** Средняя  
**Влияние:** Среднее  
**Митигация:**
- Список всех используемых функций Daytona
- Реализация недостающих функций в адаптере
- Альтернативные решения (например, Playwright для browser)

### Риск 4: Docker проблемы на production
**Вероятность:** Низкая  
**Влияние:** Высокое  
**Митигация:**
- Проверка Docker на production сервере
- Настройка Docker daemon для production
- Мониторинг Docker метрик

---

## Контакты и ресурсы

### SandboxAI
- **GitHub:** https://github.com/substratusai/sandboxai
- **Issues:** https://github.com/substratusai/sandboxai/issues
- **Discord:** (если есть)

### Документация
- **SandboxAI README:** https://github.com/substratusai/sandboxai/blob/main/README.md
- **Docker docs:** https://docs.docker.com/

### Внутренние ресурсы
- **Исследование:** `/home/ubuntu/free_selfhosted_sandbox_research.md`
- **Код адаптера:** `backend/core/sandbox/sandboxai_adapter.py`
- **Тесты:** `test_sandboxai.py`

---

## Заключение

План внедрения SandboxAI рассчитан на **2-3 недели** и включает:

✅ **Неделя 1:** PoC и разработка адаптера  
✅ **Неделя 2:** Полная интеграция и добавление функций  
✅ **Неделя 3:** A/B тестирование, оптимизация, деплой  

Этот план минимизирует риски через постепенную миграцию и обеспечивает возможность быстрого rollback при необходимости.

**Следующий шаг:** Начать с Фазы 1, День 1 - установка и тестирование SandboxAI на dev сервере.
