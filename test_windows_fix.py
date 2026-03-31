#!/usr/bin/env python3
"""
Тест исправлений для Windows
Проверяет новые функции диагностики и логирования
"""
import logging
import sys
from api_client import NSPDAPIClient

# Настройка логирования для детального вывода
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_windows_fix.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_api_with_diagnostics():
    """
    Тест API клиента с детальной диагностикой
    """
    print("=" * 80)
    print("ТЕСТ ИСПРАВЛЕНИЙ ДЛЯ WINDOWS")
    print("=" * 80)
    print()

    # Проверяем системные настройки прокси
    import os
    print("Проверка системных переменных окружения:")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY', 'no_proxy']
    found_proxy = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ⚠️  {var} = {value}")
            found_proxy = True
    if not found_proxy:
        print("   ✅ Переменные прокси не установлены")
    print()

    # Тестовый кадастровый номер
    test_cn = "77:01:0001003:1926"

    print(f"Тестовый кадастровый номер: {test_cn}")
    print()

    try:
        # Создаём клиент
        print("1. Создание API клиента...")
        client = NSPDAPIClient()
        print("   ✅ Клиент создан")
        print()

        # Получаем полную информацию
        print("2. Запрос данных участка...")
        result = client.get_full_parcel_info_with_objects(test_cn)
        print()

        # Проверяем результат
        print("3. Анализ результата:")
        print(f"   - parcel_data: {result['parcel_data']}")
        print(f"   - objects_data: {len(result['objects_data'])} объектов")
        print()

        if result['parcel_data'] is None:
            print("   ❌ ОШИБКА: parcel_data = None")
            print("   Проверьте логи и папку debug_responses/ для деталей")
        else:
            print("   ✅ Данные участка получены:")
            print(f"      Адрес: {result['parcel_data'].address}")
            print(f"      Площадь: {result['parcel_data'].area}")
            print(f"      Тип: {result['parcel_data'].parcel_type}")

        print()
        print("=" * 80)
        print("ТЕСТ ЗАВЕРШЁН")
        print("=" * 80)
        print()
        print("Проверьте следующие файлы:")
        print("  - test_windows_fix.log - полный лог выполнения")
        print("  - debug_responses/ - проблемные ответы API (если были)")
        print()

        # Закрываем клиент
        client.close()

    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_api_with_diagnostics()
