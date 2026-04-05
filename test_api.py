"""
Полноценный тест API НСПД
Проверка всех основных функций парсера
"""
import sys
from api_client import NSPDAPIClient
from models import ParseResult


def print_separator(title=""):
    """Печать разделителя"""
    print("\n" + "=" * 80)
    if title:
        print(f"{title:^80}")
        print("=" * 80)


def test_search_parcel(client: NSPDAPIClient, cadastral_number: str):
    """Тест 1: Поиск земельного участка"""
    print_separator("ТЕСТ 1: ПОИСК ЗЕМЕЛЬНОГО УЧАСТКА")

    print(f"\n📍 Кадастровый номер: {cadastral_number}")

    feature = client.search_cadastral_number(cadastral_number)

    if not feature:
        print("❌ Участок не найден")
        return None

    print("✅ Участок найден")

    # Парсим данные
    parcel = client.parse_parcel_data(feature, cadastral_number)

    # Выводим ВСЕ данные участка (колонки B-H для Excel) с проверкой на None
    print(f"\n📋 ДАННЫЕ УЧАСТКА (колонки B-H в Excel):")
    print(f"   ┌─ A: Кадастровый номер: {cadastral_number}")
    print(f"   │")
    print(f"   ├─ B: Вид объекта недвижимости: {parcel.object_type or '-'}")
    print(f"   ├─ C: Вид земельного участка: {parcel.parcel_type or '-'}")
    print(f"   ├─ D: Адрес: {parcel.address or '-'}")
    print(f"   ├─ E: Площадь декларированная: {parcel.area or '-'}")
    print(f"   ├─ F: Вид разрешенного использования: {parcel.permitted_use or '-'}")
    print(f"   ├─ G: Форма собственности: {parcel.ownership_form or '-'}")
    print(f"   └─ H: Кадастровая стоимость: {parcel.cadastral_value or '-'}")

    return feature, parcel


def test_get_objects_list(client: NSPDAPIClient, feature: dict):
    """Тест 2: Получение списка объектов на участке"""
    print_separator("ТЕСТ 2: СПИСОК ОБЪЕКТОВ НА УЧАСТКЕ")

    feature_id = feature.get('id')
    category_id = feature['properties']['category']

    print(f"\n🔍 Поиск объектов...")
    print(f"   Feature ID: {feature_id}")
    print(f"   Category ID: {category_id}")

    objects_list = client.get_objects_on_parcel(feature_id, category_id)

    if not objects_list:
        print("\n⚠️  Объектов не найдено на участке")
        return []

    print(f"\n✅ Найдено объектов: {len(objects_list)}")

    # Показываем первые 10
    print(f"\n📝 Кадастровые номера объектов (первые 10):")
    for idx, cn in enumerate(objects_list[:10], 1):
        print(f"   {idx}. {cn}")

    if len(objects_list) > 10:
        print(f"   ... и еще {len(objects_list) - 10} объектов")

    return objects_list


def test_get_object_details(client: NSPDAPIClient, objects_list: list, limit: int = 5):
    """Тест 3: Получение детальных данных объектов"""
    print_separator("ТЕСТ 3: ДЕТАЛЬНЫЕ ДАННЫЕ ОБЪЕКТОВ")

    print(f"\n📥 Загрузка данных {min(limit, len(objects_list))} объектов...")

    objects_data = []

    for idx, obj_cn in enumerate(objects_list[:limit], 1):
        print(f"\n{'─' * 80}")
        print(f"ОБЪЕКТ #{idx}")
        print(f"{'─' * 80}")

        obj_feature = client.search_cadastral_number(obj_cn)
        if obj_feature:
            obj_data = client.parse_object_data(obj_feature, obj_cn)
            objects_data.append(obj_data)

            # Выводим ВСЕ данные объекта (колонки I-U для Excel)
            print(f"\n   📦 ДАННЫЕ ОБЪЕКТА (колонки I-U в Excel):")
            print(f"   ┌─ I: Вид объекта недвижимости: {obj_data.object_type}")
            print(f"   ├─ J: Кадастровый номер: {obj_data.cadastral_number}")
            print(f"   ├─ K: Назначение: {obj_data.purpose}")
            print(f"   ├─ L: Площадь общая: {obj_data.area}")
            print(f"   ├─ M: Форма собственности: {obj_data.ownership_form}")
            print(f"   ├─ N: Кадастровая стоимость: {obj_data.cadastral_value}")
            print(f"   ├─ O: Удельный показатель кадастровой стоимости: {obj_data.unit_value}")
            print(f"   ├─ P: Количество этажей (в том числе подземных): {obj_data.floors}")
            print(f"   ├─ Q: Количество подземных этажей: {obj_data.underground_floors}")
            print(f"   ├─ R: Материал стен: {obj_data.wall_material}")
            print(f"   ├─ S: Завершение строительства: {obj_data.completion}")
            print(f"   ├─ T: Ввод в эксплуатацию: {obj_data.commissioning}")
            print(f"   └─ U: Сведения о культурном наследии: {obj_data.cultural_heritage[:80]}{'...' if len(obj_data.cultural_heritage) > 80 else ''}")
        else:
            print(f"\n   ❌ Не удалось загрузить объект {obj_cn}")

    print(f"\n{'═' * 80}")
    print(f"✅ Успешно загружено: {len(objects_data)}/{min(limit, len(objects_list))}")
    print(f"{'═' * 80}")

    return objects_data


