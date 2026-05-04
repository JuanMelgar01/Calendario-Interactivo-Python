@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHONW=%LocalAppData%\Programs\Python\Python313\pythonw.exe"
if exist "%PYTHONW%" goto run

set "PYTHONW=%LocalAppData%\Programs\Python\Launcher\pyw.exe"
if exist "%PYTHONW%" goto run

echo No se ha encontrado una instalacion compatible de Python.
echo Instala Python 3.13 o ajusta la ruta en este archivo.
pause
exit /b 1

:run
start "" "%PYTHONW%" "%SCRIPT_DIR%ActualizarCalendario.pyw"
