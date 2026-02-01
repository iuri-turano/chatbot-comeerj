#!/bin/bash

echo "========================================"
echo "  ASSISTENTE ESPIRITA - STARTUP COMPLETO"
echo "========================================"
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
