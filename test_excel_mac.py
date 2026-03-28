#!/usr/bin/env python3
"""
Тест интеграции с Excel на macOS
Запускается из Terminal, работает с открытым Excel файлом
"""
import xlwings as xw
from excel_integration import process_from_excel


def main():
    print("=" * 80)
    print("ТЕСТ EXCEL ИНТЕГРАЦИИ НА macOS")
    print("=" * 80)

    print("\n📋 Инструкция:")
    print("1. Откройте Excel")
    print("2. Создайте новый файл или откройте существующий")
    print("3. Впишите кадастровые номера в колонку A (начиная с A2)")
    print("   Пример:")
    print("   A2: 77:05:0001016:22")
    print("   A3: 77:06:0002008:40")
    print("\n4. Когда будете готовы, нажмите Enter...")

    input()

    try:
        # Получаем активную книгу Excel
        print("\n⏳ Подключение к Excel...")

        try:
            wb = xw.books.active
        except Exception:
            print("❌ Не найден открытый Excel файл!")
            print("\nОткройте Excel и попробуйте снова.")
            return

        sheet = wb.sheets.active

        print(f"✅ Подключено к файлу: {wb.name}")
        print(f"✅ Активный лист: {sheet.name}")

        # Проверяем есть ли данные в колонке A
        test_value = sheet.range('A2').value
        if not test_value:
            print("\n⚠️  Колонка A пуста!")
            print("Впишите хотя бы один кадастровый номер в A2 и запустите снова.")
            return

        print(f"\n📍 Найден номер в A2: {test_value}")

        # Запускаем обработку
        print("\n" + "=" * 80)
        print("ЗАПУСК ОБРАБОТКИ")
        print("=" * 80)

        process_from_excel(sheet)

        print("\n" + "=" * 80)
        print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print("=" * 80)
        print("\nПроверьте Excel файл - данные должны появиться в колонках A-U")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\nОтладочная информация:")
        import traceback
        traceback.print_exc()


def test_simple():
    """
    Простой тест: создает новый Excel файл и обрабатывает один номер
    """
    print("=" * 80)
    print("ПРОСТОЙ ТЕСТ: Создание нового файла")
    print("=" * 80)

    try:
        # Создаем новую книгу
        print("\n⏳ Создание нового Excel файла...")
        wb = xw.Book()
        sheet = wb.sheets[0]

        # Записываем тестовый номер
        print("✅ Записываем тестовый номер: 77:05:0001016:22")
        sheet.range('A2').value = '77:05:0001016:22'

        # Запускаем обработку
        print("\n⏳ Запуск обработки...")
        process_from_excel(sheet)

        print("\n✅ Готово!")
        print("Excel файл остался открытым - можете посмотреть результат")
        print("\nЧтобы сохранить файл:")
        print("  File → Save As...")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--simple':
        # Простой тест с созданием нового файла
        test_simple()
    else:
        # Работа с существующим открытым файлом
        main()
