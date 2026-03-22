"""
Selenium fallback для парсинга НСПД через браузер
Используется когда API недоступен или блокирует запросы
"""
import logging
import time
import random
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

from config import config
from models import Parcel, RealtyObject

logger = logging.getLogger(__name__)


class SeleniumParser:
    """Парсер на основе Selenium WebDriver"""

    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_driver()

    def _setup_driver(self):
        """Настройка Chrome WebDriver"""
        try:
            chrome_options = Options()

            if config.selenium.headless:
                chrome_options.add_argument('--headless=new')

            # Базовые опции для стабильности
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument(f'--window-size={config.selenium.window_size[0]},{config.selenium.window_size[1]}')
            chrome_options.add_argument(f'--user-agent={config.selenium.user_agent}')

            # Игнорирование SSL ошибок
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')

            # Отключение логов
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Preferences
            prefs = {
                'profile.default_content_setting_values.notifications': 2,
                'profile.default_content_settings.popups': 0,
            }
            chrome_options.add_experimental_option('prefs', prefs)

            # Инициализация драйвера
            # WebDriver Manager автоматически скачает нужную версию ChromeDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(config.selenium.page_load_timeout)
            self.driver.implicitly_wait(config.selenium.implicit_wait)

            logger.info("Selenium WebDriver успешно инициализирован")

        except WebDriverException as e:
            logger.error(f"Ошибка инициализации WebDriver: {e}")
            raise

    def _wait_random(self, min_sec: float = 1.0, max_sec: float = 2.0):
        """Случайная задержка"""
        time.sleep(random.uniform(min_sec, max_sec))

    def search_cadastral_number(self, cadastral_number: str) -> bool:
        """
        Поиск кадастрового номера через веб-интерфейс

        Args:
            cadastral_number: Кадастровый номер для поиска

        Returns:
            True если объект найден, False иначе
        """
        try:
            logger.info(f"Selenium: поиск кадастрового номера {cadastral_number}")

            # Переход на главную страницу
            self.driver.get(config.api.base_url)
            self._wait_random()

            # Поиск поля ввода (селекторы нужно адаптировать под реальный сайт)
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Кадастровый номер'], input[name='cadastralNumber'], input#search"))
            )

            # Ввод кадастрового номера
            search_input.clear()
            search_input.send_keys(cadastral_number)
            self._wait_random(0.5, 1.0)

            # Поиск и клик по кнопке поиска
            search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button.search-btn, .search-button")
            search_button.click()

            # Ожидание результатов
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".result-item, .object-card, .search-result"))
            )

            logger.info(f"Объект {cadastral_number} найден")
            return True

        except TimeoutException:
            logger.warning(f"Объект {cadastral_number} не найден (таймаут)")
            return False
        except NoSuchElementException as e:
            logger.warning(f"Элемент не найден: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return False

    def get_parcel_data(self, cadastral_number: str) -> Optional[Parcel]:
        """
        Извлечение данных земельного участка

        Args:
            cadastral_number: Кадастровый номер

        Returns:
            Объект Parcel или None
        """
        try:
            logger.info(f"Selenium: извлечение данных участка {cadastral_number}")

            # Селекторы нужно адаптировать под реальную структуру страницы
            parcel = Parcel(cadastral_number=cadastral_number)

            # Примерная структура извлечения данных
            # ВАЖНО: Адаптируйте селекторы под реальный HTML сайта

            def safe_get_text(selector: str, default: str = "Нет данных") -> str:
                """Безопасное получение текста элемента"""
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element.text.strip() or default
                except NoSuchElementException:
                    return default

            # Вид объекта
            parcel.object_type = safe_get_text(".object-type, .field-object-type")

            # Вид участка
            parcel.parcel_type = safe_get_text(".parcel-type, .field-parcel-type")

            # Адрес
            parcel.address = safe_get_text(".address, .field-address")

            # Площадь
            parcel.area = safe_get_text(".area, .field-area")

            # ВРИ
            parcel.permitted_use = safe_get_text(".permitted-use, .field-vri")

            # Форма собственности
            parcel.ownership_form = safe_get_text(".ownership, .field-ownership")

            # Кадастровая стоимость
            parcel.cadastral_value = safe_get_text(".cadastral-value, .field-value")

            logger.info(f"Данные участка {cadastral_number} успешно извлечены")
            return parcel

        except Exception as e:
            logger.error(f"Ошибка извлечения данных участка: {e}")
            return None

    def get_objects_on_parcel(self, cadastral_number: str) -> List[RealtyObject]:
        """
        Извлечение объектов недвижимости на участке

        Args:
            cadastral_number: Кадастровый номер участка

        Returns:
            Список объектов RealtyObject
        """
        try:
            logger.info(f"Selenium: извлечение объектов на участке {cadastral_number}")

            objects = []

            # Поиск раздела с объектами на участке
            try:
                objects_section = self.driver.find_element(By.CSS_SELECTOR, ".objects-list, .buildings-list, .objects-on-parcel")
                object_cards = objects_section.find_elements(By.CSS_SELECTOR, ".object-card, .building-item, .object-item")

                logger.info(f"Найдено объектов: {len(object_cards)}")

                for card in object_cards:
                    obj = RealtyObject()

                    def safe_get_text_in_card(selector: str, default: str = "Нет данных") -> str:
                        """Безопасное получение текста внутри карточки объекта"""
                        try:
                            element = card.find_element(By.CSS_SELECTOR, selector)
                            return element.text.strip() or default
                        except NoSuchElementException:
                            return default

                    # Извлечение данных объекта
                    obj.object_type = safe_get_text_in_card(".object-type")
                    obj.cadastral_number = safe_get_text_in_card(".cadastral-number")
                    obj.purpose = safe_get_text_in_card(".purpose")
                    obj.area = safe_get_text_in_card(".area")
                    obj.ownership_form = safe_get_text_in_card(".ownership")
                    obj.cadastral_value = safe_get_text_in_card(".cadastral-value")
                    obj.unit_value = safe_get_text_in_card(".unit-value")
                    obj.floors = safe_get_text_in_card(".floors")
                    obj.underground_floors = safe_get_text_in_card(".underground-floors")
                    obj.wall_material = safe_get_text_in_card(".wall-material")
                    obj.completion = safe_get_text_in_card(".completion")
                    obj.commissioning = safe_get_text_in_card(".commissioning")
                    obj.cultural_heritage = safe_get_text_in_card(".cultural-heritage")

                    objects.append(obj)

            except NoSuchElementException:
                logger.info(f"Объекты на участке {cadastral_number} не найдены")

            return objects

        except Exception as e:
            logger.error(f"Ошибка извлечения объектов: {e}")
            return []

    def parse_cadastral_number(self, cadastral_number: str) -> tuple[Optional[Parcel], List[RealtyObject]]:
        """
        Полный парсинг кадастрового номера

        Args:
            cadastral_number: Кадастровый номер

        Returns:
            Кортеж (Parcel, List[RealtyObject])
        """
        try:
            # Поиск объекта
            if not self.search_cadastral_number(cadastral_number):
                logger.warning(f"Объект {cadastral_number} не найден")
                return None, []

            self._wait_random()

            # Получение данных участка
            parcel = self.get_parcel_data(cadastral_number)

            # Получение объектов на участке
            objects = self.get_objects_on_parcel(cadastral_number)

            return parcel, objects

        except Exception as e:
            logger.error(f"Ошибка парсинга {cadastral_number}: {e}")
            return None, []

    def close(self):
        """Закрытие браузера"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Selenium WebDriver закрыт")
            except Exception as e:
                logger.error(f"Ошибка закрытия WebDriver: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
