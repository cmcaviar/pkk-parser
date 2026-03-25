"""
Конфигурация парсера НСПД
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class APIConfig:
    """Настройки API"""
    base_url: str = "https://nspd.gov.ru"
    # РЕАЛЬНЫЕ ENDPOINTS из DevTools:
    search_endpoint: str = "/api/geoportal/v2/search/geoportal"
    details_endpoint: str = "/api/geoportal/v2/object"  # Примерный, проверьте в DevTools
    timeout: int = 30
    verify_ssl: bool = False  # Самоподписанный сертификат
    max_retries: int = 3
    retry_delay: float = 5.0
    request_delay_min: float = 1.0
    request_delay_max: float = 2.0

    # Дополнительные параметры для НСПД API
    thematic_search_id: int = 1  # Из реального запроса


@dataclass
class SeleniumConfig:
    """Настройки Selenium"""
    headless: bool = True
    page_load_timeout: int = 30
    implicit_wait: int = 10
    window_size: tuple = (1920, 1080)
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


@dataclass
class ExcelConfig:
    """Настройки Excel"""
    input_sheet: str = "Входные данные"
    input_column: str = "Кадастровый номер объекта недвижимости"
    output_sheet: str = "Результат"
    output_file_pattern: str = "result_{date}.xlsx"

    # Колонки для участка
    parcel_columns: List[str] = None

    # Колонки для объекта
    object_columns: List[str] = None

    def __post_init__(self):
        if self.parcel_columns is None:
            self.parcel_columns = [
                "Кадастровый номер (вход)",
                "Вид объекта (участок)",
                "Вид участка",
                "Адрес (участок)",
                "Площадь (участок)",
                "ВРИ",
                "Форма собственности (участок)",
                "Кадастровая стоимость (участок)",
            ]

        if self.object_columns is None:
            self.object_columns = [
                "Вид объекта (объект)",
                "Кадастровый номер (объект)",
                "Назначение",
                "Площадь (объект)",
                "Форма собственности (объект)",
                "Кадастровая стоимость (объект)",
                "Удельный показатель",
                "Этажи",
                "Подземные этажи",
                "Материал стен",
                "Завершение",
                "Ввод в эксплуатацию",
                "Культурное наследие",
                "Статус обработки",
                "Ошибка"
            ]

    @property
    def all_columns(self) -> List[str]:
        """Все колонки результата"""
        return self.parcel_columns + self.object_columns


@dataclass
class ParserConfig:
    """Общая конфигурация парсера"""
    api: APIConfig = None
    selenium: SeleniumConfig = None
    excel: ExcelConfig = None

    stop_flag_file: str = "stop.flag"
    log_file: str = "parser.log"
    log_level: str = "INFO"

    # Обработка ошибок
    continue_on_error: bool = True
    error_placeholder: str = "Нет данных"

    def __post_init__(self):
        if self.api is None:
            self.api = APIConfig()
        if self.selenium is None:
            self.selenium = SeleniumConfig()
        if self.excel is None:
            self.excel = ExcelConfig()


# Глобальный экземпляр конфигурации
config = ParserConfig()
