#!/usr/bin/env python3
"""
Тест обработки отсутствующих полей (None)
"""
from models import Parcel, RealtyObject, ParseResult
from excel_export import create_excel_with_template


def test_none_fields():
    """Тест что отсутствующие поля не вызывают ошибок"""

    print("=" * 80)
    print("ТЕСТ ОБРАБОТКИ ОТСУТСТВУЮЩИХ ПОЛЕЙ (None)")
    print("=" * 80)
    print()

    # Тест 1: Участок с отсутствующим адресом
    print("─" * 80)
    print("Тест 1: Участок с отсутствующим адресом")
    print("─" * 80)

    parcel_no_address = Parcel(
        cadastral_number="77:05:0001016:22",
        object_type="Земельный участок",
        parcel_type="Для жилищного строительства",
        address=None,  # Адрес отсутствует!
        area="1500",
        permitted_use="Малоэтажная жилая застройка",
        ownership_form="Частная собственность",
        cadastral_value="5000000"
    )

    # Проверяем безопасный доступ к адресу
    if parcel_no_address.address:
        print(f"   Адрес: {parcel_no_address.address}")
    else:
        print(f"   Адрес: не указан")

    print("✅ Тест 1 пройден")
    print()

    # Тест 2: Участок со всеми полями None
    print("─" * 80)
    print("Тест 2: Участок со всеми полями None")
    print("─" * 80)

    parcel_all_none = Parcel(
        cadastral_number="77:06:0002008:40",
        object_type=None,
        parcel_type=None,
        address=None,
        area=None,
        permitted_use=None,
        ownership_form=None,
        cadastral_value=None
    )

    # Проверяем to_dict
    parcel_dict = parcel_all_none.to_dict()
    print(f"   Преобразование в словарь:")
    for key, value in parcel_dict.items():
        print(f"      {key}: {value}")

    print("✅ Тест 2 пройден")
    print()

    # Тест 3: ParseResult с None parcel
    print("─" * 80)
    print("Тест 3: ParseResult с None parcel")
    print("─" * 80)

    result_none_parcel = ParseResult(
        cadastral_number="77:01:0005016:3275",
        parcel=None,  # Участок отсутствует!
        objects=[],
        status="Ошибка: участок не найден"
    )

    # Проверяем to_excel_rows
    try:
        rows = result_none_parcel.to_excel_rows()
        print(f"   Создано строк: {len(rows)}")
        print(f"   Первая строка содержит {len(rows[0])} полей")
        print("✅ Тест 3 пройден")
    except Exception as e:
        print(f"❌ Тест 3 провален: {e}")
        return False

    print()

    # Тест 4: ParseResult с частично заполненным участком
    print("─" * 80)
    print("Тест 4: ParseResult с частично заполненным участком")
    print("─" * 80)

    parcel_partial = Parcel(
        cadastral_number="50:20:0000000:1234",
        object_type="Земельный участок",
        parcel_type=None,  # Нет
        address=None,  # Нет
        area="2000",
        permitted_use=None,  # Нет
        ownership_form="Частная собственность",
        cadastral_value=None  # Нет
    )

    result_partial = ParseResult(
        cadastral_number="50:20:0000000:1234",
        parcel=parcel_partial,
        objects=[],
        status="Успешно"
    )

    try:
        rows = result_partial.to_excel_rows()
        print(f"   Создано строк: {len(rows)}")
        for key, value in rows[0].items():
            if value == "-":
                print(f"      {key}: {value} (пустое)")
        print("✅ Тест 4 пройден")
    except Exception as e:
        print(f"❌ Тест 4 провален: {e}")
        return False

    print()

    # Тест 5: Создание Excel с отсутствующими полями
    print("─" * 80)
    print("Тест 5: Создание Excel с отсутствующими полями")
    print("─" * 80)

    results = [
        result_none_parcel,
        result_partial,
        ParseResult(
            cadastral_number="77:05:0001016:22",
            parcel=parcel_no_address,
            objects=[
                RealtyObject(
                    object_type="Здание",
                    cadastral_number="77:05:0001016:1001",
                    purpose=None,  # Нет
                    area="500",
                    ownership_form=None,  # Нет
                    cadastral_value=None  # Нет
                )
            ],
            status="Успешно"
        )
    ]

    try:
        output_file = "test_none_fields.xlsx"
        create_excel_with_template(results, output_file)
        print(f"   Excel файл создан: {output_file}")
        print("✅ Тест 5 пройден")
    except Exception as e:
        print(f"❌ Тест 5 провален: {e}")
        import traceback
        traceback.print_exc()
        return False

    print()
    print("=" * 80)
    print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
    print("=" * 80)
    print()
    print(f"Проверьте файл {output_file} - все отсутствующие поля должны быть заполнены '-'")

    return True


if __name__ == "__main__":
    import sys
    success = test_none_fields()
    sys.exit(0 if success else 1)
