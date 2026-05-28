@echo off
REM Wrapper genérico: delega al mysql.bat en la raíz del proyecto
call "%~dp0..\mysql.bat" %*
