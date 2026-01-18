@echo off
echo ========================================
echo   BACKEND + NGROK
echo ========================================
echo.

echo [1/2] Iniciando API...
start "API Backend" cmd /k "cd /d %~dp0 && start_backend.bat"

timeout /t 10 /nobreak

echo [2/2] Criando tunnel ngrok...
start "ngrok Tunnel" cmd /k "ngrok http 8000"

echo.
echo ========================================
echo   PRONTO!
echo ========================================
echo.
echo 1. Copie a URL do ngrok (https://...)
echo 2. Configure no frontend/.streamlit/secrets.toml
echo 3. Deploy o frontend no Streamlit Cloud
echo.
pause