"""
API клиент для работы с НСПД через requests
"""
import requests
import time
import random
import logging
import platform
import os
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

        # Настройка SSL для Windows
        if platform.system() == 'Windows':
            # На Windows часто проблемы с SSL, поэтому явно отключаем проверку
            self.session.verify = False
            logger.debug("Windows: SSL проверка отключена")

            # КРИТИЧНО: Отключаем прокси на Windows
            # Часто Windows пытается использовать несуществующий прокси (127.0.0.1:2080)
            self.session.trust_env = False  # Игнорировать системные настройки прокси
            self.session.proxies = {
                'http': None,
                'https': None,
            }
            logger.debug("Windows: Прокси отключены (trust_env=False)")

            # Также настраиваем адаптер для лучшей работы с SSL
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            # Создаём retry стратегию
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
            logger.debug("Windows: Настроен HTTPAdapter с retry стратегией")
        else:
            self.session.verify = config.api.verify_ssl
            logger.debug(f"SSL проверка: {config.api.verify_ssl}")

        # Определяем User-Agent в зависимости от ОС
        user_agent = self._get_user_agent()
        logger.debug(f"Используемый User-Agent: {user_agent}")
        logger.debug(f"Платформа: {platform.system()} {platform.release()}")

        # Заголовки которые РЕАЛЬНО работают (из test_real_api.py)
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'ru,en;q=0.9',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'origin': 'https://nspd.gov.ru',
            'referer': 'https://nspd.gov.ru/map?thematic=PKK',
            'user-agent': user_agent,
        })
        self.last_request_time = 0

        # Инициализируем cookies сессию через главную страницу
        self._init_session()

    def _get_user_agent(self) -> str:
        """
        Получение User-Agent в зависимости от ОС

        Returns:
            Строка User-Agent соответствующая текущей ОС
        """
        system = platform.system()

        if system == 'Windows':
            return (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/144.0.0.0 Safari/537.36'
            )
        elif system == 'Darwin':  # macOS
            return (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/144.0.0.0 Safari/537.36'
            )
        else:  # Linux и другие
            return (
                'Mozilla/5.0 (X11; Linux x86_64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/144.0.0.0 Safari/537.36'
            )

    def _init_session(self):
        """
        Инициализация сессии через главную страницу для получения cookies
        Это важно для обхода WAF/CDN защиты
        """
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Инициализация сессии (попытка {attempt + 1}/{max_attempts})...")

                # Запрос к главной странице карты для получения cookies
                response = self.session.get(
                    'https://nspd.gov.ru/map',
                    timeout=10,
                    verify=config.api.verify_ssl
                )

                logger.debug(f"Инициализация - статус: {response.status_code}")
                logger.debug(f"Инициализация - Content-Type: {response.headers.get('content-type', 'unknown')}")

                if response.status_code == 200:
                    # Логируем полученные cookies детально
                    cookies_list = [f"{cookie.name}={cookie.value[:20]}..." for cookie in self.session.cookies]
                    logger.debug(f"Сессия инициализирована успешно")
                    logger.debug(f"Получено cookies: {len(self.session.cookies)}")
                    if cookies_list:
                        logger.debug(f"Cookies: {', '.join(cookies_list)}")
                    else:
                        logger.warning("Внимание: Cookies не получены при инициализации")
                    return  # Успех
                else:
                    logger.warning(f"Не удалось инициализировать сессию: {response.status_code}")
                    logger.debug(f"Ответ (первые 500 символов): {response.text[:500]}")

                    if attempt < max_attempts - 1:
                        time.sleep(2)  # Пауза перед повтором

            except Exception as e:
                logger.warning(f"Ошибка инициализации сессии (попытка {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                else:
                    logger.error("Не удалось инициализировать сессию после всех попыток")
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

                # Логирование статуса и заголовков
                logger.debug(f"Статус ответа: {response.status_code}")
                logger.debug(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
                logger.debug(f"Content-Length: {response.headers.get('content-length', 'unknown')}")

                # Обработка специфичных кодов
                if response.status_code == 404:
                    logger.warning(f"Ресурс не найден (404): {url}")
                    logger.debug(f"Ответ 404 (первые 500 символов): {response.text[:500]}")
                    return None

                if response.status_code == 429:
                    logger.warning("Превышен лимит запросов (429), ожидание...")
                    time.sleep(config.api.retry_delay * (attempt + 1))
                    continue

                if response.status_code >= 500:
                    logger.warning(f"Ошибка сервера ({response.status_code}), повтор...")
                    logger.debug(f"Ответ сервера (первые 500 символов): {response.text[:500]}")
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

        logger.debug(f"Полный URL запроса: {url}")
        logger.debug(f"Параметры запроса: {params}")

        response = self._make_request('GET', url, params=params)
        if not response:
            logger.error(f"Не удалось получить ответ для {cadastral_number}")
            return None

        # Диагностика: сохраняем проблемный ответ
        try:
            response_text = response.text
            logger.debug(f"Получен ответ длиной: {len(response_text)} символов")
            logger.debug(f"Первые 1000 символов ответа: {response_text[:1000]}")

            # Проверяем, не HTML ли это
            if response_text.strip().startswith('<'):
                logger.error(f"API вернул HTML вместо JSON! Первые 500 символов:")
                logger.error(response_text[:500])
                self._save_debug_response(cadastral_number, response_text, "html_error")
                return None

            data = response.json()
            logger.debug(f"JSON успешно распарсен, размер: {len(str(data))} символов")

            # РЕАЛЬНАЯ СТРУКТУРА НСПД: {"data": {"features": [...]}}
            if 'data' not in data:
                logger.error(f"Ответ не содержит поле 'data'. Структура: {list(data.keys())}")
                logger.debug(f"Полный ответ: {data}")
                self._save_debug_response(cadastral_number, response_text, "no_data_field")
                return None

            response_data = data['data']

            # Проверяем наличие features (GeoJSON)
            if 'features' not in response_data:
                logger.error(f"Ответ не содержит поле 'features'. Структура data: {list(response_data.keys())}")
                logger.debug(f"Содержимое data: {response_data}")
                self._save_debug_response(cadastral_number, response_text, "no_features_field")
                return None

            features = response_data['features']

            if not isinstance(features, list):
                logger.error(f"features не является массивом: {type(features)}")
                self._save_debug_response(cadastral_number, response_text, "features_not_list")
                return None

            if len(features) == 0:
                logger.warning(f"Объект {cadastral_number} не найден (пустой массив features)")
                logger.debug(f"Полный ответ data: {response_data}")
                return None

            # Возвращаем первый найденный объект (весь feature со свойствами)
            feature = features[0]
            logger.info(f"Объект найден: {feature.get('properties', {}).get('label', cadastral_number)}")
            logger.debug(f"Структура feature: id={feature.get('id')}, type={feature.get('type')}")

            return feature

        except ValueError as e:
            logger.error(f"Ошибка парсинга JSON для {cadastral_number}: {e}")
            logger.error(f"Ответ (первые 1000 символов): {response.text[:1000]}")
            self._save_debug_response(cadastral_number, response.text, "json_parse_error")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке ответа для {cadastral_number}: {e}")
            logger.error(f"Тип ошибки: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def _save_debug_response(self, cadastral_number: str, response_text: str, error_type: str):
        """
        Сохранение проблемного ответа API для диагностики

        Args:
            cadastral_number: Кадастровый номер
            response_text: Текст ответа API
            error_type: Тип ошибки
        """
        try:
            # Создаём папку для дебага если нет
            debug_dir = "debug_responses"
            os.makedirs(debug_dir, exist_ok=True)

            # Безопасное имя файла
            safe_cn = cadastral_number.replace(':', '_')
            filename = f"{debug_dir}/{safe_cn}_{error_type}_{int(time.time())}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Cadastral Number: {cadastral_number}\n")
                f.write(f"Error Type: {error_type}\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Platform: {platform.system()} {platform.release()}\n")
                f.write("="*80 + "\n")
                f.write(response_text)

            logger.debug(f"Проблемный ответ сохранён в {filename}")
        except Exception as e:
            logger.warning(f"Не удалось сохранить debug ответ: {e}")

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
        # Здания: build_record_type_value, build_record_area, purpose, floors, materials, year_built, building_name
        # Сооружения: object_type_value, params_name, params_purpose, params_year_commisioning
        #             params_built_up_area/built_up_area (площадь застройки), params_area (площадь), params_extent (протяжённость)
        # Помещения: realty_estate_type, object_record_area, object_record_purpose

        props = data.get('properties', {})
        opts = props.get('options', {})

        # Определяем тип объекта (здание, помещение, сооружение)
        obj_type = (opts.get('build_record_type_value') or  # "Здание"
                   opts.get('object_type_value') or  # "Сооружение"
                   opts.get('realty_estate_type') or  # "Помещение"
                   opts.get('land_record_type') or
                   'Нет данных')

        # Наименование (для зданий и сооружений)
        name = (opts.get('building_name') or  # Название здания
                opts.get('params_name') or  # Название сооружения ("Водопровод", "Трубопровод" и т.д.)
                opts.get('object_name') or
                None)

        # Назначение (для зданий/помещений/сооружений)
        purpose = (opts.get('purpose') or  # "Нежилое" (для зданий)
                  opts.get('params_purpose') or  # "Нежилое здание" (для сооружений)
                  opts.get('object_record_purpose') or  # для помещений
                  opts.get('permitted_use_name') or
                  'Нет данных')

        # Площадь (для зданий - build_record_area, для помещений - object_record_area)
        # Для сооружений - params_area (если есть)
        area_value = (opts.get('build_record_area') or  # Площадь здания
                     opts.get('object_record_area') or  # Площадь помещения
                     opts.get('params_area') or  # Площадь сооружения (если есть)
                     opts.get('specified_area') or
                     opts.get('land_record_area'))

        # Площадь застройки (специфично для сооружений)
        building_area_value = (opts.get('params_built_up_area') or  # Площадь застройки сооружения
                              opts.get('built_up_area'))  # Альтернативное поле

        # Протяжённость (специфично для сооружений - трубопроводы, дороги и т.д.)
        length_value = opts.get('params_extent')  # Протяжённость

        # Год ввода в эксплуатацию (разные поля для разных типов)
        commissioning_year = (opts.get('year_commisioning') or  # для зданий/помещений
                             opts.get('params_year_commisioning') or  # для сооружений
                             'Нет данных')

        logger.debug(f"Объект {cadastral_number}: тип={obj_type}, name={name}, area={area_value}, building_area={building_area_value}, length={length_value}")

        return RealtyObject(
            cadastral_number=opts.get('cad_num') or opts.get('cad_number', cadastral_number),
            object_type=obj_type,

            # Наименование (НОВОЕ)
            name=name,

            # Назначение
            purpose=purpose,

            # Площадь
            area=self._format_area(area_value),

            # Площадь застройки (НОВОЕ для сооружений)
            building_area=self._format_area(building_area_value) if building_area_value else None,

            # Протяжённость (НОВОЕ для сооружений)
            length=self._format_length(length_value) if length_value else None,

            # Форма собственности
            ownership_form=opts.get('ownership_type') or 'Нет данных',

            # Кадастровая стоимость
            cadastral_value=self._format_cadastral_value(
                opts.get('cost_value'),
                opts.get('cost_application_date')
            ),

            # Удельный показатель (стоимость за кв.м)
            # Используем приоритетно area_value, затем building_area_value
            unit_value=self._format_unit_value(
                opts.get('cost_value'),
                area_value or building_area_value
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

    def _format_length(self, value) -> str:
        """Форматирование протяжённости"""
        if not value:
            return 'Нет данных'
        try:
            return f"{float(value):,.2f} м".replace(',', ' ')
        except (ValueError, TypeError):
            return str(value) if value else 'Нет данных'

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
