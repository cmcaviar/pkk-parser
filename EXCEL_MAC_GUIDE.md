# 🍎 Использование парсера НСПД в Excel на macOS

Подробная инструкция для работы с парсером через Excel на Mac.

---

## 🎯 Важно знать о Excel на Mac

Excel для Mac **отличается** от Windows версии:

- ✅ **VBA макросы работают** (с некоторыми ограничениями)
- ✅ **xlwings поддерживается**
- ⚠️ Некоторые VBA команды отличаются
- ⚠️ Пути к файлам указываются по-другому

**Хорошая новость:** Наш парсер будет работать!

---

## 📋 Требования

1. **macOS** (любая современная версия)
2. **Microsoft Excel для Mac** (любая версия с поддержкой макросов)
3. **Python 3.8+** (обычно уже установлен на Mac)

---

## ⚙️ Установка (делается один раз)

### Шаг 1: Проверьте Python

Откройте **Terminal** (Cmd + Space → "Terminal"):

```bash
python3 --version
```

Если Python не установлен:
```bash
# Установите через Homebrew (рекомендуется)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python
```

### Шаг 2: Установите зависимости

В Terminal перейдите в папку проекта:

```bash
cd ~/путь/к/pkk-parser

# Установите все зависимости
pip3 install -r requirements.txt

# Или установите вручную
pip3 install requests openpyxl xlwings
```

### Шаг 3: Установите xlwings add-in для Excel

```bash
xlwings addin install
```

Эта команда добавит xlwings в Excel.

### Шаг 4: Перезапустите Excel

После установки xlwings **обязательно** перезапустите Excel!

---

## 📝 Настройка Excel файла

### Способ 1: Создать файл вручную (рекомендуется)

#### 1. Создайте новый Excel файл

1. Откройте Excel
2. Создайте новую книгу
3. **Сохраните как** → Выберите формат **"Книга Excel с поддержкой макросов (.xlsm)"**
4. Сохраните в папку проекта (где лежит `run_from_excel.py`)

#### 2. Добавьте VBA макрос

1. Откройте редактор VBA:
   - **Tools → Macro → Visual Basic Editor**
   - Или нажмите **Alt + F11** (Option + F11)

2. В редакторе VBA:
   - **Insert → Module**

3. Вставьте следующий код:

```vba
Sub LoadNSPDData()
    '
    ' Макрос для загрузки данных НСПД через Python
    ' Версия для macOS
    '

    On Error GoTo ErrorHandler

    ' Показываем статус
    Application.StatusBar = "Запуск Python скрипта..."
    Application.ScreenUpdating = False

    ' Вызываем Python через xlwings
    ' ВАЖНО: Убедитесь что файл находится в той же папке
    RunPython "import sys; sys.path.append('" & ThisWorkbook.Path & "'); import run_from_excel; run_from_excel.load_nspd_data()"

    Application.StatusBar = False
    Application.ScreenUpdating = True

    Exit Sub

ErrorHandler:
    Application.StatusBar = False
    Application.ScreenUpdating = True

    MsgBox "Ошибка:" & vbNewLine & vbNewLine & _
           Err.Description & vbNewLine & vbNewLine & _
           "Убедитесь что:" & vbNewLine & _
           "1. Python установлен" & vbNewLine & _
           "2. xlwings установлен: pip3 install xlwings" & vbNewLine & _
           "3. Файл run_from_excel.py находится в: " & ThisWorkbook.Path, _
           vbCritical, "Ошибка"
End Sub

Sub TestXLWings()
    '
    ' Тест для проверки работы xlwings
    '
    On Error GoTo ErrorHandler

    RunPython "import xlwings as xw; xw.apps.active.alert('xlwings работает на Mac!', title='Успех')"

    Exit Sub

ErrorHandler:
    MsgBox "xlwings не настроен!" & vbNewLine & vbNewLine & _
           "Выполните в Terminal:" & vbNewLine & _
           "pip3 install xlwings" & vbNewLine & _
           "xlwings addin install", _
           vbCritical, "Ошибка"
End Sub
```

4. Сохраните (Cmd + S)
5. Закройте редактор VBA

#### 3. Разрешите выполнение макросов

Excel для Mac спросит при открытии файла с макросами:
- Нажмите **"Включить содержимое"** или **"Enable Macros"**

---

## 🚀 Использование

### 1. Подготовьте данные

В вашем Excel файле:

1. Колонка **A** - для кадастровых номеров
2. Начинайте с **A2** (A1 будет использована для заголовка)

Пример:
```
A1: (пусто - заголовок добавится автоматически)
A2: 77:05:0001016:22
A3: 77:06:0002008:40
A4: 77:01:0005016:3275
```

### 2. Запустите макрос

**Способ 1: Через меню**

1. **Tools → Macro → Macros...** (или Alt + F8)
2. Выберите `LoadNSPDData`
3. Нажмите **Run**

**Способ 2: Создайте кнопку**

1. **Developer → Insert → Button**
   - Если вкладки Developer нет:
     - Excel → Preferences → Ribbon & Toolbar
     - Поставьте галочку "Developer"
2. Нарисуйте кнопку на листе
3. Выберите макрос `LoadNSPDData`
4. Переименуйте кнопку в "Загрузить данные"

Теперь можно просто нажимать кнопку!

### 3. Что происходит

1. Python скрипт читает номера из колонки A (начиная с A2)
2. Для каждого номера:
   - Загружает данные участка
   - Загружает данные всех объектов
   - Записывает в колонки A-U
