#!/usr/bin/env python3
"""
Тест GUI приложения на Mac
Запускается для проверки интерфейса перед сборкой .exe на Windows
"""
import sys

print("=" * 80)
print("ТЕСТ GUI ПРИЛОЖЕНИЯ")
print("=" * 80)
print()
print("Этот тест запускает GUI приложение для проверки интерфейса.")
print("Приложение будет работать как и на Windows, но без .exe сборки.")
print()
print("Для полноценного теста:")
print("1. Откроется окно программы")
print("2. Введите тестовый номер: 77:05:0001016:22")
print("3. Нажмите 'Загрузить данные'")
print("4. Выберите где сохранить Excel файл")
print("5. Дождитесь завершения")
print()
print("=" * 80)
print()

try:
    # Импортируем и запускаем GUI приложение
    from gui_app import main

    print("✅ Запуск GUI приложения...")
    print()

    main()

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print()
    print("Убедитесь что установлены все зависимости:")
    print("   pip3 install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
