#!/bin/bash

echo "========================================"
echo "  ASSISTENTE ESPIRITA - STARTUP COMPLETO"
echo "========================================"
echo ""

# Detect OS and show configuration
OS_TYPE=$(uname -s)
case "$OS_TYPE" in
    Darwin*)
        echo "🖥️  Sistema: macOS"
        echo "💾 Hardware: Mac M4 16GB (esperado)"
        echo "🤖 Modelo: llama3.2:3b"
        echo "🧠 Raciocínio: Chain-of-Thought ativado"
        echo "✨ Otimizado para M4 com 16GB RAM"
        ;;
    Linux*)
        echo "🖥️  Sistema: Linux"
        echo "🤖 Modelo: llama3.2:3b (padrão)"
        echo "🧠 Raciocínio: Chain-of-Thought ativado"
        ;;
    *)
        echo "🖥️  Sistema: $OS_TYPE"
        echo "🤖 Modelo: llama3.2:3b"
        echo "🧠 Raciocínio: Chain-of-Thought ativado"
        ;;
esac
echo ""

# Check if Ollama is running
if command -v ollama &> /dev/null; then
    if pgrep -x "ollama" > /dev/null; then
        echo "✅ Ollama está rodando"
    else
        echo "⚠️  Ollama não está rodando. Por favor, inicie o Ollama primeiro."
        echo "   Execute: ollama serve"
    fi
else
    echo "⚠️  Ollama não encontrado. Instale com: brew install ollama"
fi
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Start backend in new terminal
echo "Iniciando Backend..."
osascript -e "tell app \"Terminal\" to do script \"cd '$SCRIPT_DIR/backend' && ./start_backend.sh\""

echo "Aguardando backend iniciar..."
sleep 5

# Start frontend in new terminal
echo "Iniciando Frontend..."
osascript -e "tell app \"Terminal\" to do script \"cd '$SCRIPT_DIR/frontend' && ./start_frontend.sh\""

echo ""
echo "========================================"
echo "  Sistema inicializado!"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:8501"
echo "========================================"
echo ""
echo "Os serviços estão rodando em terminais separados."
echo "Feche este terminal se desejar."
