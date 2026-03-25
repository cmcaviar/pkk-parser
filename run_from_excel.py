"""
Точка входа для запуска из Excel

Этот скрипт вызывается из Excel через xlwings
"""
import xlwings as xw
from excel_integration import process_from_excel


@xw.func
def hello(name):
    """Тестовая функция для проверки работы xlwings"""
    return f"Hello {name}!"


@xw.sub
def load_nspd_data():
    """
    Главная функция для вызова из Excel
    Читает номера из колонки A и загружает данные
    """
    process_from_excel()


if __name__ == "__main__":
    # Если запущен напрямую - вызываем функцию
    load_nspd_data()
