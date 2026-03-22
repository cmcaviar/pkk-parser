"""
Ядро парсера - оркестрация API и Selenium
"""
import logging
import os
from typing import List, Optional
from pathlib import Path

from config import config
from models import ParseResult, Parcel, RealtyObject
from api_client import NSPDAPIClient
from selenium_fallback import SeleniumParser

logger = logging.getLogger(__name__)


class NSPDParser:
    """Основной парсер НСПД с API-first подходом"""

    def __init__(self, use_selenium: bool = False):
        """
        Args:
            use_selenium: Сразу использовать Selenium (по умолчанию сначала API)
        """
        self.api_client: Optional[NSPDAPIClient] = None
        self.selenium_parser: Optional[SeleniumParser] = None
        self.use_selenium_fallback = use_selenium

        # Инициализация API клиента если не форсирован Selenium
        if not use_selenium:
            try:
                self.api_client = NSPDAPIClient()
                logger.info("API клиент инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации API клиента: {e}")
                self.use_selenium_fallback = True

    def _check_stop_flag(self) -> bool:
        """
        Проверка флага остановки

        Returns:
            True если нужно остановить парсинг
        """
        stop_flag_path = Path(config.stop_flag_file)
        if stop_flag_path.exists():
            logger.warning("Обнаружен файл stop.flag - остановка парсинга")
            return True
        return False

    def _init_selenium(self):
        """Инициализация Selenium парсера"""
        if not self.selenium_parser:
            try:
                logger.info("Инициализация Selenium fallback...")
                self.selenium_parser = SeleniumParser()
                logger.info("Selenium успешно инициализирован")
            except Exception as e:
                logger.error(f"Ошибка инициализации Selenium: {e}")
                raise

    def _parse_via_api(self, cadastral_number: str) -> ParseResult:
        """
        Парсинг через API

        Args:
            cadastral_number: Кадастровый номер

        Returns:
            ParseResult
        """
        result = ParseResult(cadastral_number=cadastral_number)

        try:
            # Поиск объекта
            search_data = self.api_client.search_cadastral_number(cadastral_number)

            if not search_data:
                result.status = "Не найден"
                result.error = "Объект не найден через API"
                return result

            # Извлечение ID объекта (структура зависит от реального API)
            object_id = search_data.get('id') or search_data.get('objectId')

            if not object_id:
                result.status = "Ошибка"
                result.error = "Не удалось получить ID объекта"
                return result

            # Получение данных участка
            parcel_data = self.api_client.get_parcel_details(object_id)

            if parcel_data:
                result.parcel = self.api_client.parse_parcel_data(parcel_data, cadastral_number)
                logger.info(f"Данные участка {cadastral_number} получены через API")

            # Получение объектов на участке
            objects_data = self.api_client.get_objects_on_parcel(object_id)

            if objects_data:
                for obj_data in objects_data:
                    obj = self.api_client.parse_object_data(obj_data)
                    result.objects.append(obj)
                logger.info(f"Найдено объектов на участке: {len(result.objects)}")

            result.status = "Успешно (API)"
            return result

        except Exception as e:
            logger.error(f"Ошибка парсинга через API: {e}")
            result.status = "Ошибка API"
            result.error = str(e)
            return result

    def _parse_via_selenium(self, cadastral_number: str) -> ParseResult:
        """
        Парсинг через Selenium

        Args:
            cadastral_number: Кадастровый номер

        Returns:
            ParseResult
        """
        result = ParseResult(cadastral_number=cadastral_number)

        try:
            # Инициализация Selenium если еще не создан
            self._init_selenium()

            # Парсинг
            parcel, objects = self.selenium_parser.parse_cadastral_number(cadastral_number)

            if parcel:
                result.parcel = parcel
                logger.info(f"Данные участка {cadastral_number} получены через Selenium")

            if objects:
                result.objects = objects
                logger.info(f"Найдено объектов на участке: {len(objects)}")

            if parcel or objects:
                result.status = "Успешно (Selenium)"
            else:
                result.status = "Не найден"
                result.error = "Объект не найден через Selenium"

            return result

        except Exception as e:
            logger.error(f"Ошибка парсинга через Selenium: {e}")
            result.status = "Ошибка Selenium"
            result.error = str(e)
            return result

    def parse_single(self, cadastral_number: str) -> ParseResult:
        """
        Парсинг одного кадастрового номера с fallback

        Args:
            cadastral_number: Кадастровый номер

        Returns:
            ParseResult
        """
        logger.info(f"=" * 80)
        logger.info(f"Начало парсинга: {cadastral_number}")

        # Проверка флага остановки
        if self._check_stop_flag():
            result = ParseResult(cadastral_number=cadastral_number)
            result.status = "Прерван"
            result.error = "Обнаружен файл stop.flag"
            return result

        # Попытка парсинга через API (если не форсирован Selenium)
        if not self.use_selenium_fallback and self.api_client:
            result = self._parse_via_api(cadastral_number)

            # Если успешно - возвращаем результат
            if result.status.startswith("Успешно"):
                return result

            # Если ошибка API - переключаемся на Selenium
            logger.warning(f"API не смог обработать {cadastral_number}, переключение на Selenium")
            self.use_selenium_fallback = True

        # Парсинг через Selenium
        result = self._parse_via_selenium(cadastral_number)

        return result

    def parse_batch(self, cadastral_numbers: List[str]) -> List[ParseResult]:
        """
        Пакетный парсинг списка кадастровых номеров

        Args:
            cadastral_numbers: Список кадастровых номеров

        Returns:
            Список ParseResult
        """
        results = []
        total = len(cadastral_numbers)

        logger.info(f"Начало пакетного парсинга: {total} номеров")

        for idx, cadastral_number in enumerate(cadastral_numbers, 1):
            logger.info(f"Обработка {idx}/{total}: {cadastral_number}")

            # Проверка флага остановки
            if self._check_stop_flag():
                logger.warning("Парсинг прерван по флагу stop.flag")
                break

            try:
                result = self.parse_single(cadastral_number)
                results.append(result)
                logger.info(f"Статус: {result.status}")

            except Exception as e:
                logger.error(f"Критическая ошибка при парсинге {cadastral_number}: {e}")

                if config.continue_on_error:
                    # Создаем результат с ошибкой и продолжаем
                    error_result = ParseResult(cadastral_number=cadastral_number)
                    error_result.status = "Критическая ошибка"
                    error_result.error = str(e)
                    results.append(error_result)
                else:
                    # Прерываем парсинг
                    logger.error("Парсинг прерван из-за критической ошибки")
                    break

        logger.info(f"Пакетный парсинг завершен: обработано {len(results)}/{total}")
        return results

    def close(self):
        """Закрытие ресурсов"""
        if self.api_client:
            try:
                self.api_client.close()
                logger.info("API клиент закрыт")
            except Exception as e:
                logger.error(f"Ошибка закрытия API клиента: {e}")

        if self.selenium_parser:
            try:
                self.selenium_parser.close()
                logger.info("Selenium парсер закрыт")
            except Exception as e:
                logger.error(f"Ошибка закрытия Selenium: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
