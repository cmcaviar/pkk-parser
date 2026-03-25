# NSPD Parser - Парсер НСПД

Парсер кадастровых данных из API Национальной системы пространственных данных (НСПД)

## 🎯 О проекте

Инструмент для автоматического получения данных о земельных участках и объектах недвижимости через API НСПД (https://nspd.gov.ru).

**Возможности:**
- ✅ Получение данных земельных участков по кадастровому номеру
- ✅ Получение списка объектов на участке (здания, сооружения, помещения)
- ✅ Детальные данные каждого объекта
- ✅ Экспорт в Excel по строгому шаблону

## 📦 Структура проекта

```
pkk-parser/
├── api_client.py       # API клиент НСПД (основной модуль)
├── models.py           # Модели данных (Parcel, RealtyObject, ParseResult)
├── config.py           # Конфигурация (API endpoints, заголовки)
├── excel_export.py     # Экспорт в Excel по шаблону
├── test_api.py         # Полноценный тест всех функций
├── README.md           # Эта документация
└── COMPLETE.md         # Полная техническая документация
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install requests openpyxl
```

### Тестирование

Запустите тест API для проверки работоспособности:

```bash
# Тест с участком по умолчанию (77:05:0001016:22)
python test_api.py

# Тест с конкретным участком
python test_api.py 77:06:0002008:40

# Тест с указанием лимита объектов
python test_api.py 77:05:0001016:22 10
```

**Вывод теста:**
- ✅ Тест 1: Поиск земельного участка
- ✅ Тест 2: Список объектов на участке
- ✅ Тест 3: Детальные данные объектов
- ✅ Тест 4: Формирование ParseResult

## 💻 Использование

### Пример 1: Получение данных участка

```python
from api_client import NSPDAPIClient

client = NSPDAPIClient()

try:
    feature = client.search_cadastral_number("77:05:0001016:22")
    parcel = client.parse_parcel_data(feature, "77:05:0001016:22")

    print(f"Адрес: {parcel.address}")
    print(f"Площадь: {parcel.area}")
    print(f"Стоимость: {parcel.cadastral_value}")
finally:
    client.close()
```

### Пример 2: Участок + все объекты + Excel

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

client = NSPDAPIClient()

try:
    result = client.get_full_parcel_info_with_objects("77:05:0001016:22")

    parse_result = ParseResult(
        cadastral_number="77:05:0001016:22",
        parcel=result['parcel_data'],
        objects=result['objects_data'],
        status="Успешно"
    )

    create_excel_with_template([parse_result], "output.xlsx")
    print("✅ Excel файл создан")
finally:
    client.close()
```

### Пример 3: Пакетная обработка

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

cadastral_numbers = ["77:05:0001016:22", "77:06:0002008:40"]

client = NSPDAPIClient()
results = []

try:
    for cn in cadastral_numbers:
        result = client.get_full_parcel_info_with_objects(cn)
        parse_result = ParseResult(
            cadastral_number=cn,
            parcel=result['parcel_data'],
            objects=result['objects_data'],
            status="Успешно"
        )
        results.append(parse_result)

    create_excel_with_template(results, "all_parcels.xlsx")
finally:
    client.close()
```

## 📊 Структура Excel

**Строка 1:** Группировка
- B-H: "Сведения о земельном участке"
- I-U: "Сведения об объектах расположенных на земельных участках"

**Строка 2:** Заголовки (A-U, 21 колонка)

**Строки 3+:** Данные (1 строка = 1 объект)

## 📚 Документация

- **README.md** - Краткая документация (этот файл)
- **COMPLETE.md** - Полная техническая документация

## ✅ Статус

Production Ready - полностью рабочая версия.
