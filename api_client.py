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

        # Заголовки которые РЕАЛЬНО работают (из test_real_api.py)
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'origin': 'https://nspd.gov.ru',
            'referer': 'https://nspd.gov.ru/map?thematic=PKK',
            'user-agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/144.0.0.0 Safari/537.36'
            ),
        })
        self.last_request_time = 0

        # Инициализируем cookies сессию через главную страницу
        self._init_session()

    def _init_session(self):
        """
        Инициализация сессии через главную страницу для получения cookies
        Это важно для обхода WAF/CDN защиты
        """
        try:
            logger.debug("Инициализация сессии...")

            # Запрос к главной странице карты для получения cookies
            response = self.session.get(
                'https://nspd.gov.ru/map',
                timeout=10,
                verify=config.api.verify_ssl
            )

            if response.status_code == 200:
                logger.debug(f"Сессия инициализирована. Cookies: {len(self.session.cookies)}")
            else:
                logger.warning(f"Не удалось инициализировать сессию: {response.status_code}")

        except Exception as e:
            logger.warning(f"Ошибка инициализации сессии: {e}")
            # Продолжаем работу даже если не удалось
            pass

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

        # РЕАЛЬНЫЙ API ENDPOINT из DevTools
        url = f"{config.api.base_url}{config.api.search_endpoint}"

        # РЕАЛЬНЫЕ ПАРАМЕТРЫ из DevTools
        params = {
            'thematicSearchId': config.api.thematic_search_id,  # 1
            'query': cadastral_number  # Изменено с 'cadastralNumber'
        }

        response = self._make_request('GET', url, params=params)
        if not response:
            return None

        try:
            data = response.json()
            logger.debug(f"Получен ответ: {len(str(data))} символов")

            # РЕАЛЬНАЯ СТРУКТУРА НСПД: {"data": {"features": [...]}}
            if 'data' not in data:
                logger.error("Ответ не содержит поле 'data'")
                return None

            response_data = data['data']

            # Проверяем наличие features (GeoJSON)
            if 'features' not in response_data:
                logger.error("Ответ не содержит поле 'features'")
                return None

            features = response_data['features']

            if not isinstance(features, list):
                logger.error(f"features не является массивом: {type(features)}")
                return None

            if len(features) == 0:
                logger.warning(f"Объект {cadastral_number} не найден (пустой массив features)")
                return None

            # Возвращаем первый найденный объект (весь feature со свойствами)
            feature = features[0]
            logger.info(f"Объект найден: {feature.get('properties', {}).get('label', cadastral_number)}")

            return feature

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

    def get_objects_on_parcel(self, feature_id: int, category_id: int = 36368) -> List[str]:
        """
        Получение списка кадастровых номеров объектов недвижимости на участке

        Args:
            feature_id: ID feature из search API (не путать с interactionId!)
            category_id: ID категории (по умолчанию 36368 - "Земельные участки ЕГРН")

        Returns:
            Список кадастровых номеров объектов или пустой список
        """
        logger.info(f"Получение объектов на участке с feature_id: {feature_id}")

        url = f"{config.api.base_url}/api/geoportal/v1/tab-group-data"

        params = {
            'tabClass': 'objectsList',
            'categoryId': category_id,
            'geomId': feature_id,
        }

        response = self._make_request('GET', url, params=params)
        if not response:
            return []

        try:
            data = response.json()

            # Структура: {"title": "...", "object": [{"title": "...", "value": ["cn1", "cn2", ...]}]}
            if 'object' in data and isinstance(data['object'], list) and len(data['object']) > 0:
                first_obj = data['object'][0]
                if isinstance(first_obj, dict) and 'value' in first_obj:
                    cadastral_numbers = first_obj['value']
                    logger.info(f"Найдено объектов: {len(cadastral_numbers)}")
                    return cadastral_numbers

            logger.warning(f"Объекты не найдены на участке {feature_id}")
            return []

        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            return []

    def parse_parcel_data(self, data: Dict[str, Any], cadastral_number: str) -> Parcel:
        """
        Парсинг данных участка из API ответа

        Args:
            data: Данные feature из GeoJSON (содержит properties, geometry и т.д.)
            cadastral_number: Исходный кадастровый номер

        Returns:
            Объект Parcel
        """
        # РЕАЛЬНАЯ СТРУКТУРА НСПД:
        # data = {
        #   "properties": {
        #     "options": { ... все данные здесь ... }
        #   }
        # }

        props = data.get('properties', {})
        options = props.get('options', {})

        # Извлекаем данные из options
        return Parcel(
            cadastral_number=options.get('cad_num', cadastral_number),

            # Вид объекта и тип участка
            object_type=options.get('land_record_type', 'Нет данных'),  # "Земельный участок"
            parcel_type=options.get('land_record_subtype', 'Нет данных'),  # "Землепользование"

            # Адрес
            address=options.get('readable_address', 'Нет данных').strip(),

            # Площадь (приоритет - specified_area, иначе land_record_area)
            area=self._format_area(
                options.get('specified_area') or options.get('land_record_area')
            ),

            # ВРИ (вид разрешенного использования)
            permitted_use=options.get('permitted_use_established_by_document',
                                     options.get('permitted_use_land_by_document', 'Нет данных')),

            # Форма собственности
            ownership_form=options.get('ownership_type', 'Нет данных'),  # "Государственная субъекта РФ"

            # Кадастровая стоимость
            cadastral_value=self._format_cadastral_value(
                options.get('cost_value'),
                options.get('cost_application_date')
            )
        )

    def _format_area(self, value) -> str:
        """Форматирование площади"""
        if not value:
            return 'Нет данных'
        try:
            return f"{float(value):,.2f} м²".replace(',', ' ')
        except (ValueError, TypeError):
            return str(value) if value else 'Нет данных'

    def _format_cadastral_value(self, value, date=None) -> str:
        """Форматирование кадастровой стоимости"""
        if value is None:
            return 'Нет данных'

        try:
            # Форматируем число с разделителями тысяч
            formatted = f"{float(value):,.2f}".replace(',', ' ')

            # Добавляем дату если есть
            if date:
                return f"{formatted} руб. (на {date})"
            else:
                return f"{formatted} руб."
        except (ValueError, TypeError):
            return str(value) if value else 'Нет данных'

    def parse_object_data(self, data: Dict[str, Any], cadastral_number: str) -> RealtyObject:
        """
        Парсинг данных объекта недвижимости из API ответа

        Args:
            data: Данные feature из GeoJSON (содержит properties, geometry и т.д.)
            cadastral_number: Кадастровый номер объекта

        Returns:
            Объект RealtyObject
        """
        # РЕАЛЬНАЯ СТРУКТУРА НСПД для объектов:
        # Здания: build_record_type_value, build_record_area, purpose, floors, materials, year_built
        # Сооружения: object_type_value, params_name, params_purpose, params_year_commisioning
        # Помещения: realty_estate_type, object_record_area, object_record_purpose

        props = data.get('properties', {})
        opts = props.get('options', {})

        # Определяем тип объекта (здание, помещение, сооружение)
        obj_type = (opts.get('build_record_type_value') or  # "Здание"
                   opts.get('object_type_value') or  # "Сооружение"
                   opts.get('realty_estate_type') or  # "Помещение"
                   opts.get('land_record_type') or
                   'Нет данных')

        # Назначение (для зданий/помещений/сооружений)
        purpose = (opts.get('purpose') or  # "Нежилое" (для зданий)
                  opts.get('params_purpose') or  # "Нежилое здание" (для сооружений)
                  opts.get('object_record_purpose') or  # для помещений
                  opts.get('permitted_use_name') or
                  opts.get('params_name') or  # "Водопровод" (название сооружения)
                  'Нет данных')

        # Площадь (для зданий - build_record_area, для помещений - object_record_area)
        area_value = (opts.get('build_record_area') or  # Площадь здания
                     opts.get('object_record_area') or  # Площадь помещения
                     opts.get('specified_area') or
                     opts.get('land_record_area'))

        # Год ввода в эксплуатацию (разные поля для разных типов)
        commissioning_year = (opts.get('year_commisioning') or  # для зданий/помещений
                             opts.get('params_year_commisioning') or  # для сооружений
                             'Нет данных')

        return RealtyObject(
            cadastral_number=opts.get('cad_num') or opts.get('cad_number', cadastral_number),
            object_type=obj_type,

            # Назначение
            purpose=purpose,

            # Площадь
            area=self._format_area(area_value),

            # Форма собственности
            ownership_form=opts.get('ownership_type') or 'Нет данных',

            # Кадастровая стоимость
            cadastral_value=self._format_cadastral_value(
                opts.get('cost_value'),
                opts.get('cost_application_date')
            ),

            # Удельный показатель (стоимость за кв.м)
            unit_value=self._format_unit_value(
                opts.get('cost_value'),
                area_value
            ),

            # Этажность (для зданий)
            floors=str(opts.get('floors')) if opts.get('floors') else 'Нет данных',
            underground_floors=str(opts.get('underground_floors')) if opts.get('underground_floors') else 'Нет данных',

            # Материал стен (для зданий)
            wall_material=opts.get('materials', 'Нет данных'),

            # Даты
            completion=str(opts.get('year_built')) if opts.get('year_built') else 'Нет данных',
            commissioning=str(commissioning_year) if commissioning_year != 'Нет данных' else 'Нет данных',

            # Культурное наследие
            cultural_heritage=opts.get('cultural_heritage_val') or 'Нет данных'
        )

    def _format_unit_value(self, cost_value, area_value) -> str:
        """Форматирование удельной стоимости (руб/м²)"""
        if not cost_value or not area_value:
            return 'Нет данных'

        try:
            unit_cost = float(cost_value) / float(area_value)
            return f"{unit_cost:,.2f} руб/м²".replace(',', ' ')
        except (ValueError, TypeError, ZeroDivisionError):
            return 'Нет данных'

    def get_full_parcel_info(self, cadastral_number: str) -> Dict[str, Any]:
        """
        Получение полной информации об участке включая список объектов на нем

        Args:
            cadastral_number: Кадастровый номер участка

        Returns:
            Словарь с данными: {
                'parcel_feature': {...},  # Полный feature участка
                'parcel_data': Parcel,    # Распарсенные данные участка
                'objects_cadastral_numbers': [...],  # Список кадастровых номеров объектов
                'objects_data': [RealtyObject, ...]  # Данные объектов (если запрошено)
            }
        """
        logger.info(f"Получение полной информации об участке: {cadastral_number}")

        result = {
            'parcel_feature': None,
            'parcel_data': None,
            'objects_cadastral_numbers': [],
            'objects_data': []
        }

        # Шаг 1: Поиск участка
        parcel_feature = self.search_cadastral_number(cadastral_number)
        if not parcel_feature:
            logger.error(f"Участок {cadastral_number} не найден")
            return result

        result['parcel_feature'] = parcel_feature

        # Парсим данные участка
        parcel_data = self.parse_parcel_data(parcel_feature, cadastral_number)
        result['parcel_data'] = parcel_data

        # Шаг 2: Получаем список объектов на участке
        feature_id = parcel_feature.get('id')
        category_id = parcel_feature.get('properties', {}).get('category', 36368)

        if feature_id:
            objects_cns = self.get_objects_on_parcel(feature_id, category_id)
            result['objects_cadastral_numbers'] = objects_cns

            logger.info(f"Участок {cadastral_number}: найдено {len(objects_cns)} объектов")
        else:
            logger.warning(f"Не удалось получить feature_id для участка {cadastral_number}")

        return result

    def get_full_parcel_info_with_objects(self, cadastral_number: str) -> Dict[str, Any]:
        """
        Получение полной информации об участке + детальные данные всех объектов

        Args:
            cadastral_number: Кадастровый номер участка

        Returns:
            Словарь с данными участка и всеми объектами
        """
        logger.info(f"Получение полной информации с объектами: {cadastral_number}")

        # Получаем базовую информацию
        result = self.get_full_parcel_info(cadastral_number)

        # Получаем данные каждого объекта
        objects_data = []
        for obj_cn in result['objects_cadastral_numbers']:
            logger.info(f"  Получение данных объекта: {obj_cn}")

            # Используем тот же search API для объектов
            obj_feature = self.search_cadastral_number(obj_cn)
            if obj_feature:
                obj_data = self.parse_object_data(obj_feature, obj_cn)
                objects_data.append(obj_data)
            else:
                logger.warning(f"  Объект {obj_cn} не найден")

        result['objects_data'] = objects_data
        logger.info(f"Участок {cadastral_number}: загружено данных {len(objects_data)}/{len(result['objects_cadastral_numbers'])} объектов")

        return result

    def close(self):
        """Закрытие сессии"""
        self.session.close()
