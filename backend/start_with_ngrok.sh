#!/bin/bash

echo "========================================"
echo "  BACKEND + NGROK"
echo "========================================"
echo ""

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "[OK] .env carregado"
else
    echo "[ERRO] Arquivo .env não encontrado!"
    echo "Crie o arquivo backend/.env com:"
    echo "  NGROK_AUTHTOKEN=seu_token_aqui"
    exit 1
fi

# Check ngrok auth token
if [ -z "$NGROK_AUTHTOKEN" ] || [ "$NGROK_AUTHTOKEN" = "your_ngrok_auth_token_here" ]; then
    echo "[ERRO] NGROK_AUTHTOKEN não configurado!"
    echo "Edite backend/.env e adicione seu token do ngrok."
    exit 1
fi

# Configure ngrok auth
echo "[1/3] Configurando ngrok..."
ngrok config add-authtoken "$NGROK_AUTHTOKEN"

# Start backend in background
echo "[2/3] Iniciando API..."
source venv/bin/activate
python api_server.py &
API_PID=$!

echo "Aguardando backend iniciar..."
sleep 5

# Start ngrok tunnel
echo "[3/3] Criando tunnel ngrok..."
echo ""
echo "========================================"
echo "  PRONTO!"
echo "========================================"
echo ""
echo "1. Copie a URL do ngrok (https://...)"
echo "2. Configure no frontend/.streamlit/secrets.toml"
echo "   API_URL = \"https://sua-url.ngrok-free.app\""
echo ""

ngrok http 8000

# Cleanup: kill backend when ngrok exits
kill $API_PID 2>/dev/null
