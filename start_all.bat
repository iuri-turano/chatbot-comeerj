@echo off
echo ========================================
echo   ASSISTENTE ESPIRITA - STARTUP COMPLETO
echo ========================================
echo.

echo Iniciando Backend...
start cmd /k "cd /d %~dp0\backend && call start_backend.bat"

echo Aguardando backend iniciar...
timeout /t 5 /nobreak > nul

echo Iniciando Frontend...
start cmd /k "cd /d %~dp0\frontend && call start_frontend.bat"

echo.
echo ========================================
echo   Sistema inicializado!
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:8501
echo ========================================
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause > nul