3. В строке состояния показывается прогресс
4. По завершении появляется окно с результатами

### 4. Результат

- **Строка 1:** Заголовки (A-U, 21 колонка)
- **Строки 2+:** Данные участков и объектов
  - Если на участке 3 объекта → 3 строки
  - Данные участка дублируются для каждого объекта

---

## 🧪 Тестирование

### Тест 1: Проверка xlwings

1. Откройте ваш Excel файл
2. **Tools → Macro → Macros**
3. Выберите `TestXLWings`
4. Нажмите **Run**

**Результат:** Должно появиться окно "xlwings работает на Mac!"

Если появилась ошибка - xlwings не установлен. Вернитесь к шагу установки.

### Тест 2: Обработка одного номера

1. Впишите в **A2**: `77:05:0001016:22`
2. Запустите макрос `LoadNSPDData`
3. Подождите 10-15 секунд
4. Данные должны появиться в колонках A-U

---

## 🔧 Альтернатива: Запуск через Terminal (без VBA)

Если VBA не работает или вы предпочитаете Terminal:

### Создайте тестовый скрипт

Создайте файл `test_excel_mac.py`:

```python
#!/usr/bin/env python3
"""
Тест интеграции с Excel на Mac
Запускается из Terminal
"""
import xlwings as xw
from excel_integration import process_from_excel

def main():
    print("=" * 80)
    print("ТЕСТ EXCEL ИНТЕГРАЦИИ НА macOS")
    print("=" * 80)

    # Открываем Excel файл
    print("\n1. Откройте ваш Excel файл с номерами в колонке A")
    print("2. Нажмите Enter когда будете готовы...")
    input()

    # Получаем активную книгу
    try:
        wb = xw.books.active
        sheet = wb.sheets.active

        print(f"\n✅ Работаем с файлом: {wb.name}")
        print(f"✅ Активный лист: {sheet.name}")

        # Запускаем обработку
        print("\n⏳ Запуск обработки...")
        process_from_excel(sheet)

        print("\n✅ Готово! Проверьте Excel файл")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
```

### Использование:

```bash
# 1. Откройте Excel файл, впишите номера в колонку A

# 2. Запустите скрипт в Terminal:
python3 test_excel_mac.py

# 3. Нажмите Enter когда скрипт попросит

# 4. Данные появятся в Excel
```

---

## 🐛 Решение проблем

### Проблема 1: "xlwings не найден"

**Решение:**
```bash
pip3 install xlwings
xlwings addin install
```

Перезапустите Excel!

### Проблема 2: "RunPython не работает"

**Причина:** xlwings add-in не установлен.

**Решение:**
```bash
# Удалите старый add-in (если был)
xlwings addin remove

# Установите заново
xlwings addin install
```

**Проверка:** В Excel должна появиться вкладка или меню **xlwings**.

### Проблема 3: "Файл run_from_excel.py не найден"

**Причина:** Excel файл и Python скрипты в разных папках.

**Решение:**
1. Убедитесь что `.xlsm` файл в той же папке что и `run_from_excel.py`
2. Или измените путь в VBA коде:
   ```vba
   sys.path.append('/полный/путь/к/pkk-parser')
   ```

### Проблема 4: "Python не найден"

**Решение:** Укажите полный путь к Python в VBA:

```vba
' Найдите путь к Python:
' В Terminal: which python3

' Затем в VBA добавьте перед RunPython:
Dim pythonPath As String
pythonPath = "/usr/local/bin/python3"  ' Ваш путь
```

### Проблема 5: Макросы не запускаются

**Решение:**
1. Excel → Preferences → Security & Privacy
2. Разрешите макросы
3. Перезапустите Excel

---

## 📊 Пример: Полный workflow

### 1. Подготовка (один раз)

```bash
# Terminal
cd ~/Downloads/pkk-parser
pip3 install -r requirements.txt
xlwings addin install
```

### 2. Создание Excel файла

1. Откройте Excel
2. Создайте файл, сохраните как `.xlsm` в папку `pkk-parser`
3. Alt + F11 → Insert → Module → Вставьте VBA код
4. Сохраните

### 3. Использование

1. Впишите номера в колонку A (с A2)
2. Tools → Macro → Macros → LoadNSPDData → Run
3. Подождите
4. Данные появятся в колонках A-U

---

## 💡 Советы для Mac

### 1. Используйте полные пути

В VBA на Mac лучше использовать полные пути:

```vba
' Вместо:
ThisWorkbook.Path

' Используйте:
"/Users/ваше_имя/pkk-parser"
```

### 2. Python 3, а не Python

На Mac команда `python` часто указывает на Python 2. Используйте `python3`:

```bash
python3 --version  # Python 3.x
pip3 install ...   # Установка пакетов
```

### 3. Права доступа

Если Excel не может читать файлы, дайте права:

```bash
chmod +x run_from_excel.py
```

### 4. Альтернатива VBA

Если VBA проблематичен, используйте прямой запуск через Python (см. раздел "Альтернатива" выше).

---

## 📚 Дополнительные материалы

- **README.md** - общая документация
- **EXCEL_GUIDE.md** - инструкция для Windows (для справки)
- **COMPLETE.md** - техническая документация API

---

## ✅ Готово!

Теперь вы можете использовать парсер НСПД прямо из Excel на вашем Mac! 🎉

**Вопросы?**
- Проверьте раздел "Решение проблем"
- Попробуйте альтернативный способ через Terminal
- Используйте `test_excel_mac.py` для отладки
