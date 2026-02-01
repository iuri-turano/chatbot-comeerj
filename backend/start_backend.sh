#!/bin/bash

echo "========================================"
echo "  BACKEND - ASSISTENTE ESPIRITA"
echo "========================================"
echo ""

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[1/3] Ativando ambiente virtual..."
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

echo "[2/3] Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ ERRO: Ollama não encontrado!"
    echo "Instale em: https://ollama.com/download"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

ollama list
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ERRO: Ollama não está rodando!"
    echo "Execute em outro terminal: ollama serve"
    read -p "Pressione ENTER para sair..."
    exit 1
fi

echo "[3/3] Iniciando API..."
echo ""
python api_server.py

read -p "Pressione ENTER para sair..."
