# Исправления для проблемы "Could not find details for this tool call"

## Файл: `/home/ubuntu/suna/backend/core/agentpress/response_processor.py`

### Исправление 1: Строки 597-603 (было 597-601)

**Проблема:** Assistant message не сохранялся, если не было текстового контента, даже если были tool calls.

**Было:**
```python
should_auto_continue = (can_auto_continue and finish_reason == 'length')

# Don't save partial response if user stopped (cancelled)
# But do save for other early stops like XML limit reached
if accumulated_content and not should_auto_continue and finish_reason != "cancelled":
```

**Стало:**
```python
should_auto_continue = (can_auto_continue and finish_reason == 'length')

# Don't save partial response if user stopped (cancelled)
# But do save for other early stops like XML limit reached
# CRITICAL FIX: Also save if there are tool calls even without text content
has_tool_calls = (xml_tool_call_count > 0 or len(complete_native_tool_calls) > 0)
if (accumulated_content or has_tool_calls) and not should_auto_continue and finish_reason != "cancelled":
```

**Эффект:** Теперь assistant message будет сохраняться, даже если нет текста, но есть tool calls. Это гарантирует, что `last_assistant_message_object` не будет None.

---

### Исправление 2: Строки 712-718 (было 712-714)

**Проблема:** Не было логирования, когда `last_assistant_message_object` был None.

**Было:**
```python
for tool_call, result, tool_idx, context in tool_results_buffer:
    if last_assistant_message_object: context.assistant_message_id = last_assistant_message_object['message_id']
    tool_results_map[tool_idx] = (tool_call, result, context)
```

**Стало:**
```python
for tool_call, result, tool_idx, context in tool_results_buffer:
    if last_assistant_message_object:
        context.assistant_message_id = last_assistant_message_object['message_id']
    else:
        logger.warning(f"CRITICAL: last_assistant_message_object is None for tool_idx {tool_idx}, tool: {tool_call.get('function_name', 'unknown')}")
        logger.warning(f"accumulated_content length: {len(accumulated_content) if accumulated_content else 0}, xml_tool_call_count: {xml_tool_call_count}")
    tool_results_map[tool_idx] = (tool_call, result, context)
```

**Эффект:** Теперь будет логироваться предупреждение, если `last_assistant_message_object` все еще None, что поможет в отладке.

---

### Исправление 3: Строки 759-766 (было 759-760)

**Проблема:** Не было проверки и логирования, если `assistant_message_id` все еще None перед сохранением tool result.

**Было:**
```python
if not context.assistant_message_id and last_assistant_message_object:
    context.assistant_message_id = last_assistant_message_object['message_id']

# Yield start status ONLY IF executing non-streamed (already yielded if streamed)
```

**Стало:**
```python
if not context.assistant_message_id and last_assistant_message_object:
    context.assistant_message_id = last_assistant_message_object['message_id']
    logger.info(f"Updated context.assistant_message_id to {context.assistant_message_id} for tool_idx {tool_idx}")

# CRITICAL CHECK: Log if assistant_message_id is still None
if not context.assistant_message_id:
    logger.error(f"CRITICAL: context.assistant_message_id is STILL None for tool_idx {tool_idx}, tool: {tool_call.get('function_name', 'unknown')}")
    logger.error(f"This will cause 'Could not find details for this tool call' error in frontend!")

# Yield start status ONLY IF executing non-streamed (already yielded if streamed)
```

**Эффект:** Добавлено логирование для отслеживания обновления `assistant_message_id` и критическая ошибка, если он все еще None перед сохранением.

---

## Как это исправляет проблему

1. **Основное исправление (Исправление 1):** Гарантирует, что assistant message всегда сохраняется, если есть tool calls, даже без текстового контента. Это означает, что `last_assistant_message_object` больше не будет None.

2. **Дополнительная защита (Исправления 2 и 3):** Добавляет логирование для отслеживания проблемы, если она все еще возникает по какой-то другой причине.

3. **Результат:** Tool result будет сохраняться с правильным `assistant_message_id` в metadata, что позволит frontend найти связь между assistant message и tool result.

---

## Тестирование

### Шаг 1: Запустить backend
```bash
cd /home/ubuntu/suna
python start.py
```

### Шаг 2: Воспроизвести проблему
1. Отправить сообщение в чат, которое вызывает создание файла
2. Например: "Создай HTML-страницу с презентацией SUNA AI"

### Шаг 3: Проверить логи
Посмотреть в логах backend:
- Должно быть сообщение: `"Processing X buffered tool results"`
- НЕ должно быть: `"CRITICAL: last_assistant_message_object is None"`
- НЕ должно быть: `"CRITICAL: context.assistant_message_id is STILL None"`

### Шаг 4: Проверить frontend
1. Нажать на созданный файл для просмотра
2. Должно открыться превью файла
3. НЕ должно быть ошибки: "Could not find details for this tool call"

### Шаг 5: Проверить БД
Проверить, что в таблице messages для tool result есть metadata с `assistant_message_id`:
```sql
SELECT message_id, type, metadata 
FROM messages 
WHERE type = 'tool' 
ORDER BY created_at DESC 
LIMIT 5;
```

В metadata должно быть: `{"assistant_message_id": "..."}`

---

## Откат изменений (если нужно)

Если что-то пойдет не так, можно откатить изменения:

```bash
cd /home/ubuntu/suna
git diff backend/core/agentpress/response_processor.py
git checkout backend/core/agentpress/response_processor.py
```

---

## Дополнительные заметки

- Изменения затрагивают только backend, frontend не изменялся
- Изменения обратно совместимы - не ломают существующий функционал
- Добавлено подробное логирование для отладки
- Исправление решает корневую причину проблемы, а не симптомы
