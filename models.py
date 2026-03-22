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
        """Преобразование в словарь для записи в Excel"""
        return {
            "Кадастровый номер (вход)": self.cadastral_number,
            "Вид объекта (участок)": self.object_type or "Нет данных",
            "Вид участка": self.parcel_type or "Нет данных",
            "Адрес (участок)": self.address or "Нет данных",
            "Площадь (участок)": self.area or "Нет данных",
            "ВРИ": self.permitted_use or "Нет данных",
            "Форма собственности (участок)": self.ownership_form or "Нет данных",
            "Кадастровая стоимость (участок)": self.cadastral_value or "Нет данных",
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
        """Преобразование в словарь для записи в Excel"""
        return {
            "Вид объекта (объект)": self.object_type or "Нет данных",
            "Кадастровый номер (объект)": self.cadastral_number or "Нет данных",
            "Назначение": self.purpose or "Нет данных",
            "Площадь (объект)": self.area or "Нет данных",
            "Форма собственности (объект)": self.ownership_form or "Нет данных",
            "Кадастровая стоимость (объект)": self.cadastral_value or "Нет данных",
            "Удельный показатель": self.unit_value or "Нет данных",
            "Этажи": self.floors or "Нет данных",
            "Подземные этажи": self.underground_floors or "Нет данных",
            "Материал стен": self.wall_material or "Нет данных",
            "Завершение": self.completion or "Нет данных",
            "Ввод в эксплуатацию": self.commissioning or "Нет данных",
            "Культурное наследие": self.cultural_heritage or "Нет данных",
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
        Преобразование в строки для Excel
        Если объектов несколько → несколько строк
        Если нет → одна строка с участком
        """
        rows = []

        # Базовые данные участка
        parcel_data = self.parcel.to_dict() if self.parcel else {
            "Кадастровый номер (вход)": self.cadastral_number,
            "Вид объекта (участок)": "Нет данных",
            "Вид участка": "Нет данных",
            "Адрес (участок)": "Нет данных",
            "Площадь (участок)": "Нет данных",
            "ВРИ": "Нет данных",
            "Форма собственности (участок)": "Нет данных",
            "Кадастровая стоимость (участок)": "Нет данных",
        }

        if self.objects:
            # Несколько строк - по одной на каждый объект
            for obj in self.objects:
                row = {**parcel_data, **obj.to_dict()}
                row["Статус обработки"] = self.status
                row["Ошибка"] = self.error or ""
                rows.append(row)
        else:
            # Одна строка с участком без объектов
            row = {**parcel_data}
            # Добавляем пустые поля объекта
            row.update({
                "Вид объекта (объект)": "Нет данных",
                "Кадастровый номер (объект)": "Нет данных",
                "Назначение": "Нет данных",
                "Площадь (объект)": "Нет данных",
                "Форма собственности (объект)": "Нет данных",
                "Кадастровая стоимость (объект)": "Нет данных",
                "Удельный показатель": "Нет данных",
                "Этажи": "Нет данных",
                "Подземные этажи": "Нет данных",
                "Материал стен": "Нет данных",
                "Завершение": "Нет данных",
                "Ввод в эксплуатацию": "Нет данных",
                "Культурное наследие": "Нет данных",
            })
            row["Статус обработки"] = self.status
            row["Ошибка"] = self.error or ""
            rows.append(row)

        return rows
