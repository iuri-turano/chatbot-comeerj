#!/bin/bash

echo "========================================"
echo "  FRONTEND - ASSISTENTE ESPIRITA"
echo "========================================"
echo ""

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[1/2] Ativando ambiente virtual..."
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ ERRO: Ambiente virtual não encontrado!"
    echo ""
    echo "Execute os seguintes comandos:"
    echo "  cd $(pwd)"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    read -p "Pressione ENTER para sair..."
    exit 1
fi

source venv/bin/activate

echo "[2/2] Iniciando Streamlit..."
echo ""
echo "Frontend estará disponível em: http://localhost:8501"
echo ""
streamlit run app.py

read -p "Pressione ENTER para sair..."
