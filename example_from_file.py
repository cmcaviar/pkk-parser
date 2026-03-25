"""
Пример 3: Обработка списка номеров из текстового файла

Подготовка:
    1. Создайте файл cadastral_numbers.txt
    2. Запишите в него кадастровые номера (по одному на строку)

Использование:
    python example_from_file.py
"""
from api_client import NSPDAPIClient
from models import ParseResult
from excel_export import create_excel_with_template

# ===== НАСТРОЙКИ =====
INPUT_FILE = "cadastral_numbers.txt"  # Файл со списком номеров
OUTPUT_FILE = "results.xlsx"          # Результат
# =====================

def read_cadastral_numbers(file_path):
    """Читает кадастровые номера из файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Читаем строки, убираем пробелы, пропускаем пустые
            numbers = [line.strip() for line in f if line.strip()]
        return numbers
    except FileNotFoundError:
        print(f"❌ Файл не найден: {file_path}")
        print(f"\nСоздайте файл {file_path} и добавьте кадастровые номера.")
        print("Пример содержимого:")
        print("  77:05:0001016:22")
        print("  77:06:0002008:40")
        return None
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return None


def main():
    print("=" * 80)
    print("ОБРАБОТКА НОМЕРОВ ИЗ ФАЙЛА")
    print("=" * 80)

    # Читаем номера из файла
    print(f"\n📖 Чтение файла {INPUT_FILE}...")
    cadastral_numbers = read_cadastral_numbers(INPUT_FILE)

    if not cadastral_numbers:
        return

    print(f"✅ Найдено номеров: {len(cadastral_numbers)}")
    print(f"\nСписок:")
    for idx, cn in enumerate(cadastral_numbers, 1):
        print(f"   {idx}. {cn}")

    # Обрабатываем
    client = NSPDAPIClient()
    results = []
    success_count = 0
    error_count = 0

    try:
        for idx, cn in enumerate(cadastral_numbers, 1):
            print(f"\n{'─' * 80}")
            print(f"[{idx}/{len(cadastral_numbers)}] {cn}")
            print(f"{'─' * 80}")

            try:
                result = client.get_full_parcel_info_with_objects(cn)

                parse_result = ParseResult(
                    cadastral_number=cn,
                    parcel=result['parcel_data'],
                    objects=result['objects_data'],
                    status="Успешно"
                )

                print(f"✅ Объектов: {len(parse_result.objects)}")
                results.append(parse_result)
                success_count += 1

            except Exception as e:
                print(f"❌ {e}")
                results.append(ParseResult(
                    cadastral_number=cn,
                    status="Ошибка",
                    error=str(e)
                ))
                error_count += 1

        # Создаем Excel
        print(f"\n{'=' * 80}")
        print("📝 Создание Excel файла...")
        create_excel_with_template(results, OUTPUT_FILE)

        print(f"\n{'=' * 80}")
        print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print(f"{'=' * 80}")
        print(f"\n📊 Статистика:")
        print(f"   Всего: {len(cadastral_numbers)}")
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
