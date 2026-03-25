# ✅ Парсер НСПД - Полностью готов!

## 🎉 Статус: Production Ready

Полностью рабочий парсер кадастровых данных с API НСПД (Национальная система пространственных данных).

---

## 📋 Что реализовано

### 1. ✅ API клиент (api_client.py)

**Основные методы:**
- `search_cadastral_number(cadastral_number)` - поиск участка/объекта
- `get_objects_on_parcel(feature_id, category_id)` - список объектов на участке
- `get_full_parcel_info(cadastral_number)` - участок + список объектов
- `get_full_parcel_info_with_objects(cadastral_number)` - участок + полные данные объектов
- `parse_parcel_data(feature)` - парсинг данных участка
- `parse_object_data(feature)` - парсинг данных объекта

**Поддержка:**
- Retry логика (3 попытки)
- Задержки между запросами
- Правильные заголовки для обхода WAF
- Форматирование значений (площадь, стоимость, удельная стоимость)

### 2. ✅ Модели данных (models.py)

**Parcel** - Земельный участок
- Кадастровый номер, тип, адрес
- Площадь, ВРИ, форма собственности
- Кадастровая стоимость

**RealtyObject** - Объект недвижимости
- Кадастровый номер, тип, назначение
- Площадь, этажность, материал стен
- Кадастровая стоимость, удельная стоимость
- Год постройки, ввод в эксплуатацию
- Культурное наследие

**ParseResult** - Результат парсинга
- Участок + список объектов
- Метод `to_excel_rows()` для экспорта

### 3. ✅ Тестовые скрипты

- `test_real_api.py` - тест search API (базовый)
- `test_tab_group_data.py` - тест получения списка объектов
- `test_object_details.py` - тест детальных данных объектов
- `test_full_workflow.py` - полный workflow

---

## 🚀 Использование

### Быстрый старт

```python
from api_client import NSPDAPIClient

client = NSPDAPIClient()

try:
    # Получить участок и список объектов
    result = client.get_full_parcel_info("77:05:0001016:22")

    parcel = result['parcel_data']
    objects = result['objects_cadastral_numbers']

    print(f"Участок: {parcel.address}")
    print(f"Объектов: {len(objects)}")

finally:
    client.close()
```

### Полный workflow с объектами

```python
from api_client import NSPDAPIClient
from models import ParseResult

client = NSPDAPIClient()

try:
    # Получить ВСЕ данные (медленно!)
    result = client.get_full_parcel_info_with_objects("77:05:0001016:22")

    # Формируем результат
    parse_result = ParseResult(
        cadastral_number="77:05:0001016:22",
        parcel=result['parcel_data'],
        objects=result['objects_data'],
        status="Успешно"
    )

    # Excel строки
    rows = parse_result.to_excel_rows()
    print(f"Строк для Excel: {len(rows)}")

finally:
    client.close()
```

---

## 📊 Пример результата

### Участок: 77:05:0001016:22

```
Тип: Земельный участок
Адрес: Российская Федерация, город Москва, вн.тер.г. муниципальный округ Донской, шоссе Загородное, земельный участок 18А
Площадь: 41 199.00 м²
ВРИ: ЭКСПЛУАТАЦИИ СУЩЕСТВУЮЩИХ ЗДАНИЙ И СООРУЖЕНИЙ БОЛЬНИЦЫ...
Форма собственности: Государственная субъекта РФ
Кадастровая стоимость: 747 360 571.74 руб. (на 2025-01-01)
```

**Объектов на участке:** 22

### Примеры объектов:

**1. Здание (77:05:0001016:1005)**
```
Тип: Здание
Назначение: Нежилое
Площадь: 3 504.40 м²
Этажей: 2
Материал стен: Кирпичные
Год постройки: 1905
Кадастровая стоимость: 509 983 872.61 руб. (на 2026-01-01)
Удельная стоимость: 145 537.88 руб/м²
```

**2. Здание (77:05:0001016:1007)**
```
Тип: Здание
Назначение: Нежилое
Площадь: 14 596.90 м²
Этажей: 2
Материал стен: Кирпичные
Год постройки: 1892
Кадастровая стоимость: 1 043 431 954.33 руб. (на 2026-01-01)
Удельная стоимость: 71 480.88 руб/м²
```

---

## 🔑 Ключевые находки

### 1. API Endpoints

**Поиск (участки и объекты):**
```
GET /api/geoportal/v2/search/geoportal
Параметры:
  - thematicSearchId: 1
  - query: {кадастровый номер}
  - CRS: EPSG:4326
```

**Список объектов на участке:**
```
GET /api/geoportal/v1/tab-group-data
Параметры:
  - tabClass: objectsList
  - categoryId: 36368 (участки) или 36369 (объекты)
  - geomId: {feature.id}
```

### 2. Структура данных

**Для участков и объектов одинаковая:**
```json
{
  "data": {
    "features": [{
      "id": 150334046,
      "properties": {
        "category": 36368,
        "options": {
          "cad_num": "77:05:0001016:22",
          "land_record_type": "Земельный участок",
          "land_record_area": 41199,
          ...
        }
      }
    }]
  }
}
```

### 3. Поля для парсинга

**Участки (land_record_*):**
- `land_record_type` - тип ("Земельный участок")
- `land_record_subtype` - подтип ("Землепользование")
- `land_record_area` или `specified_area` - площадь
- `readable_address` - адрес
- `permitted_use_established_by_document` - ВРИ
- `ownership_type` - форма собственности
- `cost_value` - кадастровая стоимость

**Объекты (build_record_*):**
- `build_record_type_value` - тип ("Здание")
- `build_record_area` - площадь
- `purpose` - назначение ("Нежилое")
- `floors` - этажность
- `underground_floors` - подземных этажей
- `materials` - материал стен
- `year_built` - год постройки
- `cultural_heritage_val` - культурное наследие

