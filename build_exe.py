#!/usr/bin/env python3
"""
Скрипт для сборки .exe файла с помощью PyInstaller
Запускать на Windows!
"""
import PyInstaller.__main__
import os
import sys

def build_exe():
    """Сборка .exe файла"""

    print("=" * 80)
    print("СБОРКА STANDALONE .EXE ФАЙЛА")
    print("=" * 80)
    print()

    # Проверяем что мы на Windows
    if sys.platform != 'win32':
        print("⚠️  ВНИМАНИЕ: Этот скрипт должен запускаться на Windows!")
        print("   На текущей платформе:", sys.platform)
        print()
        response = input("Продолжить всё равно? (y/n): ")
        if response.lower() != 'y':
            print("Сборка отменена.")
            return

    # Параметры сборки
    app_name = "nspd_parser"
    main_script = "gui_app.py"

    # Проверяем наличие главного скрипта
    if not os.path.exists(main_script):
        print(f"❌ Ошибка: Не найден файл {main_script}")
        return

    print(f"📦 Начинаем сборку: {app_name}.exe")
    print(f"📝 Главный скрипт: {main_script}")
    print()

    # Параметры для PyInstaller
    pyinstaller_args = [
        main_script,                    # Главный скрипт
        '--name=' + app_name,           # Имя exe файла
        '--onefile',                     # Собрать в один файл
        '--windowed',                    # Без консоли (GUI приложение)
        '--clean',                       # Очистить временные файлы

        # Добавляем необходимые модули
        '--hidden-import=requests',
        '--hidden-import=openpyxl',
        '--hidden-import=urllib3',

        # Иконка (если есть)
        # '--icon=icon.ico',

        # Добавляем файлы конфигурации если нужны
        # '--add-data=config.py;.',
    ]

    print("🔧 Параметры PyInstaller:")
    for arg in pyinstaller_args:
        print(f"   {arg}")
    print()

    try:
        print("⏳ Запуск PyInstaller...")
        print("   Это может занять несколько минут...")
        print()

        # Запускаем PyInstaller
        PyInstaller.__main__.run(pyinstaller_args)

        print()
        print("=" * 80)
        print("✅ СБОРКА ЗАВЕРШЕНА!")
        print("=" * 80)
        print()
        print(f"📁 Готовый .exe файл находится в: dist/{app_name}.exe")
        print()
        print("📋 Следующие шаги:")
        print("   1. Найдите файл: dist/nspd_parser.exe")
        print("   2. Протестируйте его на этом компьютере")
        print("   3. Скопируйте на другой Windows компьютер для проверки")
        print()
        print("💡 Размер файла: ~50-70 МБ (включает Python + все библиотеки)")
        print("💡 Файл полностью автономный - не требует Python на целевом компьютере")
        print()

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ОШИБКА СБОРКИ!")
        print("=" * 80)
        print()
        print(f"Ошибка: {e}")
        print()
        print("Возможные причины:")
        print("   1. PyInstaller не установлен: pip install pyinstaller")
        print("   2. Не хватает зависимостей: pip install -r requirements.txt")
        print("   3. Проблемы с правами доступа")
        print()
        return


def clean_build_files():
    """Очистка временных файлов сборки"""
    import shutil

    print("🧹 Очистка временных файлов...")

    dirs_to_remove = ['build', 'dist', '__pycache__']
    files_to_remove = ['nspd_parser.spec']

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"   ✅ Удалена папка: {dir_name}")
            except Exception as e:
                print(f"   ⚠️  Не удалось удалить {dir_name}: {e}")

    for file_name in files_to_remove:
        if os.path.exists(file_name):
            try:
                os.remove(file_name)
                print(f"   ✅ Удалён файл: {file_name}")
            except Exception as e:
                print(f"   ⚠️  Не удалось удалить {file_name}: {e}")

    print("✅ Очистка завершена")


if __name__ == "__main__":
    print()

    # Проверяем установлен ли PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("❌ PyInstaller не установлен!")
        print()
        print("Установите его командой:")
        print("   pip install pyinstaller")
        print()
        sys.exit(1)

    # Меню
    print("Выберите действие:")
    print("   1. Собрать .exe файл")
    print("   2. Очистить временные файлы")
    print("   3. Собрать и очистить временные файлы")
    print("   0. Выход")
    print()

    choice = input("Ваш выбор (1-3): ").strip()

    if choice == "1":
        build_exe()
    elif choice == "2":
        clean_build_files()
    elif choice == "3":
        build_exe()
        print()
        clean_build_files()
    elif choice == "0":
        print("Выход.")
    else:
        print("Неверный выбор!")
