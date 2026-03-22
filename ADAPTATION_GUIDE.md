# Руководство по адаптации под реальный НСПД

Этот документ описывает, как адаптировать парсер под реальную структуру API и веб-интерфейса сайта https://nspd.gov.ru

## Этап 1: Исследование API

### 1.1 Открытие DevTools

1. Откройте https://nspd.gov.ru в Chrome
2. Нажмите `F12` (DevTools)
3. Перейдите на вкладку **Network**
4. Включите фильтр **XHR** или **Fetch**

### 1.2 Выполнение тестового поиска

1. Введите тестовый кадастровый номер в форму поиска
2. Нажмите "Найти"
3. В DevTools найдите запросы к API
4. Изучите:
   - URL endpoints
   - HTTP методы (GET/POST)
   - Query параметры
   - Request payload (для POST)
   - Response структуру (JSON)

### 1.3 Документирование структуры

Запишите:
```
SEARCH ENDPOINT:
URL: /api/v1/search (пример)
Method: GET / POST
Parameters:
  - cadastralNumber: string
  - objectType: "parcel" | "building"
Response:
{
  "id": "12345",
  "cadastralNumber": "77:01:0001001:1",
  "type": "parcel",
  ...
}

DETAILS ENDPOINT:
URL: /api/v1/object/{id}
Method: GET
Response:
{
  "id": "12345",
  "address": "г. Москва, ул. Ленина, д. 1",
  "area": 1000.5,
  ...
}

OBJECTS ON PARCEL ENDPOINT:
URL: /api/v1/parcel/{id}/buildings
Method: GET
Response:
{
  "buildings": [
    {
      "cadastralNumber": "77:01:0001001:1001",
      "purpose": "Жилое",
      ...
    }
  ]
}
```

## Этап 2: Адаптация API клиента

### 2.1 Обновление endpoints в `config.py`

```python
@dataclass
class APIConfig:
    base_url: str = "https://nspd.gov.ru"

    # ⚠️ ОБНОВИТЕ РЕАЛЬНЫЕ ENDPOINTS:
    search_endpoint: str = "/api/v1/search"  # Ваш реальный endpoint
    details_endpoint: str = "/api/v1/object"  # Ваш реальный endpoint
    objects_endpoint: str = "/api/v1/parcel/{id}/buildings"  # Ваш реальный endpoint
```

### 2.2 Адаптация методов в `api_client.py`

#### Метод `search_cadastral_number`:

```python
def search_cadastral_number(self, cadastral_number: str) -> Optional[Dict[str, Any]]:
    logger.info(f"Поиск кадастрового номера: {cadastral_number}")

    # ⚠️ ОБНОВИТЕ URL И ПАРАМЕТРЫ:
    url = f"{config.api.base_url}{config.api.search_endpoint}"

    # Вариант 1: GET с query параметрами
    params = {
        'cadastralNumber': cadastral_number,  # Проверьте реальное имя параметра!
        'type': 'parcel'  # Если требуется
    }
    response = self._make_request('GET', url, params=params)

    # Вариант 2: POST с JSON body
    # payload = {
    #     'cadastralNumber': cadastral_number,
    #     'searchType': 'full'
    # }
    # response = self._make_request('POST', url, json=payload)

    if not response:
        return None

    try:
        data = response.json()
        # ⚠️ ПРОВЕРЬТЕ СТРУКТУРУ ОТВЕТА:
        # Может быть data['result'], data['data'], или просто data
        return data
    except ValueError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return None
```

#### Метод `parse_parcel_data`:

```python
def parse_parcel_data(self, data: Dict[str, Any], cadastral_number: str) -> Parcel:
    # ⚠️ ОБНОВИТЕ ПОД РЕАЛЬНУЮ СТРУКТУРУ JSON:

    # Изучите реальный JSON ответ и адаптируйте:
    return Parcel(
        cadastral_number=cadastral_number,

        # Примеры - замените на реальные пути:
        object_type=data.get('objectType') or data.get('type', 'Нет данных'),
        parcel_type=data.get('parcelCategory') or data.get('category', 'Нет данных'),

        # Адрес может быть вложенным объектом:
        address=data.get('address', {}).get('fullAddress', 'Нет данных'),
        # Или простой строкой:
        # address=data.get('address', 'Нет данных'),

        # Площадь может быть числом - конвертируем в строку:
        area=str(data.get('areaValue') or data.get('area', 'Нет данных')),

        # ВРИ может быть массивом или объектом:
        permitted_use=self._extract_permitted_use(data),

        # Форма собственности:
        ownership_form=data.get('ownershipType', 'Нет данных'),

        # Кадастровая стоимость:
        cadastral_value=self._format_value(data.get('cadastralCost'))
    )

def _extract_permitted_use(self, data: Dict) -> str:
    """Извлечение ВРИ из различных форматов"""
    # Вариант 1: Простая строка
    if 'permittedUse' in data and isinstance(data['permittedUse'], str):
        return data['permittedUse']

    # Вариант 2: Объект с полем name
    if 'permittedUse' in data and isinstance(data['permittedUse'], dict):
        return data['permittedUse'].get('name', 'Нет данных')

    # Вариант 3: Массив объектов
    if 'permittedUses' in data and isinstance(data['permittedUses'], list):
        if len(data['permittedUses']) > 0:
            return data['permittedUses'][0].get('name', 'Нет данных')

    return 'Нет данных'

def _format_value(self, value) -> str:
    """Форматирование числовых значений"""
    if value is None:
        return 'Нет данных'
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".replace(',', ' ')
    return str(value)
```

