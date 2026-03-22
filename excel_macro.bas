Attribute VB_Name = "NSPDParserModule"
'
' VBA макрос для запуска парсера НСПД из Excel
' Инструкция по установке:
' 1. Откройте Excel файл с данными
' 2. Alt + F11 (открыть редактор VBA)
' 3. Insert -> Module
' 4. Вставьте этот код
' 5. Создайте кнопку на листе и привяжите к процедуре RunNSPDParser
'

Option Explicit

' Константы для настройки
Private Const PARSER_NAME As String = "nspd_parser.exe"    ' Имя .exe файла
Private Const PYTHON_SCRIPT As String = "main.py"           ' Имя Python скрипта
Private Const VBS_SCRIPT As String = "run_hidden.vbs"       ' VBS скрипт для скрытого запуска
Private Const TIMEOUT_SECONDS As Long = 3600                ' Таймаут 1 час

' Основная процедура запуска парсера
Public Sub RunNSPDParser()
    On Error GoTo ErrorHandler

    Dim workbookPath As String
    Dim parserPath As String
    Dim vbsPath As String
    Dim command As String
    Dim result As Long
    Dim startTime As Double
    Dim timeoutReached As Boolean

    ' Отключение обновления экрана
    Application.ScreenUpdating = False
    Application.Calculation = xlCalculationManual

    ' Сохранение книги перед запуском
    If Not ThisWorkbook.Saved Then
        MsgBox "Книга будет сохранена перед запуском парсера.", vbInformation, "НСПД Парсер"
        ThisWorkbook.Save
    End If

    ' Получение пути к текущей книге
    workbookPath = ThisWorkbook.FullName

    ' Поиск парсера
    parserPath = FindParser(ThisWorkbook.Path)

    If parserPath = "" Then
        MsgBox "Парсер не найден!" & vbCrLf & vbCrLf & _
               "Ожидается один из файлов:" & vbCrLf & _
               "- " & PARSER_NAME & vbCrLf & _
               "- " & PYTHON_SCRIPT & vbCrLf & vbCrLf & _
               "В директории: " & ThisWorkbook.Path, _
               vbCritical, "НСПД Парсер - Ошибка"
        GoTo CleanUp
    End If

    ' Информирование пользователя
    Dim response As VbMsgBoxResult
    response = MsgBox("Запустить парсинг НСПД?" & vbCrLf & vbCrLf & _
                      "Файл: " & ThisWorkbook.Name & vbCrLf & _
                      "Парсер: " & Dir(parserPath) & vbCrLf & vbCrLf & _
                      "Процесс может занять продолжительное время.", _
                      vbQuestion + vbYesNo, "НСПД Парсер")

    If response <> vbYes Then
        MsgBox "Парсинг отменен пользователем.", vbInformation, "НСПД Парсер"
        GoTo CleanUp
    End If

    ' Закрытие книги для предотвращения конфликтов
    Dim shouldReopen As Boolean
    shouldReopen = True

    ' Формирование команды запуска
    If LCase(Right(parserPath, 4)) = ".exe" Then
        ' Запуск .exe
        command = """" & parserPath & """ """ & workbookPath & """"
    Else
        ' Запуск через Python
        command = "python """ & parserPath & """ """ & workbookPath & """"
    End If

    ' Проверка наличия VBS скрипта для скрытого запуска
    vbsPath = ThisWorkbook.Path & "\" & VBS_SCRIPT
    If Dir(vbsPath) <> "" Then
        ' Запуск через VBS (скрытое окно)
        command = "cscript //nologo """ & vbsPath & """ """ & workbookPath & """"
        result = RunCommand(command, waitForCompletion:=True, showWindow:=0)
    Else
        ' Прямой запуск (с окном консоли)
        result = RunCommand(command, waitForCompletion:=True, showWindow:=1)
    End If

    ' Обработка результата
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic

    If result = 0 Then
        ' Успех - обновление книги
        ThisWorkbook.RefreshAll
        DoEvents
        Application.CalculateFullRebuild

        MsgBox "Парсинг успешно завершен!" & vbCrLf & vbCrLf & _
               "Результаты сохранены в листе 'Результат'." & vbCrLf & _
               "Проверьте данные и столбец 'Статус обработки'.", _
               vbInformation, "НСПД Парсер - Успех"
    Else
        MsgBox "Парсинг завершен с ошибками." & vbCrLf & vbCrLf & _
               "Код завершения: " & result & vbCrLf & _
               "Проверьте файл parser.log для деталей.", _
               vbExclamation, "НСПД Парсер - Предупреждение"
    End If

CleanUp:
    ' Восстановление настроек Excel
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic
    Exit Sub

ErrorHandler:
    Application.ScreenUpdating = True
    Application.Calculation = xlCalculationAutomatic

    MsgBox "Произошла ошибка:" & vbCrLf & vbCrLf & _
           "Ошибка " & Err.Number & ": " & Err.Description & vbCrLf & vbCrLf & _
           "Проверьте:" & vbCrLf & _
           "- Наличие парсера в директории книги" & vbCrLf & _
           "- Наличие листа 'Входные данные'" & vbCrLf & _
           "- Права доступа к файлу", _
           vbCritical, "НСПД Парсер - Ошибка"
End Sub

' Поиск парсера в указанной директории
Private Function FindParser(basePath As String) As String
    Dim exePath As String
    Dim pyPath As String

    ' Поиск .exe
    exePath = basePath & "\" & PARSER_NAME
    If Dir(exePath) <> "" Then
        FindParser = exePath
        Exit Function
    End If

    ' Поиск .py
    pyPath = basePath & "\" & PYTHON_SCRIPT
    If Dir(pyPath) <> "" Then
        FindParser = pyPath
        Exit Function
    End If

    ' Не найдено
    FindParser = ""
End Function

' Выполнение команды в Shell
Private Function RunCommand(command As String, _
                           Optional waitForCompletion As Boolean = True, _
                           Optional showWindow As Long = 1) As Long
    Dim wsh As Object
    Dim result As Long

    Set wsh = CreateObject("WScript.Shell")

    ' Запуск команды
    ' showWindow: 0 = скрытое, 1 = нормальное, 2 = минимизированное
    result = wsh.Run(command, showWindow, waitForCompletion)

    Set wsh = Nothing
    RunCommand = result
End Function

' Процедура для создания флага остановки
Public Sub CreateStopFlag()
    Dim flagPath As String
    Dim fileNum As Integer

    flagPath = ThisWorkbook.Path & "\stop.flag"

    On Error Resume Next
    fileNum = FreeFile
    Open flagPath For Output As #fileNum
    Print #fileNum, "STOP"
    Close #fileNum

    If Err.Number = 0 Then
        MsgBox "Флаг остановки создан: stop.flag" & vbCrLf & vbCrLf & _
               "Парсер остановится после обработки текущего номера." & vbCrLf & _
               "Для возобновления удалите этот файл.", _
               vbInformation, "НСПД Парсер"
    Else
        MsgBox "Ошибка создания флага: " & Err.Description, vbCritical, "НСПД Парсер"
    End If
    On Error GoTo 0
End Sub

' Процедура для удаления флага остановки
Public Sub RemoveStopFlag()
    Dim flagPath As String

    flagPath = ThisWorkbook.Path & "\stop.flag"

    On Error Resume Next
    Kill flagPath

    If Err.Number = 0 Then
        MsgBox "Флаг остановки удален.", vbInformation, "НСПД Парсер"
    Else
        MsgBox "Флаг не найден или уже удален.", vbInformation, "НСПД Парсер"
    End If
    On Error GoTo 0
End Sub

' Процедура для просмотра логов
Public Sub ViewLogs()
    Dim logPath As String
    Dim wsh As Object

    logPath = ThisWorkbook.Path & "\parser.log"

    If Dir(logPath) = "" Then
        MsgBox "Файл логов не найден: parser.log", vbInformation, "НСПД Парсер"
        Exit Sub
    End If

    ' Открытие в Notepad
    Set wsh = CreateObject("WScript.Shell")
    wsh.Run "notepad.exe """ & logPath & """", 1, False
    Set wsh = Nothing
End Sub

'
' ИНСТРУКЦИЯ ПО ДОБАВЛЕНИЮ КНОПОК В EXCEL:
'
' 1. Перейдите на лист с данными
' 2. Вкладка "Разработчик" -> Вставить -> Кнопка (элемент управления формы)
' 3. Нарисуйте кнопку на листе
' 4. В появившемся окне выберите макрос "RunNSPDParser"
' 5. ПКМ на кнопке -> Изменить текст -> "Запустить парсинг НСПД"
'
' Дополнительные кнопки:
' - CreateStopFlag - создать флаг остановки парсинга
' - RemoveStopFlag - удалить флаг остановки
' - ViewLogs - просмотр логов парсинга
'
