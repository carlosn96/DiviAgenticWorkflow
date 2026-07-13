@echo off
REM Wrapper genérico: delega al wp.bat en la raíz del proyecto
call "%~dp0..\wp.bat" %*
