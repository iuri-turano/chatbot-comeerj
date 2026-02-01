@echo off
echo ========================================
echo   ASSISTENTE ESPIRITA - STARTUP COMPLETO
echo ========================================
echo.

REM Detect OS and show configuration
echo Sistema: Windows
echo Hardware: Ryzen 7 5700X + 32GB RAM + RTX 3070 8GB (esperado)
echo Modelo: llama3.1:8b
echo Raciocinio: Chain-of-Thought ativado
echo Otimizado para RTX 3070 8GB
echo.

REM Check if Ollama is running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Ollama esta rodando
) else (
    echo Ollama nao encontrado. Tentando iniciar...
    start /B ollama serve
    timeout /t 3 /nobreak > nul

    REM Check again
    tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo Ollama iniciado com sucesso!
    ) else (
        echo AVISO: Ollama nao esta rodando. Instale em https://ollama.ai
    )
)
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
