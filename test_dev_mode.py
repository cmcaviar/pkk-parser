#!/usr/bin/env python3
"""
Тест режима разработчика (dev logging)
"""
import tkinter as tk
from gui_app import NSPDParserGUI


def test_dev_mode():
    """Демонстрация режима разработчика"""
    print("=" * 80)
    print("ТЕСТ РЕЖИМА РАЗРАБОТЧИКА")
    print("=" * 80)
    print()
    print("Инструкция:")
    print("1. Откроется GUI приложение")
    print("2. Включите чекбокс '🔧 Dev логи' внизу")
    print("3. Скопируйте тестовые номера или используйте 'Импорт CSV'")
    print("4. Нажмите '📥 Старт' (если есть доступ к API)")
    print()
    print("В режиме разработчика вы увидите:")
    print("  • [DEBUG] сообщения в логах")
    print("  • Время выполнения API запросов")
    print("  • Типы данных объектов")
    print("  • Детальную информацию об объектах")
    print("  • Информацию об ошибках")
    print()
    print("Также:")
    print("  • Все логи автоматически сохраняются в папку logs/")
    print("  • Кнопка '📄 Экспорт логов' позволяет сохранить логи отдельно")
    print()
    print("Запуск приложения...")
    print()

    root = tk.Tk()
    app = NSPDParserGUI(root)
    root.mainloop()


if __name__ == "__main__":
    test_dev_mode()
