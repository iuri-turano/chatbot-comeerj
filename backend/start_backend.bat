@echo off
echo ========================================
echo   BACKEND - ASSISTENTE ESPIRITA
echo ========================================
echo.

cd /d %~dp0

echo [1/3] Ativando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERRO: Ambiente virtual nao encontrado!
    echo.
    echo Execute os seguintes comandos:
    echo   cd C:\Users\iurit\chatbot-comeerj\backend
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit
)

call venv\Scripts\activate

echo [2/3] Verificando Ollama...
ollama list
if errorlevel 1 (
    echo.
    echo ❌ ERRO: Ollama nao esta rodando!
    echo Execute em outro terminal: ollama serve
    pause
    exit
)

echo [3/3] Iniciando API...
echo.
python api_server.py

pause