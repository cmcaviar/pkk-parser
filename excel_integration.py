"""
Интеграция парсера НСПД с Excel через xlwings
"""
import xlwings as xw
from typing import List, Optional
from api_client import NSPDAPIClient
from models import ParseResult, Parcel


# Порядок колонок по шаблону
COLUMNS = [
    "Кадастровый номер объекта недвижимости",  # A
    "Вид объекта недвижимости",  # B
    "Вид земельного участка",  # C
    "Адрес",  # D
    "Площадь декларированная",  # E
    "Вид разрешенного использования",  # F
    "Форма собственности",  # G
    "Кадастровая стоимость",  # H
    "Вид объекта недвижимости_obj",  # I
    "Кадастровый номер_obj",  # J
    "Назначение",  # K
    "Площадь общая",  # L
    "Форма собственности_obj",  # M
    "Кадастровая стоимость_obj",  # N
    "Удельный показатель кадастровой стоимости",  # O
    "Количество этажей (в том числе подземных)",  # P
    "Количество подземных этажей",  # Q
    "Материал стен",  # R
    "Завершение строительства",  # S
    "Ввод в эксплуатацию",  # T
    "Сведения о культурном наследии",  # U
]


def read_cadastral_numbers_from_sheet(sheet: xw.Sheet, start_row: int = 2) -> List[str]:
    """
    Читает кадастровые номера из колонки A

    Args:
        sheet: Лист Excel
        start_row: Начальная строка (по умолчанию 2, т.к. 1 - заголовки)

    Returns:
        Список кадастровых номеров
    """
    numbers = []
    row = start_row

    while True:
        value = sheet.range(f'A{row}').value
        if value is None or value == "":
            break

        # Преобразуем в строку и очищаем
        cadastral_number = str(value).strip()
        if cadastral_number:
            numbers.append(cadastral_number)

        row += 1

    return numbers


def write_headers_to_sheet(sheet: xw.Sheet, start_row: int = 1):
    """
    Записывает заголовки колонок в первую строку

    Args:
        sheet: Лист Excel
        start_row: Строка для заголовков (по умолчанию 1)
    """
    # Записываем заголовки
    for col_idx, col_name in enumerate(COLUMNS, 1):
        # Убираем _obj суффикс для отображения
        display_name = col_name.replace('_obj', '')
        sheet.cells(start_row, col_idx).value = display_name

    # Форматирование заголовков
    header_range = sheet.range((start_row, 1), (start_row, len(COLUMNS)))
    header_range.font.bold = True
    header_range.color = (217, 225, 242)  # Светло-синий
    header_range.api.HorizontalAlignment = xw.constants.HAlign.xlHAlignCenter


def write_result_to_sheet(
    sheet: xw.Sheet,
    parse_result: ParseResult,
    start_row: int
) -> int:
    """
    Записывает результат парсинга в Excel лист

    Args:
        sheet: Лист Excel
        parse_result: Результат парсинга
        start_row: Начальная строка для записи

    Returns:
        Номер следующей свободной строки
    """
    # Получаем строки для записи
    rows = parse_result.to_excel_rows()

    # Записываем каждую строку
    for row_data in rows:
        for col_idx, col_name in enumerate(COLUMNS, 1):
            value = row_data.get(col_name, "-")
            sheet.cells(start_row, col_idx).value = value

        start_row += 1

    return start_row


