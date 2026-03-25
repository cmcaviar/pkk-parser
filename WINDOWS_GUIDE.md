# 🪟 Инструкция для Windows

Пошаговое руководство по использованию парсера НСПД на Windows.

---

## 📋 Что нужно установить

### 1. Python 3.8 или новее

**Проверьте, установлен ли Python:**

```cmd
python --version
```

Если Python не установлен или версия старше 3.8:

1. Скачайте Python с официального сайта: https://www.python.org/downloads/
2. Запустите установщик
3. **ВАЖНО:** Поставьте галочку **"Add Python to PATH"**
4. Нажмите "Install Now"

**Проверка установки:**

```cmd
python --version
pip --version
```

---

## 🚀 Установка парсера

### Шаг 1: Скопируйте файлы проекта

Скопируйте папку `pkk-parser` на ваш компьютер, например в:
```
C:\Users\ВашеИмя\pkk-parser
```

### Шаг 2: Откройте командную строку

1. Нажмите `Win + R`
2. Введите `cmd` и нажмите Enter
3. Перейдите в папку проекта:

```cmd
cd C:\Users\ВашеИмя\pkk-parser
```

### Шаг 3: Установите зависимости

```cmd
pip install -r requirements.txt
```

Будут установлены:
- `requests` - для работы с API
- `openpyxl` - для создания Excel файлов

**Если возникает ошибка:**

Попробуйте:
```cmd
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 🧪 Тестирование

### Базовый тест

```cmd
python test_api.py
```

**Результат:** Загрузит тестовый участок и 5 объектов с полным выводом всех данных.

### Тест другого участка

```cmd
python test_api.py 77:06:0002008:40
```

### Тест с указанием количества объектов

```cmd
python test_api.py 77:05:0001016:22 10
```

---

## 💻 Использование в Python

### Вариант 1: Один участок → Excel

Создайте файл `example.py`:

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# Кадастровый номер участка
cadastral_number = "77:05:0001016:22"

# Создаем клиент
client = NSPDAPIClient()

try:
    print(f"Загрузка данных участка {cadastral_number}...")

    # Получаем все данные (участок + объекты)
    result = client.get_full_parcel_info_with_objects(cadastral_number)

    # Формируем результат
    parse_result = ParseResult(
        cadastral_number=cadastral_number,
        parcel=result['parcel_data'],
        objects=result['objects_data'],
        status="Успешно"
    )

    print(f"Участок: {parse_result.parcel.address}")
    print(f"Объектов: {len(parse_result.objects)}")

    # Создаем Excel
    output_file = "output.xlsx"
    create_excel_with_template([parse_result], output_file)

    print(f"\n✅ Готово! Файл сохранен: {output_file}")

except Exception as e:
    print(f"❌ Ошибка: {e}")

finally:
    client.close()
```

Запустите:
```cmd
python example.py
```

### Вариант 2: Несколько участков → Excel

Создайте файл `batch_example.py`:

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# Список кадастровых номеров
cadastral_numbers = [
    "77:05:0001016:22",
    "77:06:0002008:40",
    # Добавьте свои номера
]

client = NSPDAPIClient()
results = []

try:
    for idx, cn in enumerate(cadastral_numbers, 1):
        print(f"\n[{idx}/{len(cadastral_numbers)}] Обработка {cn}...")

        try:
            result = client.get_full_parcel_info_with_objects(cn)

            parse_result = ParseResult(
                cadastral_number=cn,
                parcel=result['parcel_data'],
                objects=result['objects_data'],
                status="Успешно"
            )

            print(f"   ✅ Участок загружен, объектов: {len(parse_result.objects)}")
            results.append(parse_result)

        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            results.append(ParseResult(
                cadastral_number=cn,
                status="Ошибка",
                error=str(e)
            ))

    # Создаем общий Excel файл
    output_file = "all_parcels.xlsx"
    create_excel_with_template(results, output_file)

    print(f"\n✅ Готово!")
    print(f"Обработано участков: {len(results)}")
    print(f"Файл сохранен: {output_file}")

except Exception as e:
    print(f"❌ Критическая ошибка: {e}")

finally:
    client.close()
```

Запустите:
```cmd
python batch_example.py
```

### Вариант 3: Чтение номеров из текстового файла

Создайте файл `cadastral_numbers.txt`:
```
77:05:0001016:22
77:06:0002008:40
77:01:0005016:3275
```

Создайте файл `process_from_file.py`:

```python
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# Читаем номера из файла
input_file = "cadastral_numbers.txt"
output_file = "results.xlsx"

