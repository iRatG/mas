# 🔍 РУКОВОДСТВО ПО ТРАССИРОВКЕ MAS СИСТЕМЫ

## Обзор

MAS система поддерживает **сквозную трассировку** выполнения через correlation ID, что позволяет отслеживать полный жизненный цикл обработки каждого бага от начала до конца.

## 🏷️ Correlation ID Format

### Синхронный подход
```
sync-case{bug_id}-{timestamp}
```
Пример: `sync-case1-7834`

### Асинхронный подход  
```
cid-{sequence:04d}
```
Пример: `cid-0001`

## 📋 Пример полной трассировки

### Кейс: Выход за границы массива (ID=1)

```bash
python main.py --approach sync --cases 1 --verbose
```

**Ожидаемый trace:**
```
[sync-case1-7834] SYNC | Старт обработки кейса 1
[sync-case1-7834] SYNC | Отчёт: Обнаружен выход за границы индекса в цикле range(len(arr)+1).
[sync-case1-7834] SYNC | Кандидаты (2): ['Заменить range(len(arr)+1) на range(len(arr)).', 'Итерироваться по элементам: for x in arr: s += x.']
[sync-case1-7834] SYNC | Вердикт 'approve' для 'Заменить range(len(arr)+1) на range(len(arr)).' по голосам ['approve', 'approve', 'approve', 'approve', 'approve']
[sync-case1-7834] SYNC | Вердикт 'approve' для 'Итерироваться по элементам: for x in arr: s += x.' по голосам ['approve', 'request_changes', 'approve', 'approve', 'approve']  
[sync-case1-7834] SYNC | Тесты: OK
```

**Результат:**
```json
{
  "status": "success",
  "approach": "sync", 
  "correlation_id": "sync-case1-7834",
  "bug_report": "Обнаружен выход за границы индекса...",
  "chosen_fix": "Заменить range(len(arr)+1) на range(len(arr)).",
  "metrics": { ... }
}
```

## 🔄 Асинхронная трассировка

### Агентная коммуникация

```bash
python main.py --approach async --cases 1 --verbose
```

**Ожидаемый trace:**
```
[cid-0001] Agent:Координатор | -> Аналитик (analyze_code)
[cid-0001] Agent:Аналитик | -> Координатор (bug_report)  
[cid-0001] Agent:Координатор | -> Исправитель (bug_report)
[cid-0001] Agent:Исправитель | -> Координатор (fix_candidates)
[cid-0001] Agent:Координатор | -> Контролёр (fix_candidates)
[cid-0001] Agent:Контролёр | -> Координатор (approved_fixes)
```

## 🛠️ Использование трассировки

### 1. Отладка проблем
```bash
# Найти все логи для конкретного кейса
grep "sync-case3" logs.txt

# Отследить путь сообщения в асинхронном режиме  
grep "cid-0002" logs.txt
```

### 2. Анализ производительности
```bash
# Время между началом и концом обработки
grep -E "(Старт обработки|Тесты: OK)" logs.txt | grep "sync-case1"
```

### 3. Поиск узких мест
```bash
# Долгие операции в асинхронном режиме
grep -A5 -B5 "TimeoutError" logs.txt
```

## 📊 Интеграция с аналитикой

Correlation ID автоматически включается в:
- **Логи** - каждое сообщение помечено ID
- **Результаты** - JSON содержит correlation_id
- **Метрики** - связь между временными метками и кейсами

### Пример анализа результатов

```python
import json

# Загружаем результаты
with open('results.json') as f:
    data = json.load(f)

# Группируем по correlation_id
by_correlation = {}
for result in data['detailed_results']:
    cid = result.get('correlation_id')
    if cid:
        by_correlation[cid] = result

# Анализируем самые медленные кейсы
slow_cases = sorted(
    by_correlation.values(),
    key=lambda x: x.get('metrics', {}).get('execution_time_seconds', 0),
    reverse=True
)

print("Топ-3 самых медленных кейсов:")
for case in slow_cases[:3]:
    cid = case['correlation_id'] 
    time = case['metrics']['execution_time_seconds']
    print(f"{cid}: {time}s")
```

## 🔧 Настройка трассировки

### Включение подробных логов
```bash
python main.py --verbose --approach both
```

### Настройка уровня логирования
```python
import logging
logging.getLogger("MAS").setLevel(logging.DEBUG)
logging.getLogger("Agent:Координатор").setLevel(logging.DEBUG)
```

### Кастомный формат логов
```python
import logging

# Добавляем correlation_id в формат логов
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | [%(correlation_id)s] | %(name)s | %(message)s'
)
```

## 🎯 Лучшие практики

### 1. Сохранение correlation_id
```python
# В своих расширениях сохраняйте correlation_id
def my_custom_processor(code, bug_id, correlation_id):
    log.info(f"[{correlation_id}] Начало кастомной обработки")
    # ... обработка ...
    log.info(f"[{correlation_id}] Завершение кастомной обработки")
```

### 2. Передача через цепочку вызовов
```python
# Всегда передавайте correlation_id дальше по цепочке
def process_step_1(data, correlation_id):
    result = do_work(data)
    return process_step_2(result, correlation_id)

def process_step_2(data, correlation_id):
    log.debug(f"[{correlation_id}] Выполняется шаг 2")
    return final_result
```

### 3. Корреляция с внешними системами
```python
# При интеграции с внешними API передавайте correlation_id
headers = {
    'X-Correlation-ID': correlation_id,
    'Authorization': 'Bearer ...'
}
response = requests.post(url, headers=headers, json=data)
```

## 🚀 Расширенные возможности

### Экспорт трассировки в OpenTelemetry
```python
from opentelemetry import trace

def traced_function(correlation_id):
    with trace.get_tracer(__name__).start_as_current_span("mas-processing") as span:
        span.set_attribute("correlation_id", correlation_id)
        span.set_attribute("approach", "sync")
        # ... основная логика ...
```

### Интеграция с системами мониторинга
```python
# Отправка метрик с correlation_id
import statsd
client = statsd.StatsClient()

def send_metrics(correlation_id, execution_time):
    tags = [f"correlation_id:{correlation_id}"]
    client.timing('mas.execution_time', execution_time, tags=tags)
```

## 📈 Примеры использования

### Отладка зависшего кейса
```bash
# 1. Найти correlation_id проблемного кейса
grep "Старт обработки" logs.txt | grep "кейса 3"

# 2. Отследить весь путь выполнения  
grep "sync-case3-1234" logs.txt

# 3. Найти место остановки
grep -A10 -B10 "sync-case3-1234" logs.txt | tail -20
```

### Анализ успешности по типам багов
```bash
# Группировка по типам багов
grep "correlation_id.*case1" results.json  # Выход за границы
grep "correlation_id.*case2" results.json  # None-обращение
grep "correlation_id.*case3" results.json  # Деление на ноль
```

Трассировка делает MAS систему полностью **наблюдаемой** и **отлаживаемой**! 🔍✨
