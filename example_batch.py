"""
Пример 2: Пакетная обработка нескольких участков

Использование:
    python example_batch.py
"""
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# ===== НАСТРОЙКИ =====
CADASTRAL_NUMBERS = [
    "77:05:0001016:22",
    "77:06:0002008:40",
    # Добавьте свои кадастровые номера здесь
]

OUTPUT_FILE = "all_parcels.xlsx"
# =====================

def main():
    print("=" * 80)
    print("ПАКЕТНАЯ ОБРАБОТКА УЧАСТКОВ")
    print("=" * 80)

    print(f"\n📋 Всего участков: {len(CADASTRAL_NUMBERS)}")

    client = NSPDAPIClient()
    results = []
    success_count = 0
    error_count = 0

    try:
        for idx, cn in enumerate(CADASTRAL_NUMBERS, 1):
            print(f"\n{'─' * 80}")
            print(f"[{idx}/{len(CADASTRAL_NUMBERS)}] Обработка {cn}")
            print(f"{'─' * 80}")

            try:
                # Получаем данные
                result = client.get_full_parcel_info_with_objects(cn)

                # Формируем ParseResult
                parse_result = ParseResult(
                    cadastral_number=cn,
                    parcel=result['parcel_data'],
                    objects=result['objects_data'],
                    status="Успешно"
                )

                print(f"✅ Загружено:")
                print(f"   Адрес: {parse_result.parcel.address[:80]}...")
                print(f"   Объектов: {len(parse_result.objects)}")

                results.append(parse_result)
                success_count += 1

            except Exception as e:
                print(f"❌ Ошибка: {e}")

                # Добавляем результат с ошибкой
                results.append(ParseResult(
                    cadastral_number=cn,
                    status="Ошибка",
                    error=str(e)
                ))
                error_count += 1

        # Создаем Excel файл
        print(f"\n{'=' * 80}")
        print("📝 Создание Excel файла...")
        create_excel_with_template(results, OUTPUT_FILE)

        print(f"\n{'=' * 80}")
        print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"{'=' * 80}")
        print(f"\n📊 Статистика:")
        print(f"   Всего участков: {len(CADASTRAL_NUMBERS)}")
        print(f"   Успешно: {success_count}")
        print(f"   Ошибок: {error_count}")
        print(f"\n📄 Файл сохранен: {OUTPUT_FILE}")

    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

    finally:
        client.close()


if __name__ == "__main__":
    main()
