"""
Модели данных для участков, объектов недвижимости и помещений зданий
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Parcel:
    """Земельный участок"""
    cadastral_number: str  # Кадастровый номер входной
    object_type: Optional[str] = None  # Вид объекта
    parcel_type: Optional[str] = None  # Вид участка
    address: Optional[str] = None  # Адрес
    area: Optional[str] = None  # Площадь
    permitted_use: Optional[str] = None  # ВРИ (вид разрешенного использования)
    ownership_form: Optional[str] = None  # Форма собственности
    cadastral_value: Optional[str] = None  # Кадастровая стоимость

    def to_dict(self) -> dict:
        """Преобразование в словарь для записи в Excel (колонки B-H)"""
        return {
            "Вид объекта недвижимости": self.object_type or "-",
            "Вид земельного участка": self.parcel_type or "-",
            "Адрес": self.address or "-",
            "Площадь декларированная": self.area or "-",
            "Вид разрешенного использования": self.permitted_use or "-",
            "Форма собственности": self.ownership_form or "-",
            "Кадастровая стоимость": self.cadastral_value or "-",
        }


@dataclass
class RealtyObject:
    """Объект недвижимости на участке"""
    object_type: Optional[str] = None  # Вид объекта
    cadastral_number: Optional[str] = None  # Кадастровый номер объекта
    name: Optional[str] = None  # Наименование (для сооружений и зданий)
    purpose: Optional[str] = None  # Назначение
    area: Optional[str] = None  # Площадь (общая или застройки)
    building_area: Optional[str] = None  # Площадь застройки (для сооружений)
    length: Optional[str] = None  # Протяжённость (для сооружений)
    ownership_form: Optional[str] = None  # Форма собственности
    cadastral_value: Optional[str] = None  # Кадастровая стоимость
    unit_value: Optional[str] = None  # Удельный показатель
    floors: Optional[str] = None  # Этажи
    underground_floors: Optional[str] = None  # Подземные этажи
    wall_material: Optional[str] = None  # Материал стен
    completion: Optional[str] = None  # Завершение
    commissioning: Optional[str] = None  # Ввод в эксплуатацию
    cultural_heritage: Optional[str] = None  # Культурное наследие

    def to_dict(self) -> dict:
        """Преобразование в словарь для записи в Excel (колонки I-U)"""
        return {
            "Вид объекта недвижимости_obj": self.object_type or "-",
            "Кадастровый номер_obj": self.cadastral_number or "-",
            "Наименование": self.name or "-",  # НОВОЕ ПОЛЕ
            "Назначение": self.purpose or "-",
            "Площадь общая": self.area or "-",
            "Площадь застройки": self.building_area or "-",  # НОВОЕ ПОЛЕ для сооружений
            "Протяжённость": self.length or "-",  # НОВОЕ ПОЛЕ для сооружений
            "Форма собственности_obj": self.ownership_form or "-",
            "Кадастровая стоимость_obj": self.cadastral_value or "-",
            "Удельный показатель кадастровой стоимости": self.unit_value or "-",
            "Количество этажей (в том числе подземных)": self.floors or "-",
            "Количество подземных этажей": self.underground_floors or "-",
            "Материал стен": self.wall_material or "-",
            "Завершение строительства": self.completion or "-",
            "Ввод в эксплуатацию": self.commissioning or "-",
            "Сведения о культурном наследии": self.cultural_heritage or "-",
        }


@dataclass
class ParseResult:
    """Результат парсинга для одного кадастрового номера"""
    cadastral_number: str
    parcel: Optional[Parcel] = None
    objects: List[RealtyObject] = field(default_factory=list)
    status: str = "Не обработан"
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_excel_rows(self) -> List[dict]:
        """
        Преобразование в строки для Excel по шаблону

        Структура:
        - A: Кадастровый номер объекта недвижимости
        - B-H: Сведения о земельном участке
        - I-U: Сведения об объектах на участке

        Если объектов несколько → несколько строк (участок дублируется)
        Если нет объектов → одна строка (I-U пустые "-")
        """
        rows = []

        # Базовые данные участка (колонки B-H)
        parcel_data = self.parcel.to_dict() if self.parcel else {
            "Вид объекта недвижимости": "-",
            "Вид земельного участка": "-",
            "Адрес": "-",
            "Площадь декларированная": "-",
            "Вид разрешенного использования": "-",
            "Форма собственности": "-",
            "Кадастровая стоимость": "-",
        }

        # Пустые данные объекта (колонки I-U + новые поля)
        empty_object = {
            "Вид объекта недвижимости_obj": "-",
            "Кадастровый номер_obj": "-",
            "Наименование": "-",
            "Назначение": "-",
            "Площадь общая": "-",
            "Площадь застройки": "-",
            "Протяжённость": "-",
            "Форма собственности_obj": "-",
            "Кадастровая стоимость_obj": "-",
            "Удельный показатель кадастровой стоимости": "-",
            "Количество этажей (в том числе подземных)": "-",
            "Количество подземных этажей": "-",
            "Материал стен": "-",
            "Завершение строительства": "-",
            "Ввод в эксплуатацию": "-",
            "Сведения о культурном наследии": "-",
        }

        if self.objects:
            # Несколько строк - по одной на каждый объект
            for obj in self.objects:
                row = {
                    "Кадастровый номер объекта недвижимости": self.cadastral_number,
                    **parcel_data,
                    **obj.to_dict()
                }
                rows.append(row)
        else:
            # Одна строка с участком без объектов
            row = {
                "Кадастровый номер объекта недвижимости": self.cadastral_number,
                **parcel_data,
                **empty_object
            }
            rows.append(row)

        return rows


@dataclass
class Premise:
    """Помещение в здании"""
    cad_number: str                          # Кадастровый номер помещения
    building_cad_number: str                 # Кадастровый номер здания
    has_coordinates: bool = False            # Есть ли координаты границ
    removed_gcu: bool = False               # Снят с государственного кадастрового учёта
    obj_type: str = "Помещение"             # Вид объекта
    registration_date: Optional[str] = None  # Дата присвоения
    living_type: Optional[str] = None       # Вид жилого помещения (Квартира, Комната и т.д.)
    purpose: Optional[str] = None           # Назначение (Жилое/Нежилое)
    floor: Optional[str] = None             # Номер/тип этажа
    area: Optional[float] = None            # Площадь, кв.м
    address: Optional[str] = None           # Адрес
    cadastral_status: Optional[str] = None  # Статус (кадастровый)
    ownership_form: Optional[str] = None    # Форма собственности
    common_property_mkd: Optional[str] = None   # Общее имущество в МКД
    common_property_other: Optional[str] = None  # Общее имущество (прочее)
    cadastral_value: Optional[float] = None  # Кадастровая стоимость, руб.
    unit_value: Optional[float] = None      # Удельный показатель, руб./кв.м
    cultural_heritage: Optional[str] = None  # Включение в реестр ОКН
    cancel_date: Optional[str] = None       # Дата снятия с учёта

    def to_dict(self) -> dict:
        def fmt_val(v):
            return v if v is not None and v != "" else "—"

        coords = "Без координат границ" if not self.has_coordinates else "Есть координаты"
        removed = "Снят с государственного кадастрового учета" if self.removed_gcu else "—"

        return {
            "Кадастровый номер помещения": self.cad_number,
            "Координаты границ": coords,
            "Снят с учёта (доп.статус)": removed,
            "Вид объекта": self.obj_type or "—",
            "Дата присвоения": fmt_val(self.registration_date),
            "Вид жилого помещения": fmt_val(self.living_type),
            "Назначение помещения": fmt_val(self.purpose),
            "Номер/тип этажа": fmt_val(self.floor),
            "Площадь, кв.м": self.area if self.area is not None else "—",
            "Адрес": fmt_val(self.address),
            "Статус (кадастровый)": fmt_val(self.cadastral_status),
            "Форма собственности": fmt_val(self.ownership_form),
            "Общее имущество в МКД": fmt_val(self.common_property_mkd),
            "Общее имущество (прочее)": fmt_val(self.common_property_other),
            "Кадастровая стоимость, руб.": self.cadastral_value if self.cadastral_value is not None else "—",
            "Удельный показатель, руб./кв.м": self.unit_value if self.unit_value is not None else "—",
            "Кадастровый номер здания_2": self.building_cad_number,
            "Включение в реестр объектов культурного наследия": fmt_val(self.cultural_heritage),
            "Дата снятия с учёта": fmt_val(self.cancel_date),
        }


@dataclass
class BuildingParseResult:
    """Результат парсинга здания со списком помещений"""
    building_cad_number: str
    building_area: str = "данные отсутствуют"
    building_relevance: str = "данные отсутствуют"
    premises: List[Premise] = field(default_factory=list)
    status: str = "Не обработан"
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_excel_rows(self) -> List[dict]:
        """Преобразование в строки Excel: одна строка = здание + одно помещение"""
        building_base = {
            "Кадастровый номер здания": self.building_cad_number,
            "Площадь здания": self.building_area,
            "Актуальность здания": self.building_relevance,
        }

        if not self.premises:
            empty_premise = {
                "Кадастровый номер помещения": "данные отсутствуют",
                "Координаты границ": "данные отсутствуют",
                "Снят с учёта (доп.статус)": "данные отсутствуют",
                "Вид объекта": "данные отсутствуют",
                "Дата присвоения": "данные отсутствуют",
                "Вид жилого помещения": "данные отсутствуют",
                "Назначение помещения": "данные отсутствуют",
                "Номер/тип этажа": "данные отсутствуют",
                "Площадь, кв.м": "данные отсутствуют",
                "Адрес": "данные отсутствуют",
                "Статус (кадастровый)": "данные отсутствуют",
                "Форма собственности": "данные отсутствуют",
                "Общее имущество в МКД": "данные отсутствуют",
                "Общее имущество (прочее)": "данные отсутствуют",
                "Кадастровая стоимость, руб.": "данные отсутствуют",
                "Удельный показатель, руб./кв.м": "данные отсутствуют",
                "Кадастровый номер здания_2": "данные отсутствуют",
                "Включение в реестр объектов культурного наследия": "данные отсутствуют",
                "Дата снятия с учёта": "данные отсутствуют",
            }
            return [{**building_base, **empty_premise}]

        return [{**building_base, **premise.to_dict()} for premise in self.premises]
