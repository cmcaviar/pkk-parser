"""
Настройка логирования для парсера
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config import config


def setup_logger(
    log_file: str = None,
    log_level: str = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Настройка логгера для парсера

    Args:
        log_file: Путь к файлу логов (по умолчанию из config)
        log_level: Уровень логирования (по умолчанию из config)
        console_output: Выводить логи в консоль

    Returns:
        Настроенный logger
    """
    # Используем значения из конфига если не указаны
    if log_file is None:
        log_file = config.log_file

    if log_level is None:
        log_level = config.log_level

    # Преобразование строки уровня в константу
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Получаем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Формат логов
    log_format = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Обработчик для файла с ротацией
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Предупреждение: не удалось создать файл логов {log_file}: {e}", file=sys.stderr)

    # Обработчик для консоли
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(log_format)
        logger.addHandler(console_handler)

    # Логирование начала работы
    logger.info("=" * 80)
    logger.info(f"Парсер НСПД запущен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Уровень логирования: {log_level}")
    logger.info(f"Файл логов: {log_file}")
    logger.info("=" * 80)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получение именованного логгера

    Args:
        name: Имя логгера (обычно __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, exc: Exception, context: str = ""):
    """
    Логирование исключения с контекстом

    Args:
        logger: Logger instance
        exc: Исключение
        context: Дополнительный контекст
    """
    if context:
        logger.error(f"{context}: {type(exc).__name__}: {exc}", exc_info=True)
    else:
        logger.error(f"{type(exc).__name__}: {exc}", exc_info=True)
