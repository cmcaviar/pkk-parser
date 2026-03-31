"""
Пример 1: Обработка одного участка

Использование:
    python example_single.py
"""
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# ===== НАСТРОЙКИ =====
CADASTRAL_NUMBER = "77:05:0001016:22"  # Измените на свой кадастровый номер
OUTPUT_FILE = "output.xlsx"             # Имя выходного файла
# =====================

def main():
    print("=" * 80)
    print("ОБРАБОТКА ОДНОГО УЧАСТКА")
    print("=" * 80)

    client = NSPDAPIClient()

    try:
        print(f"\n📍 Кадастровый номер: {CADASTRAL_NUMBER}")
        print("⏳ Загрузка данных...")

        # Получаем все данные (участок + объекты)
        result = client.get_full_parcel_info_with_objects(CADASTRAL_NUMBER)

        # Формируем результат
        parse_result = ParseResult(
            cadastral_number=CADASTRAL_NUMBER,
            parcel=result['parcel_data'],
            objects=result['objects_data'],
            status="Успешно"
        )

        # Выводим информацию (с проверкой на None)
        print(f"\n✅ Участок загружен:")
        if parse_result.parcel:
            print(f"   Адрес: {parse_result.parcel.address or 'не указан'}")
            print(f"   Площадь: {parse_result.parcel.area or 'не указана'}")
            print(f"   Стоимость: {parse_result.parcel.cadastral_value or 'не указана'}")
        else:
            print(f"   Данные участка отсутствуют")
        print(f"\n✅ Объектов на участке: {len(parse_result.objects)}")

        # Создаем Excel
        print(f"\n📝 Создание Excel файла...")
        create_excel_with_template([parse_result], OUTPUT_FILE)

        print(f"\n{'=' * 80}")
        print("✅ ГОТОВО!")
        print(f"{'=' * 80}")
        print(f"\n📄 Файл сохранен: {OUTPUT_FILE}")
        print(f"📊 Строк в Excel: {len(parse_result.objects)}")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    main()