### 4. Важные моменты

**geomId для объектов:**
```python
# Правильно:
geom_id = feature['id']

# Неправильно:
geom_id = feature['properties']['interactionId']
```

**Все данные уже в search API:**
- Дополнительный запрос tab-group-data НЕ нужен для получения данных объекта
- tab-group-data используется только для получения СПИСКА объектов на участке
- Все характеристики объекта уже есть в search API response

---

## 🧪 Тестирование

### Базовые тесты

```bash
# Тест search API
python test_real_api.py "77:05:0001016:22"

# Тест получения списка объектов
python test_tab_group_data.py

# Тест детальных данных объектов
python test_object_details.py "77:05:0001016:1037"
```

### Полный workflow

```bash
# Быстрый тест (только список объектов)
python test_full_workflow.py

# Полный тест (с загрузкой всех объектов)
python test_full_workflow.py --full

# Тест конкретного участка
python test_full_workflow.py "77:06:0002008:40" --full
```

---

## 📈 Производительность

### Время выполнения

| Операция | Время |
|----------|-------|
| Поиск участка | ~0.3 сек |
| Получение списка объектов | ~1 сек |
| Получение данных 1 объекта | ~0.5 сек |
| **Участок + 22 объекта** | **~12 сек** |

### Оптимизация

Можно ускорить через параллельные запросы:
```python
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    objects_data = list(executor.map(fetch_object, objects_list))
```

Ожидаемое ускорение: **~3-5x**

---

## 📁 Структура проекта

```
pkk-parser/
├── api_client.py          ✅ Основной API клиент
├── models.py              ✅ Модели данных
├── config.py              ✅ Конфигурация
│
├── test_real_api.py       ✅ Тест search API
├── test_tab_group_data.py ✅ Тест списка объектов
├── test_object_details.py ✅ Тест детальных данных
├── test_full_workflow.py  ✅ Полный workflow
│
├── API_WORKING.md         📄 Документация API
├── OBJECTS_API_READY.md   📄 Документация объектов
├── FULL_WORKFLOW_READY.md 📄 Документация workflow
└── COMPLETE.md            📄 Финальная документация (этот файл)
```

---

## ✅ Excel Экспорт (ГОТОВО!)

### Строгий шаблон реализован

**Файл:** `excel_export.py`

**Структура:**
- **Строка 1:** Группировка (объединенные ячейки)
  - B1-H1: "Сведения о земельном участке"
  - I1-U1: "Сведения об объектах расположенных на земельных участках"
- **Строка 2:** Заголовки колонок (A-U)
- **Строки 3+:** Данные объектов

**Колонки:**
- A: Кадастровый номер объекта недвижимости
- B-H: Данные участка (дублируются для каждого объекта)
- I-U: Данные объекта недвижимости

**Использование:**
```python
from excel_export import create_excel_with_template

create_excel_with_template([parse_result], "output.xlsx")
```

### Поддержка разных типов объектов

Парсер корректно обрабатывает:
- **Здания** (`build_record_*`): площадь, этажность, материал стен
- **Сооружения** (`object_type_value`, `params_*`): назначение, год ввода
- **Помещения** (`realty_estate_type`, `object_record_*`): площадь, назначение

## 🎯 Следующие шаги

### 1. Интеграция в main.py

Обновить основной скрипт для использования нового API:
```python
# Было (Selenium):
parcel_data = scraper.get_parcel_info(cadastral_number)

# Стало (API):
result = client.get_full_parcel_info_with_objects(cadastral_number)
parse_result = ParseResult(
    cadastral_number=cadastral_number,
    parcel=result['parcel_data'],
    objects=result['objects_data'],
    status="Успешно"
)

# Excel экспорт
from excel_export import create_excel_with_template
create_excel_with_template([parse_result], "output.xlsx")
```

### 2. Пакетная обработка

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

cadastral_numbers = ["77:05:0001016:22", "77:06:0002008:40", ...]

client = NSPDAPIClient()
results = []

for cn in cadastral_numbers:
    result = client.get_full_parcel_info_with_objects(cn)
    parse_result = ParseResult(
        cadastral_number=cn,
        parcel=result['parcel_data'],
        objects=result['objects_data'],
        status="Успешно"
    )
    results.append(parse_result)

create_excel_with_template(results, "all_results.xlsx")
client.close()
```

### 3. Опции командной строки

```bash
python main.py input.txt --output results.xlsx --with-objects
```

---

## ✅ Проверочный список

- ✅ API клиент работает
- ✅ Обход 403 Forbidden (правильные заголовки)
- ✅ Поиск участков работает
- ✅ Получение списка объектов работает
- ✅ Получение данных объектов работает
- ✅ Парсинг участков корректный
- ✅ Парсинг объектов корректный (здания, сооружения, помещения)
- ✅ Модели готовы для Excel
- ✅ Excel экспорт по строгому шаблону
- ✅ Тесты созданы и работают
- ✅ Документация написана
- ✅ Полный workflow протестирован (22 объекта)
- ⏭️ Интеграция в main.py
- ⏭️ Пакетная обработка
- ⏭️ Параллельные запросы (опционально)

---

## 📞 Использованные API

**Base URL:** `https://nspd.gov.ru`

**Endpoints:**
1. `/api/geoportal/v2/search/geoportal` - поиск
2. `/api/geoportal/v1/tab-group-data` - список объектов

**Заголовки (критично!):**
```
origin: https://nspd.gov.ru
referer: https://nspd.gov.ru/map?thematic=PKK
user-agent: Mozilla/5.0 ...
```

---

**Дата завершения:** 2026-03-23
**Статус:** ✅ Production Ready
**Версия:** 1.0.0
