' VBScript для скрытого запуска парсера без окна консоли
' Использование: cscript //nologo run_hidden.vbs "путь\к\файлу.xlsx"

Option Explicit

Dim objShell, objFSO
Dim excelFile, scriptDir, pythonScript, exeFile
Dim command, exitCode

' Создание объектов
Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Получение аргумента (путь к Excel файлу)
If WScript.Arguments.Count = 0 Then
    WScript.Echo "Ошибка: не указан путь к Excel файлу"
    WScript.Echo "Использование: run_hidden.vbs <путь_к_файлу.xlsx>"
    WScript.Quit 1
End If

excelFile = WScript.Arguments(0)

' Проверка существования файла
If Not objFSO.FileExists(excelFile) Then
    WScript.Echo "Ошибка: файл не найден: " & excelFile
    WScript.Quit 1
End If

' Получение директории скрипта
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Поиск парсера (.exe или .py)
exeFile = objFSO.BuildPath(scriptDir, "nspd_parser.exe")
pythonScript = objFSO.BuildPath(scriptDir, "main.py")

' Формирование команды запуска
If objFSO.FileExists(exeFile) Then
    ' Запуск .exe
    command = """" & exeFile & """ """ & excelFile & """"
ElseIf objFSO.FileExists(pythonScript) Then
    ' Запуск Python скрипта
    command = "python """ & pythonScript & """ """ & excelFile & """"
Else
    WScript.Echo "Ошибка: парсер не найден"
    WScript.Echo "Ожидается: nspd_parser.exe или main.py в " & scriptDir
    WScript.Quit 1
End If

' Запуск команды в скрытом режиме (0 = скрытое окно, True = ожидать завершения)
exitCode = objShell.Run(command, 0, True)

' Очистка объектов
Set objFSO = Nothing
Set objShell = Nothing

' Возврат кода завершения
WScript.Quit exitCode
