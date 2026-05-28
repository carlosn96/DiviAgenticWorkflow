@echo off
REM Wrapper genérico: delega al php.bat en la raíz del proyecto
call "%~dp0..\php.bat" %*