def process_from_excel(sheet: Optional[xw.Sheet] = None):
    """
    Основная функция обработки из Excel

    Args:
        sheet: Лист Excel (если None - берется активный лист)
    """
    # Получаем активный лист если не указан
    if sheet is None:
        sheet = xw.books.active.sheets.active

    print("\n" + "=" * 80)
    print("НАЧАЛО ОБРАБОТКИ")
    print("=" * 80)

    try:
        # Обновляем status bar
        xw.apps.active.status_bar = "Чтение кадастровых номеров..."
        print("\n📖 Чтение кадастровых номеров из колонки A...")

        # Читаем кадастровые номера из колонки A
        cadastral_numbers = read_cadastral_numbers_from_sheet(sheet, start_row=2)
        print(f"✅ Найдено номеров: {len(cadastral_numbers)}")
        for idx, cn in enumerate(cadastral_numbers, 1):
            print(f"   {idx}. {cn}")

        if not cadastral_numbers:
            print("❌ Не найдены кадастровые номера в колонке A")
            xw.apps.active.alert("Не найдены кадастровые номера в колонке A (начиная со строки 2)")
            return

        xw.apps.active.status_bar = f"Найдено номеров: {len(cadastral_numbers)}"

        # Очищаем старые данные (кроме колонки A)
        print("\n🧹 Очистка старых данных...")
        last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row
        if last_row > 1:
            clear_range = sheet.range((1, 2), (last_row, len(COLUMNS)))
            clear_range.clear_contents()
            print(f"✅ Очищено строк: {last_row}")

        # Записываем заголовки
        print("\n📝 Запись заголовков...")
        write_headers_to_sheet(sheet, start_row=1)
        print("✅ Заголовки записаны")

        # Создаем API клиент
        print("\n🔌 Создание API клиента...")
        client = NSPDAPIClient()
        current_row = 2  # Начинаем со второй строки (после заголовков)

        print("\n" + "=" * 80)
        print("ОБРАБОТКА НОМЕРОВ")
        print("=" * 80)

        try:
            # Обрабатываем каждый номер
            for idx, cadastral_number in enumerate(cadastral_numbers, 1):
                print(f"\n{'─' * 80}")
                print(f"[{idx}/{len(cadastral_numbers)}] {cadastral_number}")
                print(f"{'─' * 80}")

                xw.apps.active.status_bar = f"Обработка [{idx}/{len(cadastral_numbers)}]: {cadastral_number}"

                try:
                    # Получаем данные
                    print("⏳ Загрузка данных участка...")
                    result = client.get_full_parcel_info_with_objects(cadastral_number)

                    parcel = result['parcel_data']
                    objects = result['objects_data']

                    # Безопасный вывод адреса (с проверкой на None)
                    if parcel and parcel.address:
                        print(f"✅ Участок: {parcel.address[:60]}...")
                    else:
                        print(f"✅ Участок: {cadastral_number} (адрес не указан)")
                    print(f"✅ Объектов найдено: {len(objects)}")

                    # Формируем ParseResult
                    parse_result = ParseResult(
                        cadastral_number=cadastral_number,
                        parcel=parcel,
                        objects=objects,
                        status="Успешно"
                    )

                    # Записываем в Excel
                    print(f"📝 Запись в Excel (строка {current_row})...")
                    rows_before = current_row
                    current_row = write_result_to_sheet(sheet, parse_result, current_row)
                    print(f"✅ Записано строк: {current_row - rows_before}")

                except Exception as e:
                    print(f"❌ Ошибка: {e}")
                    # Записываем строку с ошибкой
                    sheet.cells(current_row, 1).value = cadastral_number
                    sheet.cells(current_row, 2).value = f"ОШИБКА: {str(e)}"
                    sheet.cells(current_row, 2).color = (255, 200, 200)  # Светло-красный
                    current_row += 1

        finally:
            print("\n🔒 Закрытие API клиента...")
            client.close()

        # Автоподбор ширины колонок
        print("\n🎨 Автоподбор ширины колонок...")
        try:
            sheet.autofit(axis='columns')
            print("✅ Ширина колонок настроена")
        except Exception as e:
            print(f"⚠️  Не удалось автоподобрать ширину колонок: {e}")
            # Не критично, продолжаем

        # Завершение
        print("\n" + "=" * 80)
        print("✅ ОБРАБОТКА ЗАВЕРШЕНА!")
        print("=" * 80)
        print(f"\n📊 Статистика:")
        print(f"   Обработано номеров: {len(cadastral_numbers)}")
        print(f"   Строк добавлено: {current_row - 2}")

        xw.apps.active.status_bar = f"✅ Готово! Обработано: {len(cadastral_numbers)}"
        xw.apps.active.alert(
            f"Обработка завершена!\n\nОбработано номеров: {len(cadastral_numbers)}\nСтрок добавлено: {current_row - 2}",
            title="НСПД Парсер"
        )

    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

        xw.apps.active.status_bar = f"❌ Ошибка: {str(e)}"
        xw.apps.active.alert(f"Произошла ошибка:\n\n{str(e)}", title="Ошибка")
        raise

    finally:
        xw.apps.active.status_bar = False
        print("\n" + "=" * 80)


def process_single_from_excel(cadastral_number: str, sheet: Optional[xw.Sheet] = None):
    """
    Обработка одного кадастрового номера

    Args:
        cadastral_number: Кадастровый номер
        sheet: Лист Excel (если None - берется активный лист)
    """
    if sheet is None:
        sheet = xw.books.active.sheets.active

    try:
        xw.apps.active.status_bar = f"Обработка: {cadastral_number}"

        # Создаем API клиент
        client = NSPDAPIClient()

        try:
            # Получаем данные
            result = client.get_full_parcel_info_with_objects(cadastral_number)

            # Формируем ParseResult
            parse_result = ParseResult(
                cadastral_number=cadastral_number,
                parcel=result['parcel_data'],
                objects=result['objects_data'],
                status="Успешно"
            )

            # Определяем где записывать
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row
            start_row = last_row + 1 if last_row > 1 else 2

            # Если нет заголовков - добавляем
            if sheet.range('A1').value is None:
                write_headers_to_sheet(sheet, start_row=1)
                start_row = 2

            # Записываем результат
            write_result_to_sheet(sheet, parse_result, start_row)

            # Автоподбор
            sheet.autofit(axis='columns')

            xw.apps.active.status_bar = "✅ Готово!"
            # Безопасный вывод адреса (с проверкой на None)
            address_info = parse_result.parcel.address if (parse_result.parcel and parse_result.parcel.address) else "Адрес не указан"
            xw.apps.active.alert(
                f"Участок: {address_info}\n\nОбъектов: {len(parse_result.objects)}",
                title="Успешно"
            )

        finally:
            client.close()

    except Exception as e:
        xw.apps.active.status_bar = f"❌ Ошибка: {str(e)}"
        xw.apps.active.alert(f"Произошла ошибка:\n\n{str(e)}", title="Ошибка")
        raise

    finally:
        xw.apps.active.status_bar = False
