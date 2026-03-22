"""
API клиент для работы с НСПД через requests
"""
import requests
import time
import random
import logging
from typing import Optional, Dict, Any, List
from urllib3.exceptions import InsecureRequestWarning

from config import config
from models import Parcel, RealtyObject

# Отключаем предупреждения о небезопасных SSL соединениях
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


class NSPDAPIClient:
    """Клиент для работы с API НСПД"""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = config.api.verify_ssl
        self.session.headers.update({
            'User-Agent': config.selenium.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
        })
        self.last_request_time = 0

    def _wait_between_requests(self):
        """Задержка между запросами"""
        elapsed = time.time() - self.last_request_time
        min_delay = config.api.request_delay_min
        max_delay = config.api.request_delay_max
        delay = random.uniform(min_delay, max_delay)

        if elapsed < delay:
            time.sleep(delay - elapsed)

        self.last_request_time = time.time()

    def _make_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[requests.Response]:
        """
        Выполнение HTTP запроса с retry логикой

        Args:
            method: HTTP метод (GET, POST и т.д.)
            url: URL для запроса
            **kwargs: Дополнительные параметры для requests

        Returns:
            Response объект или None при ошибке
        """
        self._wait_between_requests()

        for attempt in range(config.api.max_retries):
            try:
                logger.debug(f"Запрос {method} {url} (попытка {attempt + 1}/{config.api.max_retries})")

                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=config.api.timeout,
                    verify=config.api.verify_ssl,
                    **kwargs
                )

                # Логирование статуса
                logger.debug(f"Статус ответа: {response.status_code}")

                # Обработка специфичных кодов
                if response.status_code == 404:
                    logger.warning(f"Ресурс не найден (404): {url}")
                    return None

                if response.status_code == 429:
                    logger.warning("Превышен лимит запросов (429), ожидание...")
                    time.sleep(config.api.retry_delay * (attempt + 1))
                    continue

                if response.status_code >= 500:
                    logger.warning(f"Ошибка сервера ({response.status_code}), повтор...")
                    time.sleep(config.api.retry_delay * (attempt + 1))
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL ошибка: {e}")
                if attempt < config.api.max_retries - 1:
                    time.sleep(config.api.retry_delay)
                continue

            except requests.exceptions.Timeout as e:
                logger.warning(f"Таймаут запроса: {e}")
                if attempt < config.api.max_retries - 1:
                    time.sleep(config.api.retry_delay)
                continue

            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Ошибка соединения: {e}")
                if attempt < config.api.max_retries - 1:
                    time.sleep(config.api.retry_delay * (attempt + 1))
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка запроса: {e}")
                if attempt < config.api.max_retries - 1:
                    time.sleep(config.api.retry_delay)
                continue

        logger.error(f"Не удалось выполнить запрос после {config.api.max_retries} попыток")
        return None

    def search_cadastral_number(self, cadastral_number: str) -> Optional[Dict[str, Any]]:
        """
        Поиск объекта по кадастровому номеру

        Args:
            cadastral_number: Кадастровый номер для поиска

        Returns:
            Словарь с данными или None
        """
        logger.info(f"Поиск кадастрового номера: {cadastral_number}")

        # Реальный API endpoint может отличаться - это примерная структура
        # Необходимо проанализировать реальные запросы через DevTools
        url = f"{config.api.base_url}/api/object/search"
        params = {
            'cadastralNumber': cadastral_number,
            'objectType': 'parcel'  # или 'building'
        }

        response = self._make_request('GET', url, params=params)
        if not response:
            return None

        try:
            data = response.json()
            return data
        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None

    def get_parcel_details(self, parcel_id: str) -> Optional[Dict[str, Any]]:
        """
        Получение детальной информации об участке

        Args:
            parcel_id: ID участка

        Returns:
            Словарь с данными или None
        """
        logger.info(f"Получение данных участка: {parcel_id}")

        url = f"{config.api.base_url}/api/object/{parcel_id}/details"

        response = self._make_request('GET', url)
        if not response:
            return None

        try:
            data = response.json()
            return data
        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return None

    def get_objects_on_parcel(self, parcel_id: str) -> List[Dict[str, Any]]:
        """
        Получение списка объектов на участке

        Args:
            parcel_id: ID участка

        Returns:
            Список объектов
        """
        logger.info(f"Получение объектов на участке: {parcel_id}")

        url = f"{config.api.base_url}/api/object/{parcel_id}/objects"

        response = self._make_request('GET', url)
        if not response:
            return []

        try:
            data = response.json()
            return data.get('objects', [])
        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []

    def parse_parcel_data(self, data: Dict[str, Any], cadastral_number: str) -> Parcel:
        """
        Парсинг данных участка из API ответа

        Args:
            data: Данные из API
            cadastral_number: Исходный кадастровый номер

        Returns:
            Объект Parcel
        """
        # Структура данных может отличаться - адаптируйте под реальный API
        return Parcel(
            cadastral_number=cadastral_number,
            object_type=data.get('objectType', 'Нет данных'),
            parcel_type=data.get('parcelType', 'Нет данных'),
            address=data.get('address', 'Нет данных'),
            area=str(data.get('area', 'Нет данных')),
            permitted_use=data.get('permittedUse', {}).get('name', 'Нет данных'),
            ownership_form=data.get('ownershipForm', 'Нет данных'),
            cadastral_value=str(data.get('cadastralValue', 'Нет данных'))
        )

    def parse_object_data(self, data: Dict[str, Any]) -> RealtyObject:
        """
        Парсинг данных объекта из API ответа

        Args:
            data: Данные из API

        Returns:
            Объект RealtyObject
        """
        # Структура данных может отличаться - адаптируйте под реальный API
        return RealtyObject(
            object_type=data.get('objectType', 'Нет данных'),
            cadastral_number=data.get('cadastralNumber', 'Нет данных'),
            purpose=data.get('purpose', 'Нет данных'),
            area=str(data.get('area', 'Нет данных')),
            ownership_form=data.get('ownershipForm', 'Нет данных'),
            cadastral_value=str(data.get('cadastralValue', 'Нет данных')),
            unit_value=str(data.get('unitValue', 'Нет данных')),
            floors=str(data.get('floors', 'Нет данных')),
            underground_floors=str(data.get('undergroundFloors', 'Нет данных')),
            wall_material=data.get('wallMaterial', 'Нет данных'),
            completion=str(data.get('completion', 'Нет данных')),
            commissioning=str(data.get('commissioning', 'Нет данных')),
            cultural_heritage=data.get('culturalHeritage', 'Нет данных')
        )

    def close(self):
        """Закрытие сессии"""
        self.session.close()
