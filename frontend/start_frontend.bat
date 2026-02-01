@echo off
echo ========================================
echo   FRONTEND - ASSISTENTE ESPIRITA
echo ========================================
echo.

cd /d %~dp0

echo [1/2] Ativando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERRO: Ambiente virtual nao encontrado!
    echo.
    echo Execute os seguintes comandos:
    echo   cd %~dp0
    echo   python -m venv venv
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    echo.
    pause
    exit
)

call venv\Scripts\activate

echo [2/2] Iniciando Streamlit...
echo.
echo Frontend estará disponível em: http://localhost:8501
echo.
streamlit run app.py

pause
