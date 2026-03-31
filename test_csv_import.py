#!/usr/bin/env python3
"""
Тест функции импорта CSV
"""
import sys
import os

# Импортируем класс GUI для использования метода парсинга
from gui_app import NSPDParserGUI
import tkinter as tk


def test_csv_parsing():
    """Тест парсинга различных форматов CSV"""

    print("=" * 80)
    print("ТЕСТ ПАРСИНГА CSV ФАЙЛОВ")
    print("=" * 80)
    print()

    # Создаём временный экземпляр GUI для использования методов
    root = tk.Tk()
    root.withdraw()  # Скрываем окно
    app = NSPDParserGUI(root)

    # Тестовые файлы
    test_files = [
        ("test_cadastral_simple.csv", "Простой список номеров"),
        ("test_cadastral_with_header.csv", "CSV с заголовком (запятая)"),
        ("test_cadastral_semicolon.csv", "CSV с заголовком (точка с запятой)"),
    ]

    all_passed = True

    for filename, description in test_files:
        print(f"{'─' * 80}")
        print(f"Тест: {description}")
        print(f"Файл: {filename}")
        print(f"{'─' * 80}")

        if not os.path.exists(filename):
            print(f"❌ ОШИБКА: Файл не найден!")
            all_passed = False
            print()
            continue

        try:
            # Парсим файл
            cadastral_numbers = app._parse_csv_file(filename)

            if cadastral_numbers:
                print(f"✅ Успешно! Найдено номеров: {len(cadastral_numbers)}")
                print()
                print("Распознанные номера:")
                for idx, num in enumerate(cadastral_numbers, 1):
                    print(f"  {idx}. {num}")
                print()

                # Проверка валидности
                invalid = [num for num in cadastral_numbers if not app._is_valid_cadastral_number(num)]
                if invalid:
                    print(f"⚠️  ВНИМАНИЕ: Найдены невалидные номера: {invalid}")
                    all_passed = False
                else:
                    print("✅ Все номера валидны")

            else:
                print(f"❌ ОШИБКА: Номера не найдены!")
                all_passed = False

        except Exception as e:
            print(f"❌ ОШИБКА: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

        print()

    print("=" * 80)
    if all_passed:
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ!")
    print("=" * 80)
    print()

    root.destroy()

    return all_passed


if __name__ == "__main__":
    success = test_csv_parsing()
    sys.exit(0 if success else 1)