#### Метод `parse_object_data`:

```python
def parse_object_data(self, data: Dict[str, Any]) -> RealtyObject:
    # ⚠️ ОБНОВИТЕ ПОД РЕАЛЬНУЮ СТРУКТУРУ JSON:

    return RealtyObject(
        object_type=data.get('objectType', 'Нет данных'),
        cadastral_number=data.get('cadastralNumber', 'Нет данных'),
        purpose=data.get('purposeName') or data.get('purpose', 'Нет данных'),
        area=str(data.get('area', 'Нет данных')),
        ownership_form=data.get('ownershipForm', 'Нет данных'),
        cadastral_value=self._format_value(data.get('cadastralValue')),
        unit_value=self._format_value(data.get('specificValue')),

        # Этажность может быть объектом:
        floors=str(data.get('floors', {}).get('above', 'Нет данных')),
        underground_floors=str(data.get('floors', {}).get('underground', 'Нет данных')),

        wall_material=data.get('wallMaterial', {}).get('name', 'Нет данных'),
        completion=str(data.get('completionYear', 'Нет данных')),
        commissioning=str(data.get('commissioningDate', 'Нет данных')),
        cultural_heritage=data.get('culturalHeritage', 'Нет')
    )
```

## Этап 3: Адаптация Selenium парсера

### 3.1 Изучение HTML структуры

1. Откройте страницу объекта в браузере
2. ПКМ → **Просмотреть код** (`Ctrl+Shift+C`)
3. Изучите:
   - Классы и ID элементов
   - Структуру форм
   - Таблицы с данными
   - Списки объектов

### 3.2 Обновление селекторов в `selenium_fallback.py`

#### Метод `search_cadastral_number`:

```python
def search_cadastral_number(self, cadastral_number: str) -> bool:
    try:
        self.driver.get(config.api.base_url)
        self._wait_random()

        # ⚠️ ОБНОВИТЕ СЕЛЕКТОР ПОЛЯ ПОИСКА:
        # Варианты поиска:
        # 1. По placeholder
        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='кадастр']"))
        )

        # 2. По имени/ID
        # search_input = self.driver.find_element(By.ID, "cadastralNumberInput")
        # search_input = self.driver.find_element(By.NAME, "cadastralNumber")

        # 3. По классу
        # search_input = self.driver.find_element(By.CLASS_NAME, "search-input")

        search_input.clear()
        search_input.send_keys(cadastral_number)
        self._wait_random(0.5, 1.0)

        # ⚠️ ОБНОВИТЕ СЕЛЕКТОР КНОПКИ:
        # Варианты:
        # 1. По типу кнопки
        search_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")

        # 2. По классу
        # search_button = self.driver.find_element(By.CLASS_NAME, "search-btn")

        # 3. По тексту кнопки
        # search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Найти')]")

        search_button.click()

        # ⚠️ ОБНОВИТЕ СЕЛЕКТОР РЕЗУЛЬТАТОВ:
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "result-item"))
            # Или:
            # EC.presence_of_element_located((By.CSS_SELECTOR, ".search-results .item"))
        )

        return True

    except TimeoutException:
        return False
```

#### Метод `get_parcel_data`:

