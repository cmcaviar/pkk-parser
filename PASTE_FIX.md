# 🔧 Исправление вставки в GUI приложении

## Проблема

При попытке вставить текст (Ctrl+V / Cmd+V) в текстовое поле GUI приложения вставка не работала из-за конфликта с placeholder.

## Решение

### Изменения в `gui_app.py`:

#### 1. Добавлена переменная состояния placeholder
```python
self.placeholder_text = "Пример:\n77:05:0001016:22\n77:06:0002008:40\n77:01:0005016:3275"
self.is_placeholder_active = True
```

Теперь приложение отслеживает активен ли placeholder, вместо проверки содержимого текста.

#### 2. Добавлены обработчики для вставки
```python
# Обработка вставки (Ctrl+V / Cmd+V)
self.text_input.bind("<Control-v>", self._on_paste)  # Windows/Linux
self.text_input.bind("<Command-v>", self._on_paste)  # macOS
```

#### 3. Добавлен обработчик нажатия клавиш
```python
self.text_input.bind("<Key>", self._on_input_key)
```

Удаляет placeholder при начале печати (но игнорирует служебные клавиши Shift, Ctrl, Alt, Command).

#### 4. Новый метод `_on_paste()`
```python
def _on_paste(self, event):
    """Обработка вставки (Ctrl+V / Cmd+V)"""
    if self.is_placeholder_active:
        # Удаляем placeholder перед вставкой
        self.text_input.delete("1.0", tk.END)
        self.text_input.config(fg="black")
        self.is_placeholder_active = False
    # Tkinter сам обработает вставку после нашего обработчика
    return None  # Продолжить стандартную обработку
```

#### 5. Новый метод `_on_input_key()`
```python
def _on_input_key(self, event):
    """Обработка нажатия клавиш - удаляет placeholder"""
    if self.is_placeholder_active and event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Command']:
        self.text_input.delete("1.0", tk.END)
        self.text_input.config(fg="black")
        self.is_placeholder_active = False
```

#### 6. Обновлены существующие методы

- `_on_input_focus_in()` - использует `is_placeholder_active`
- `_on_input_focus_out()` - использует `is_placeholder_active`
- `_on_clear_click()` - восстанавливает placeholder и флаг
- `_on_process_click()` - проверяет `is_placeholder_active` вместо содержимого

## Результат

✅ **Вставка теперь работает корректно:**
- Ctrl+V на Windows/Linux
- Cmd+V на macOS
- Placeholder автоматически удаляется перед вставкой
- Вставленный текст отображается чёрным цветом (не серым)

## Тестирование

### Тест 1: Простой тест вставки
```bash
python3 test_paste.py
```

Откроется окно с упрощённым тестом вставки.

### Тест 2: Полное GUI приложение
```bash
python3 gui_app.py
```

**Шаги:**
1. Скопируйте текст: `77:05:0001016:22`
2. Кликните в текстовое поле
3. Нажмите Cmd+V (Mac) или Ctrl+V (Windows)
4. Текст должен вставиться, удалив placeholder

## Дополнительные улучшения

### Теперь также работают:

1. **Печать с клавиатуры** - placeholder удаляется при первом нажатии клавиши
2. **Фокус** - placeholder удаляется при получении фокуса (клик в поле)
3. **Очистка** - кнопка "Очистить" восстанавливает placeholder
4. **Проверка** - кнопка "Загрузить" проверяет флаг `is_placeholder_active`

## Совместимость

✅ Windows (Ctrl+V)
✅ Linux (Ctrl+V)
✅ macOS (Cmd+V)

## Влияние на сборку .exe

❌ Никакого влияния - все изменения в Python коде, PyInstaller соберёт как обычно.

## Обновлённые файлы

- ✅ `gui_app.py` - основные исправления
- ✅ `test_paste.py` - новый тестовый скрипт
- ✅ `PASTE_FIX.md` - эта документация

---

## ✅ Готово!

Проблема с вставкой исправлена. Можно тестировать на Mac или собирать .exe на Windows.
