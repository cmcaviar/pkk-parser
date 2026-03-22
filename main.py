"""
Главный модуль парсера НСПД
Точка входа для запуска из командной строки или Excel
"""
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

from logger_setup import setup_logger
from excel_io import read_cadastral_numbers_from_excel, write_results_to_excel
from parser_core import NSPDParser
from config import config

logger = None


def parse_arguments():
    """
    Парсинг аргументов командной строки

    Returns:
        Namespace с аргументами
    """
    parser = argparse.ArgumentParser(
        description='Парсер НСПД (https://nspd.gov.ru) для получения данных по кадастровым номерам',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py data.xlsx
  python main.py data.xlsx --output results.xlsx
  python main.py data.xlsx --selenium
  python main.py data.xlsx --log-level DEBUG
        """
    )

    parser.add_argument(
        'excel_file',
        type=str,
        help=f'Путь к Excel файлу с кадастровыми номерами (должен содержать лист "{config.excel.input_sheet}")'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Путь к выходному файлу (по умолчанию создается лист в исходном файле)'
    )

    parser.add_argument(
        '--selenium',
        action='store_true',
        help='Использовать только Selenium (без попыток API)'
    )

    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.log_level,
        help=f'Уровень логирования (по умолчанию: {config.log_level})'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        default=config.log_file,
        help=f'Файл для логов (по умолчанию: {config.log_file})'
    )

    parser.add_argument(
        '--no-console',
        action='store_true',
        help='Не выводить логи в консоль'
    )

    parser.add_argument(
        '--create-new-file',
        action='store_true',
        help='Создать новый файл с результатами вместо добавления листа'
    )

    return parser.parse_args()


def validate_excel_file(file_path: str) -> Path:
    """
    Валидация Excel файла

    Args:
        file_path: Путь к файлу

    Returns:
        Path объект

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если файл не является Excel
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    if path.suffix.lower() not in ['.xlsx', '.xlsm', '.xls']:
        raise ValueError(f"Файл должен быть в формате Excel (.xlsx, .xlsm, .xls): {file_path}")

    return path


def main():
    """Основная функция"""
    global logger

    try:
        # Парсинг аргументов
        args = parse_arguments()

        # Настройка логирования
        logger = setup_logger(
            log_file=args.log_file,
            log_level=args.log_level,
            console_output=not args.no_console
        )

        # Валидация входного файла
        excel_path = validate_excel_file(args.excel_file)
        logger.info(f"Входной файл: {excel_path}")

        # Чтение кадастровых номеров
        logger.info("Чтение кадастровых номеров из Excel...")
        cadastral_numbers = read_cadastral_numbers_from_excel(str(excel_path))

        if not cadastral_numbers:
            logger.error("Не найдено ни одного кадастрового номера для обработки")
            sys.exit(1)

        logger.info(f"Найдено кадастровых номеров для обработки: {len(cadastral_numbers)}")

        # Запуск парсера
        logger.info(f"Режим работы: {'Selenium' if args.selenium else 'API-first с Selenium fallback'}")

        with NSPDParser(use_selenium=args.selenium) as parser:
            results = parser.parse_batch(cadastral_numbers)

        # Статистика
        successful = sum(1 for r in results if r.status.startswith("Успешно"))
        errors = sum(1 for r in results if "Ошибка" in r.status)
        not_found = sum(1 for r in results if "Не найден" in r.status)

        logger.info("=" * 80)
        logger.info("СТАТИСТИКА ПАРСИНГА:")
        logger.info(f"  Всего обработано: {len(results)}")
        logger.info(f"  Успешно: {successful}")
        logger.info(f"  Не найдено: {not_found}")
        logger.info(f"  Ошибки: {errors}")
        logger.info("=" * 80)

        # Запись результатов
        logger.info("Запись результатов в Excel...")

        write_results_to_excel(
            results=results,
            excel_file=str(excel_path),
            create_new_file=args.create_new_file or args.output is not None
        )

        logger.info("Парсинг успешно завершен!")
        logger.info(f"Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except KeyboardInterrupt:
        if logger:
            logger.warning("Парсинг прерван пользователем (Ctrl+C)")
        else:
            print("Парсинг прерван пользователем", file=sys.stderr)
        return 130

    except Exception as e:
        if logger:
            logger.error(f"Критическая ошибка: {e}", exc_info=True)
        else:
            print(f"Критическая ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
