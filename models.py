"""
Модели данных для участков и объектов недвижимости
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
    purpose: Optional[str] = None  # Назначение
    area: Optional[str] = None  # Площадь
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
            "Назначение": self.purpose or "-",
            "Площадь общая": self.area or "-",
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

        # Пустые данные объекта (колонки I-U)
        empty_object = {
            "Вид объекта недвижимости_obj": "-",
            "Кадастровый номер_obj": "-",
            "Назначение": "-",
            "Площадь общая": "-",
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