```python
def get_parcel_data(self, cadastral_number: str) -> Optional[Parcel]:
    try:
        parcel = Parcel(cadastral_number=cadastral_number)

        def safe_get_text(selector: str, default: str = "Нет данных") -> str:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                return element.text.strip() or default
            except NoSuchElementException:
                return default

        # ⚠️ ОБНОВИТЕ СЕЛЕКТОРЫ ПОД РЕАЛЬНУЮ СТРАНИЦУ:

        # Способ 1: Прямые селекторы
        parcel.object_type = safe_get_text(".object-type")
        parcel.address = safe_get_text(".address")

        # Способ 2: По меткам (labels)
        # parcel.address = self._get_field_by_label("Адрес:")

        # Способ 3: Из таблицы
        # parcel.area = self._get_table_value("Площадь")

        return parcel

    except Exception as e:
        logger.error(f"Ошибка извлечения данных: {e}")
        return None

def _get_field_by_label(self, label: str) -> str:
    """Получение значения по метке поля"""
    try:
        # Ищем элемент с текстом метки
        label_elem = self.driver.find_element(
            By.XPATH,
            f"//label[contains(text(), '{label}')]"
        )
        # Получаем следующий элемент (значение)
        value_elem = label_elem.find_element(By.XPATH, "following-sibling::*[1]")
        return value_elem.text.strip() or "Нет данных"
    except NoSuchElementException:
        return "Нет данных"

def _get_table_value(self, row_name: str) -> str:
    """Получение значения из таблицы по названию строки"""
    try:
        # Ищем строку таблицы с нужным названием
        row = self.driver.find_element(
            By.XPATH,
            f"//tr[td[contains(text(), '{row_name}')]]"
        )
        # Берем второй столбец (значение)
        value = row.find_element(By.XPATH, "./td[2]")
        return value.text.strip() or "Нет данных"
    except NoSuchElementException:
        return "Нет данных"
```

## Этап 4: Тестирование

### 4.1 Модульное тестирование

Создайте тестовый скрипт `test_api.py`:

```python
from api_client import NSPDAPIClient

# Тест поиска
client = NSPDAPIClient()
result = client.search_cadastral_number("77:01:0001001:1")
print("Search result:", result)

# Тест детальных данных
if result:
    details = client.get_parcel_details(result['id'])
    print("Details:", details)

client.close()
```

### 4.2 Тестирование Selenium

Создайте `test_selenium.py`:

```python
from selenium_fallback import SeleniumParser

with SeleniumParser() as parser:
    # Отключите headless для визуального контроля
    from config import config
    config.selenium.headless = False

    found = parser.search_cadastral_number("77:01:0001001:1")
    print("Found:", found)

    if found:
        parcel = parser.get_parcel_data("77:01:0001001:1")
        print("Parcel:", parcel)
```

### 4.3 Полное тестирование

```bash
# Создайте тестовый Excel с 1-2 номерами
python main.py test.xlsx --log-level DEBUG

# Проверьте логи
cat parser.log

# Проверьте результаты в Excel
```

## Этап 5: Частые проблемы и решения

### Проблема: "Element not found"

**Решение:**
1. Увеличьте таймауты в `config.py`
2. Добавьте явные ожидания (WebDriverWait)
3. Проверьте селекторы в DevTools

### Проблема: "SSL Error" даже с verify=False

**Решение:**
```python
# В api_client.py
self.session.verify = False
self.session.cert = None

# Добавьте:
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

### Проблема: "API возвращает 403/401"

**Решение:**
```python
# Возможно требуется авторизация или специальные headers
self.session.headers.update({
    'User-Agent': config.selenium.user_agent,
    'Referer': config.api.base_url,
    'X-Requested-With': 'XMLHttpRequest',  # Для AJAX запросов
    # Возможно потребуется токен:
    # 'Authorization': 'Bearer YOUR_TOKEN',
})
```

### Проблема: Данные загружаются динамически (AJAX)

**Решение в Selenium:**
```python
# Ждем загрузки данных
WebDriverWait(self.driver, 10).until(
    EC.presence_of_element_located((By.CLASS_NAME, "loaded"))
)

# Или ждем исчезновения loader'а
WebDriverWait(self.driver, 10).until_not(
    EC.presence_of_element_located((By.CLASS_NAME, "loading"))
)
```

## Этап 6: Оптимизация

### Кэширование результатов

Добавьте в `parser_core.py`:

```python
import pickle
from pathlib import Path

class NSPDParser:
    def __init__(self):
        self.cache_file = Path("cache.pkl")
        self.cache = self._load_cache()

    def _load_cache(self):
        if self.cache_file.exists():
            with open(self.cache_file, 'rb') as f:
                return pickle.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)

    def parse_single(self, cadastral_number: str):
        # Проверка кэша
        if cadastral_number in self.cache:
            logger.info(f"Используется кэш для {cadastral_number}")
            return self.cache[cadastral_number]

        # Обычный парсинг
        result = self._parse_via_api(cadastral_number)

        # Сохранение в кэш
        self.cache[cadastral_number] = result
        self._save_cache()

        return result
```

## Чеклист готовности

- [ ] Изучена структура API через DevTools
- [ ] Обновлены endpoints в `config.py`
- [ ] Адаптирован `search_cadastral_number` в `api_client.py`
- [ ] Адаптирован `parse_parcel_data` в `api_client.py`
- [ ] Адаптирован `parse_object_data` в `api_client.py`
- [ ] Обновлены селекторы в `selenium_fallback.py`
- [ ] Проведено тестирование на 3-5 кадастровых номерах
- [ ] Проверены логи на наличие ошибок
- [ ] Результаты в Excel корректны
- [ ] Документированы особенности API

**После выполнения чеклиста парсер готов к продакшену!** ✅