print(f"Чтение номеров из {input_file}...")

with open(input_file, 'r', encoding='utf-8') as f:
    cadastral_numbers = [line.strip() for line in f if line.strip()]

print(f"Найдено номеров: {len(cadastral_numbers)}")

client = NSPDAPIClient()
results = []

try:
    for idx, cn in enumerate(cadastral_numbers, 1):
        print(f"\n[{idx}/{len(cadastral_numbers)}] {cn}...")

        try:
            result = client.get_full_parcel_info_with_objects(cn)

            parse_result = ParseResult(
                cadastral_number=cn,
                parcel=result['parcel_data'],
                objects=result['objects_data'],
                status="Успешно"
            )

            print(f"   ✅ Объектов: {len(parse_result.objects)}")
            results.append(parse_result)

        except Exception as e:
            print(f"   ❌ {e}")
            results.append(ParseResult(
                cadastral_number=cn,
                status="Ошибка",
                error=str(e)
            ))

    create_excel_with_template(results, output_file)
    print(f"\n✅ Файл сохранен: {output_file}")

finally:
    client.close()
```

Запустите:
```cmd
python process_from_file.py
```

---

## 📊 Формат Excel файла

Excel создается по строгому шаблону:

**Строка 1:** Группировка
- B-H: "Сведения о земельном участке"
- I-U: "Сведения об объектах..."

**Строка 2:** Заголовки (A-U, 21 колонка)

**Строки 3+:** Данные
- 1 строка = 1 объект
- Данные участка дублируются в каждой строке

---

## ⚙️ Настройки

Если нужно изменить настройки (задержки, retry и т.д.), отредактируйте файл `config.py`:

```python
class NSPDConfig:
    # Количество повторных попыток при ошибке
    MAX_RETRIES = 3

    # Задержка между запросами (секунды)
    RETRY_DELAY = 2
```

---

## 🐛 Решение проблем

### Ошибка "python не является внутренней командой"

**Решение:** Python не добавлен в PATH.

1. Найдите где установлен Python (обычно `C:\Users\ВашеИмя\AppData\Local\Programs\Python\Python3XX`)
2. Добавьте в PATH:
   - Откройте "Панель управления" → "Система" → "Дополнительные параметры системы"
   - "Переменные среды"
   - В "Path" добавьте путь к Python

Или переустановите Python с галочкой "Add Python to PATH".

### Ошибка "ModuleNotFoundError: No module named 'requests'"

**Решение:** Не установлены зависимости.

```cmd
pip install requests openpyxl
```

### Ошибка 403 Forbidden

**Решение:** Это нормально, в коде есть retry логика. Если ошибка повторяется постоянно - попробуйте позже.

### SSL ошибки

Иногда возникают временные SSL ошибки - это нормально, код автоматически повторит запрос.

### Кириллица отображается неправильно

Убедитесь, что:
1. Python скрипт сохранен в кодировке UTF-8
2. При чтении файлов используется `encoding='utf-8'`

---

## 📁 Структура файлов

После установки у вас должны быть:

```
C:\Users\ВашеИмя\pkk-parser\
├── api_client.py         # API клиент
├── models.py             # Модели данных
├── config.py             # Конфигурация
├── excel_export.py       # Экспорт в Excel
├── test_api.py           # Тест
├── requirements.txt      # Зависимости
├── README.md             # Документация
├── COMPLETE.md           # Техническая документация
└── WINDOWS_GUIDE.md      # Эта инструкция

# Ваши файлы:
├── example.py            # Ваш скрипт (создаете сами)
├── cadastral_numbers.txt # Список номеров (создаете сами)
└── output.xlsx           # Результат (создается автоматически)
```

---

## 🎯 Быстрый старт (кратко)

```cmd
# 1. Установка
cd C:\Users\ВашеИмя\pkk-parser
pip install -r requirements.txt

# 2. Тест
python test_api.py

# 3. Создайте example.py (скопируйте код из "Вариант 1" выше)

# 4. Запустите
python example.py

# 5. Откройте output.xlsx
```

---

## 💡 Полезные команды Windows

```cmd
# Посмотреть текущую папку
cd

# Перейти в папку
cd C:\путь\к\папке

# Показать содержимое папки
dir

# Запустить Python скрипт
python script.py

# Показать версию Python
python --version

# Показать установленные пакеты
pip list

# Обновить pip
python -m pip install --upgrade pip
```

---

## ✅ Готово!

Теперь вы можете использовать парсер НСПД на Windows! 🎉

Если возникнут вопросы - смотрите README.md и COMPLETE.md для дополнительной информации.
