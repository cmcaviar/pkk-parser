@echo off
REM Скрипт для сборки парсера НСПД в .exe файл
REM Требуется Python 3.11+ и PyInstaller

echo ========================================
echo Сборка парсера НСПД в .exe
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден в PATH
    echo Установите Python 3.11+ и добавьте в PATH
    pause
    exit /b 1
)

echo [OK] Python найден
python --version
echo.

REM Проверка наличия PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [УСТАНОВКА] PyInstaller не найден, устанавливаем...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось установить PyInstaller
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller готов
echo.

REM Установка зависимостей
echo [УСТАНОВКА] Проверка зависимостей...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)
echo [OK] Зависимости установлены
echo.

REM Создание директории для сборки
if not exist "dist" mkdir dist
if not exist "build" mkdir build

REM Сборка .exe с помощью PyInstaller
echo [СБОРКА] Запуск PyInstaller...
echo.

pyinstaller ^
    --name=nspd_parser ^
    --onefile ^
    --windowed ^
    --icon=NONE ^
    --clean ^
    --noconfirm ^
    --add-data "config.py;." ^
    --hidden-import=selenium ^
    --hidden-import=selenium.webdriver ^
    --hidden-import=selenium.webdriver.chrome ^
    --hidden-import=selenium.webdriver.chrome.service ^
    --hidden-import=openpyxl ^
    --hidden-import=openpyxl.cell ^
    --hidden-import=openpyxl.cell._writer ^
    --hidden-import=requests ^
    --hidden-import=urllib3 ^
    --collect-all selenium ^
    main.py

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Сборка не удалась
    pause
    exit /b 1
)

echo.
echo ========================================
echo [УСПЕХ] Сборка завершена!
echo ========================================
echo.
echo Файл: dist\nspd_parser.exe
echo.

REM Проверка наличия файла
if exist "dist\nspd_parser.exe" (
    echo [OK] Исполняемый файл создан
    echo Размер:
    dir "dist\nspd_parser.exe" | find "nspd_parser.exe"
) else (
    echo [ОШИБКА] Файл nspd_parser.exe не найден в dist\
)

echo.
echo Для использования:
echo 1. Скопируйте nspd_parser.exe в нужную директорию
echo 2. Запускайте из командной строки: nspd_parser.exe file.xlsx
echo 3. Или используйте VBA макрос из Excel
echo.

pause
