Sub LoadNSPDData()
    '
    ' Макрос для загрузки данных НСПД из Python
    ' Вызывает Python скрипт через xlwings
    '

    Dim pythonPath As String
    Dim scriptPath As String
    Dim result As Integer

    ' Определяем путь к Python и скрипту
    ' ВАЖНО: Измените эти пути на свои!
    pythonPath = "python"  ' Если Python в PATH, иначе укажите полный путь
    scriptPath = ThisWorkbook.Path & "\run_from_excel.py"

    ' Проверяем существование скрипта
    If Dir(scriptPath) = "" Then
        MsgBox "Файл run_from_excel.py не найден!" & vbCrLf & _
               "Путь: " & scriptPath, vbCritical, "Ошибка"
        Exit Sub
    End If

    ' Показываем сообщение о начале обработки
    Application.StatusBar = "Запуск Python скрипта..."
    Application.ScreenUpdating = False

    ' Запускаем Python скрипт
    On Error GoTo ErrorHandler

    ' Используем RunPython из xlwings
    RunPython "import run_from_excel; run_from_excel.load_nspd_data()"

    Application.StatusBar = False
    Application.ScreenUpdating = True

    Exit Sub

ErrorHandler:
    Application.StatusBar = False
    Application.ScreenUpdating = True

    MsgBox "Ошибка при выполнении скрипта:" & vbCrLf & vbCrLf & _
           Err.Description & vbCrLf & vbCrLf & _
           "Убедитесь что:" & vbCrLf & _
           "1. Установлен Python" & vbCrLf & _
           "2. Установлен xlwings: pip install xlwings" & vbCrLf & _
           "3. Выполнена команда: xlwings quickstart myproject", _
           vbCritical, "Ошибка"
End Sub

Sub TestXLWings()
    '
    ' Тестовый макрос для проверки работы xlwings
    '
    On Error GoTo ErrorHandler

    RunPython "import sys; import xlwings as xw; xw.apps.active.alert('xlwings работает!\\n\\nПуть к Python: ' + sys.executable, title='Тест')"

    Exit Sub

ErrorHandler:
    MsgBox "xlwings не настроен!" & vbCrLf & vbCrLf & _
           "Установите: pip install xlwings" & vbCrLf & _
           "Затем выполните: xlwings addin install", _
           vbCritical, "Ошибка"
End Sub
