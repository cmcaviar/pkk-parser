#!/usr/bin/env python3
"""
Автоматический запуск всех тестов
"""
import subprocess
import sys
import os


def print_header(text):
    """Красивый заголовок"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_subheader(text):
    """Подзаголовок"""
    print("\n" + "─" * 80)
    print(f"  {text}")
    print("─" * 80)


def run_test(test_name, test_file, description):
    """Запуск одного теста"""
    print_subheader(f"{test_name}: {description}")

    try:
        # Запускаем тест
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Выводим результат
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Проверяем код возврата
        if result.returncode == 0:
            print(f"✅ {test_name} - ПРОЙДЕН")
            return True
        else:
            print(f"❌ {test_name} - ПРОВАЛЕН (код: {result.returncode})")
            return False

    except subprocess.TimeoutExpired:
        print(f"⏱️  {test_name} - ТАЙМАУТ (>30 секунд)")
        return False
    except Exception as e:
        print(f"❌ {test_name} - ОШИБКА: {e}")
        return False


def main():
    """Главная функция"""
    print_header("ЗАПУСК ВСЕХ ТЕСТОВ НСПД ПАРСЕРА")

    print("\n📋 План тестирования:")
    print("  1. Тест импорта CSV")
    print("  2. Тест обработки пустых полей (None)")
    print("  3. Проверка тестовых файлов")
    print()

    # Список тестов (без GUI тестов, т.к. они интерактивные)
    tests = [
        ("Тест 1", "test_csv_import.py", "Импорт CSV файлов"),
        ("Тест 2", "test_none_fields.py", "Обработка пустых полей"),
    ]

    results = []

    # Запускаем все тесты
    for test_name, test_file, description in tests:
        if not os.path.exists(test_file):
            print(f"⚠️  {test_name} - ПРОПУЩЕН (файл {test_file} не найден)")
            results.append(False)
            continue

        success = run_test(test_name, test_file, description)
        results.append(success)

    # Итоговая статистика
    print_header("ИТОГОВЫЕ РЕЗУЛЬТАТЫ")

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n📊 Статистика:")
    print(f"   Всего тестов: {total}")
    print(f"   Пройдено: {passed}")
    print(f"   Провалено: {failed}")
    print()

    # Детальные результаты
    for i, (test_name, test_file, description) in enumerate(tests):
        status = "✅ ПРОЙДЕН" if results[i] else "❌ ПРОВАЛЕН"
        print(f"   {test_name}: {status}")

    print()

    # Интерактивные тесты
    print("─" * 80)
    print("📝 ИНТЕРАКТИВНЫЕ ТЕСТЫ (запустите вручную):")
    print()
    print("  Тест вставки и контекстного меню:")
    print("    python test_paste.py")
    print()
    print("  Основное GUI приложение:")
    print("    python gui_app.py")
    print()
    print("─" * 80)

    # Проверка созданных файлов
    print()
    print("📁 СОЗДАННЫЕ ФАЙЛЫ:")

    files_to_check = [
        "test_none_fields.xlsx",
        "test_cadastral_simple.csv",
        "test_cadastral_with_header.csv",
        "test_cadastral_semicolon.csv",
    ]

    for filename in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"   ✅ {filename} ({size} байт)")
        else:
            print(f"   ❌ {filename} (не найден)")

    print()
    print("=" * 80)

    # Финальный результат
    if all(results):
        print("✅ ВСЕ АВТОМАТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print()
        print("Следующие шаги:")
        print("  1. Запустите: python test_paste.py")
        print("  2. Запустите: python gui_app.py")
        print("  3. Проверьте все функции вручную")
        return 0
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ!")
        print()
        print("Проверьте ошибки выше и исправьте их.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