def test_create_parse_result(cadastral_number: str, parcel, objects_data: list):
    """Тест 4: Формирование ParseResult"""
    print_separator("ТЕСТ 4: ФОРМИРОВАНИЕ РЕЗУЛЬТАТА")

    print(f"\n📦 Создание ParseResult...")

    parse_result = ParseResult(
        cadastral_number=cadastral_number,
        parcel=parcel,
        objects=objects_data,
        status="Успешно"
    )

    print(f"✅ ParseResult создан:")
    print(f"   Кадастровый номер: {parse_result.cadastral_number}")
    print(f"   Статус: {parse_result.status}")
    print(f"   Участок: {'✅' if parse_result.parcel else '❌'}")
    print(f"   Объектов: {len(parse_result.objects)}")
    print(f"   Временная метка: {parse_result.timestamp}")

    # Проверяем метод to_excel_rows()
    rows = parse_result.to_excel_rows()
    print(f"\n📊 Метод to_excel_rows():")
    print(f"   Сгенерировано строк: {len(rows)}")
    print(f"   Колонок в строке: {len(rows[0]) if rows else 0}")

    if rows:
        print(f"\n📝 Первая строка (пример):")
        first_row = rows[0]
        print(f"   A: {first_row.get('Кадастровый номер объекта недвижимости', 'N/A')}")
        print(f"   B: {first_row.get('Вид объекта недвижимости', 'N/A')}")
        print(f"   I: {first_row.get('Вид объекта недвижимости_obj', 'N/A')}")
        print(f"   J: {first_row.get('Кадастровый номер_obj', 'N/A')}")

    return parse_result


def run_full_test(cadastral_number: str, objects_limit: int = 5):
    """Запуск полного теста"""
    print_separator("🧪 ПОЛНОЦЕННЫЙ ТЕСТ API НСПД")
    print(f"\n📍 Тестовый участок: {cadastral_number}")
    print(f"🔢 Лимит объектов: {objects_limit}")

    client = NSPDAPIClient()

    try:
        # Тест 1: Поиск участка
        result = test_search_parcel(client, cadastral_number)
        if not result:
            print("\n❌ Тест провален: участок не найден")
            return False

        feature, parcel = result

        # Тест 2: Список объектов
        objects_list = test_get_objects_list(client, feature)

        # Тест 3: Детальные данные объектов
        objects_data = []
        if objects_list:
            objects_data = test_get_object_details(client, objects_list, objects_limit)

        # Тест 4: Формирование ParseResult
        parse_result = test_create_parse_result(cadastral_number, parcel, objects_data)

        # Итоговая статистика
        print_separator("✅ ИТОГОВАЯ СТАТИСТИКА")
        print(f"\n✅ Все тесты пройдены успешно!")
        print(f"\n📊 Статистика:")
        print(f"   Участок: ✅ загружен")
        print(f"   Объектов найдено: {len(objects_list)}")
        print(f"   Объектов загружено: {len(objects_data)}")
        print(f"   Строк для Excel: {len(parse_result.to_excel_rows())}")

        return True

    except Exception as e:
        print(f"\n❌ Ошибка во время теста: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        client.close()
        print("\n🔒 Клиент закрыт")


def main():
    """Главная функция"""
    # Параметры по умолчанию
    default_cadastral_number = "77:07:0006004:165"
    default_objects_limit = 5

    # Получаем параметры из командной строки
    cadastral_number = sys.argv[1] if len(sys.argv) > 1 else default_cadastral_number
    objects_limit = int(sys.argv[2]) if len(sys.argv) > 2 else default_objects_limit

    # Запускаем тест
    success = run_full_test(cadastral_number, objects_limit)

    # Возвращаем код выхода
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
