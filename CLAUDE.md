# 🤖 CLAUDE.md - Assistente Espírita

## 📋 Visão Geral do Projeto

**Chatbot Espírita com RAG (Retrieval-Augmented Generation)** - Um assistente conversacional inteligente especializado em obras espíritas que utiliza busca semântica e geração de respostas baseadas em fontes autênticas.

### 🎯 Objetivo Principal

Criar uma experiência similar ao **Perplexity Chat** onde:
- O usuário vê **em tempo real** o que o sistema está fazendo
- Mostra quais **livros estão sendo consultados**
- Exibe as **fontes** das informações com priorização inteligente
- Oferece **respostas contextualizadas** baseadas em obras espíritas autênticas

### 🌍 Idioma e Localização

- **Interface do Usuário**: PORTUGUÊS BRASILEIRO (pt-BR)
- **Respostas da IA**: SEMPRE em PORTUGUÊS BRASILEIRO
- **Livros**: Obras espíritas em português (Codificação de Allan Kardec)

### ✨ Características Principais

#### 1. Inteligência Contextual
- ✅ **Identifica e recusa perguntas FORA DE CONTEXTO** (não relacionadas ao Espiritismo) - **IMPLEMENTADO 2025-02-01**
- ✅ **Correlaciona contexto** através do histórico de conversa
- 🔴 **Múltiplas buscas automáticas** quando necessário para respostas mais completas - **PENDENTE** (ver [proposta 002](docs/proposed/002-multiple-search-capability.md))
- ✅ **Priorização inteligente de fontes** (O Livro dos Espíritos tem peso máximo)

#### 2. Interface Estilo Perplexity
- 🟡 **Indicadores de processo em tempo real** - **50% IMPLEMENTADO** (backend pronto, frontend pendente):
  - "Criando modelo LLM..." (10% concluído) - Backend ✅ | Frontend 🔴
  - "Buscando nos livros espíritas..." (30% concluído) - Backend ✅ | Frontend 🔴
  - "Construindo contexto..." (50% concluído) - Backend ✅ | Frontend 🔴
  - "Gerando resposta..." (70% concluído) - Backend ✅ | Frontend 🔴
  - "Formatando resposta..." (90% concluído) - Backend ✅ | Frontend 🔴
  - Ver [proposta 003](docs/proposed/003-real-time-progress-indicators.md)
- ✅ **Exibe fontes consultadas** com badges de prioridade
- ✅ **Streaming de respostas** (texto aparece progressivamente)
- ✅ **Status do backend** visível para o usuário

#### 3. Sistema de Priorização de Fontes

**Hierarquia de Prioridades:**

| Prioridade | Peso | Obras | Badge |
|-----------|------|-------|-------|
| 🥇 **MÁXIMA** | 100 | O Livro dos Espíritos | `PRIORIDADE MÁXIMA` |
| 🥈 **FUNDAMENTAL** | 70 | Evangelho, Médiuns, Gênese, Céu e Inferno, O que é o Espiritismo | `OBRA FUNDAMENTAL` |
| 🥉 **COMPLEMENTAR** | 40 | Revista Espírita (1858-1869) | `COMPLEMENTAR` |
| 📄 **OUTRAS** | 10 | Demais obras | `OUTRAS OBRAS` |

## 🏗️ Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                      │
│  - Interface em Português BR                                 │
│  - Chat com histórico contextual                             │
│  - Indicadores de processo em tempo real                     │
│  - Exibição de fontes com badges de prioridade              │
│  - Sistema de feedback                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP/API REST
                  │ /query (normal) ou /query_stream (streaming)
┌─────────────────▼───────────────────────────────────────────┐
│                  BACKEND (FastAPI)                           │
│  - API REST com endpoints de status                          │
│  - Sistema de rastreamento de tarefas                        │
│  - Validação de contexto (rejeita perguntas off-topic)       │
│  - Múltiplas buscas automáticas se necessário                │
└─────────────────┬───────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┬──────────────┐
        │                   │              │
┌───────▼────────┐  ┌──────▼──────┐  ┌───▼──────────┐
│   ChromaDB     │  │   Ollama    │  │  PyTorch     │
│  (Vector DB)   │  │  (LLM Local)│  │  (Embeddings)│
│  - Embeddings  │  │  - Qwen2.5  │  │  - GPU/CPU   │
│  - Busca       │  │  - 7B params│  │  - CUDA/MPS  │
│    Semântica   │  │             │  │              │
└────────────────┘  └─────────────┘  └──────────────┘
```

### Fluxo de Processamento

1. **Usuário faz pergunta** → Frontend envia para `/query_stream`
2. **Backend analisa contexto** → Verifica se pergunta é relevante ao Espiritismo
3. **Busca semântica** → ChromaDB retorna top-K trechos mais relevantes
4. **Priorização** → Sistema reordena resultados por prioridade de fonte
5. **Geração com contexto** → LLM gera resposta baseada nos trechos + histórico
6. **Streaming** → Resposta enviada token por token para o frontend
7. **Exibição de fontes** → Usuário vê de quais livros vieram as informações

## 🛠️ Stack Tecnológico

### Backend
- **FastAPI** - Framework web assíncrono
- **Ollama** - Servidor LLM local (roda Qwen2.5:7b)
- **ChromaDB** - Banco de dados vetorial
- **LangChain** - Framework para RAG
- **Sentence Transformers** - Embeddings multilíngues (paraphrase-multilingual-mpnet-base-v2)
- **PyTorch** - Aceleração GPU (CUDA para NVIDIA, MPS para Apple Silicon)

### Frontend
- **Streamlit** - Interface web interativa
- **Requests** - Cliente HTTP para API

### Modelo LLM
- **Qwen2.5:7b** - Modelo otimizado para português (padrão)
- Suporta outros: llama3.2:3b, llama3.2:1b

## 📦 Instalação e Configuração

### Pré-requisitos

#### Para Windows (NVIDIA GPU)
- Python 3.11+
- NVIDIA GPU (RTX 3070 ou superior)
- NVIDIA CUDA Toolkit 11.8+
- Ollama for Windows

#### Para Mac (Apple Silicon)
- Python 3.11+
- Mac com chip M1/M2/M3/M4
- Ollama for macOS

### 1️⃣ Instalação do Ollama

#### Windows:
```bash
# Baixar de: https://ollama.com/download/windows
# Instalar e verificar
ollama --version

# Baixar modelo
ollama pull qwen2.5:7b
```

#### Mac:
```bash
# Baixar de: https://ollama.com/download/mac
# Ou via Homebrew:
brew install ollama

# Baixar modelo
ollama pull qwen2.5:7b
```

### 2️⃣ Setup do Backend

#### Windows (NVIDIA 3070):

```bash
cd backend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar PyTorch com CUDA (para GPU NVIDIA)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verificar CUDA
python -c "import torch; print(f'CUDA disponível: {torch.cuda.is_available()}')"
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

#### Mac (M4 Pro):

```bash
cd backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# PyTorch já vem com suporte MPS (Metal Performance Shaders)
# Verificar MPS
python -c "import torch; print(f'MPS disponível: {torch.backends.mps.is_available()}')"
```

### 3️⃣ Adicionar Livros

```bash
# Copiar PDFs dos livros espíritas para a pasta books/
# Estrutura esperada:
backend/books/
  ├── Livro-dos-Espiritos.pdf
  ├── O-evangelho-segundo-o-espiritismo.pdf
  ├── Livro-dos-Mediuns_Guillon.pdf
  ├── A-genese_Guillon.pdf
  ├── ceu-e-inferno-Manuel-Quintao.pdf
  └── ... (outros livros)
```

### 4️⃣ Processar Livros

```bash
# Windows
python process_books.py

# Mac
python3 process_books.py

# Este processo:
# - Carrega todos os PDFs da pasta books/
# - Divide em chunks de 1000 caracteres
# - Cria embeddings usando GPU/MPS
# - Salva no ChromaDB (pasta database/)
# Tempo estimado: 10-20 minutos
```

### 5️⃣ Setup do Frontend

#### Windows:
```bash
cd frontend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar API URL (para uso local)
mkdir .streamlit
echo API_URL = "http://localhost:8000" > .streamlit\secrets.toml
```

#### Mac:
```bash
cd frontend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar API URL (para uso local)
mkdir -p .streamlit
echo 'API_URL = "http://localhost:8000"' > .streamlit/secrets.toml
```

## 🚀 Scripts de Execução

### Windows (NVIDIA 3070)

#### Backend - `start_backend.bat`
```batch
@echo off
echo ========================================
echo   BACKEND - ASSISTENTE ESPIRITA
echo ========================================
echo.

cd /d %~dp0

echo [1/3] Ativando ambiente virtual...
call venv\Scripts\activate

echo [2/3] Verificando Ollama...
ollama list

echo [3/3] Iniciando API...
python api_server.py

pause
```

#### Frontend - `start_frontend.bat`
```batch
@echo off
echo ========================================
echo   FRONTEND - ASSISTENTE ESPIRITA
echo ========================================
echo.

cd /d %~dp0

echo [1/2] Ativando ambiente virtual...
call venv\Scripts\activate

echo [2/2] Iniciando Streamlit...
streamlit run app.py

pause
```

#### Completo - `start_all.bat`
```batch
@echo off
echo ========================================
echo   ASSISTENTE ESPIRITA - STARTUP COMPLETO
echo ========================================
echo.

echo Iniciando Backend...
start cmd /k "cd backend && call start_backend.bat"

timeout /t 5

echo Iniciando Frontend...
start cmd /k "cd frontend && call start_frontend.bat"

echo.
echo ========================================
echo   Sistema inicializado!
echo   Backend: http://localhost:8000
echo   Frontend: http://localhost:8501
echo ========================================
```

### Mac (M4 Pro)

#### Backend - `start_backend.sh`
```bash
#!/bin/bash

echo "========================================"
echo "  BACKEND - ASSISTENTE ESPIRITA"
echo "========================================"
echo ""

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[1/3] Ativando ambiente virtual..."
source venv/bin/activate

echo "[2/3] Verificando Ollama..."
ollama list

echo "[3/3] Iniciando API..."
python api_server.py
```

#### Frontend - `start_frontend.sh`
```bash
#!/bin/bash

echo "========================================"
echo "  FRONTEND - ASSISTENTE ESPIRITA"
echo "========================================"
echo ""

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "[1/2] Ativando ambiente virtual..."
source venv/bin/activate

echo "[2/2] Iniciando Streamlit..."
streamlit run app.py
```

#### Completo - `start_all.sh`
```bash
#!/bin/bash

echo "========================================"
echo "  ASSISTENTE ESPIRITA - STARTUP COMPLETO"
echo "========================================"
echo ""

# Start backend in new terminal
osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/backend\" && ./start_backend.sh"'

echo "Aguardando backend iniciar..."
sleep 5

# Start frontend in new terminal
osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/frontend\" && ./start_frontend.sh"'

echo ""
echo "========================================"
echo "  Sistema inicializado!"
echo "  Backend: http://localhost:8000"
echo "  Frontend: http://localhost:8501"
echo "========================================"
```

## 🎮 Como Usar

### 1. Iniciar o Sistema

**Windows:**
```bash
# Opção 1: Tudo de uma vez
start_all.bat

# Opção 2: Separado
cd backend
start_backend.bat
# Em outro terminal:
cd frontend
start_frontend.bat
```

**Mac:**
```bash
# Tornar scripts executáveis (primeira vez)
chmod +x start_all.sh backend/start_backend.sh frontend/start_frontend.sh

# Opção 1: Tudo de uma vez
./start_all.sh

# Opção 2: Separado
cd backend
./start_backend.sh
# Em outro terminal:
cd frontend
./start_frontend.sh
```

### 2. Acessar a Interface

Abrir navegador em: **http://localhost:8501**

### 3. Fazer Perguntas

**Exemplos de perguntas válidas (IN CONTEXT):**
- "O que é o perispírito?"
- "Explique sobre a reencarnação segundo o Espiritismo"
- "O que Allan Kardec diz sobre a mediunidade?"
- "Qual a diferença entre médium e sensitivo?"

**Exemplos de perguntas FORA DE CONTEXTO (serão recusadas):**
- "Qual é a previsão do tempo?"
- "Como fazer um bolo de chocolate?"
- "Quem ganhou a Copa do Mundo?"

### 4. Ver Progresso em Tempo Real

Durante o processamento, você verá:
```
🔍 Consultando os livros...
├─ [10%] Criando modelo LLM
├─ [30%] Buscando nos livros espíritas
├─ [50%] Construindo contexto
├─ [70%] Gerando resposta
└─ [90%] Formatando resposta
```

### 5. Analisar Fontes

Após cada resposta, expanda "📖 Fontes Consultadas" para ver:
- 🥇 **PRIORIDADE MÁXIMA** - O Livro dos Espíritos
- 🥈 **OBRA FUNDAMENTAL** - Evangelho, Médiuns, etc.
- 🥉 **COMPLEMENTAR** - Revista Espírita
- 📄 **OUTRAS OBRAS** - Demais livros

## 🔧 Configuração Avançada

### Ajustar Prioridades

Editar `backend/config.py`:

```python
BOOK_PRIORITIES = {
    "livro-dos-espiritos.pdf": 100,  # Peso máximo
    "evangelho": 70,                  # Fundamental
    "mediuns": 70,
    # Adicionar novas prioridades...
}
```

### Alterar Modelo LLM

```bash
# Baixar novo modelo
ollama pull llama3.2:3b

# Na interface Streamlit (sidebar):
# Selecionar modelo desejado no dropdown
```

### Ajustar Parâmetros de Busca

Na interface Streamlit:
- **Temperatura** (0.0 - 1.0): Controla criatividade
  - 0.1-0.3: Mais fiel aos textos (recomendado)
  - 0.7-1.0: Mais criativo
- **Nº de trechos** (1-10): Quantos trechos usar
  - 3-5: Padrão (recomendado)
  - 8-10: Mais contexto (mais lento)
- **Busca inicial** (fetch_k): Quantos trechos buscar antes de priorizar
  - 15: Padrão
  - 20-30: Busca mais ampla

### Modificar Chunk Size

Editar `backend/config.py`:

```python
CHUNK_SIZE = 1000      # Tamanho em caracteres
CHUNK_OVERLAP = 200    # Sobreposição
```

**Depois reprocessar:**
```bash
cd backend
python process_books.py
```

## 🧪 Testes

### Testar Backend

```bash
# Health check
curl http://localhost:8000/health

# Status detalhado
curl http://localhost:8000/status/detailed

# Fazer pergunta via API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "O que é o perispírito?",
    "model_name": "qwen2.5:7b",
    "temperature": 0.3,
    "top_k": 3,
    "fetch_k": 15
  }'
```

### Testar Frontend

1. Acessar http://localhost:8501
2. Verificar status do backend (sidebar)
3. Fazer pergunta de teste
4. Verificar fontes retornadas
5. Testar feedback (👍😐👎)

## 📊 Endpoints da API

### Status Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Health check rápido |
| `/health` | GET | Ultra-lightweight health check |
| `/status` | GET | Status quick (idêntico a `/`) |
| `/status/detailed` | GET | Status detalhado com tasks ativas |
| `/status/task/{task_id}` | GET | Status de uma task específica |
| `/status/history` | GET | Histórico de requests |

### Query Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/query` | POST | Processa pergunta (resposta completa) |
| `/query_stream` | POST | Processa com streaming (estilo Perplexity) |

## 🔍 Detecção de Contexto (Out-of-Context Detection)

O sistema identifica perguntas fora de contexto através de:

1. **Análise semântica**: Embeddings da pergunta comparados com corpus espírita
2. **Threshold de relevância**: Score mínimo de similaridade
3. **Validação de tópicos**: Keywords relacionadas ao Espiritismo
4. **Histórico de conversa**: Contexto acumulado das mensagens

**Comportamento:**
```python
# Pergunta IN CONTEXT
"O que é reencarnação?" → Processa normalmente

# Pergunta OUT OF CONTEXT
"Qual a receita de bolo?" → Responde:
"Desculpe, só posso responder perguntas sobre Espiritismo
e Doutrina Espírita. Por favor, faça uma pergunta relacionada
às obras de Allan Kardec."
```

## 🤝 Sistema de Feedback

Cada resposta pode ser avaliada:
- 👍 **Boa**: Resposta útil e precisa
- 😐 **Regular**: Resposta ok mas pode melhorar
- 👎 **Ruim**: Resposta inadequada

Feedback é salvo em `frontend/feedback.jsonl` para análise.

## 📁 Estrutura de Arquivos

```
chatbot-comeerj/
├── CLAUDE.md                    # Este arquivo
├── README.md                    # Documentação geral
├── FEEDBACK_GUIDE.md           # Guia de feedback
├── LICENSE
├── start_all.bat               # Windows: Inicia tudo
├── start_all.sh                # Mac: Inicia tudo
│
├── backend/
│   ├── api_server.py           # API FastAPI
│   ├── config.py               # Configurações e prioridades
│   ├── priority_retriever.py  # Sistema de priorização
│   ├── process_books.py        # Processa PDFs
│   ├── feedback_system.py     # Sistema de feedback
│   ├── requirements.txt
│   ├── start_backend.bat       # Windows
│   ├── start_backend.sh        # Mac
│   ├── books/                  # PDFs (não versionado)
│   ├── database/               # ChromaDB (não versionado)
│   └── venv/                   # Python venv
│
└── frontend/
    ├── app.py                  # Interface Streamlit
    ├── chat_history.py         # Gerenciamento de conversas
    ├── feedback_system.py     # Sistema de feedback
    ├── requirements.txt
    ├── start_frontend.bat      # Windows
    ├── start_frontend.sh       # Mac
    ├── .streamlit/
    │   └── secrets.toml        # Config API URL (não versionado)
    └── venv/                   # Python venv
```

## 🐛 Troubleshooting

### Backend não inicia

**Windows:**
```bash
# Verificar Ollama
ollama list

# Se não funcionar, iniciar Ollama
# Procurar "Ollama" no menu iniciar e executar

# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Se False, reinstalar PyTorch com CUDA
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

**Mac:**
```bash
# Verificar Ollama
ollama list

# Se não funcionar, iniciar Ollama
ollama serve &

# Verificar MPS
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Frontend não conecta

```bash
# Verificar se backend está rodando
curl http://localhost:8000/health

# Verificar secrets.toml
cat frontend/.streamlit/secrets.toml

# Deve conter:
# API_URL = "http://localhost:8000"
```

### Respostas ruins

1. **Reduzir temperatura** para 0.1-0.2
2. **Aumentar top_k** para 5-8 trechos
3. **Aumentar fetch_k** para 20-30
4. **Testar outro modelo**: llama3.2:3b

### Banco corrompido

```bash
cd backend

# Windows
rmdir /s database
python process_books.py

# Mac
rm -rf database
python process_books.py
```

## ⚡ Performance

### Benchmarks

**Windows (NVIDIA RTX 3070):**
- Processamento inicial: ~15min para 23k chunks
- Busca vetorial: ~200ms
- Geração de resposta: 2-5s
- Throughput: 10-15 perguntas/min

**Mac (M4 Pro):**
- Processamento inicial: ~20min para 23k chunks
- Busca vetorial: ~300ms
- Geração de resposta: 3-6s
- Throughput: 8-12 perguntas/min

## 📝 Desenvolvimento

### Adicionar Nova Funcionalidade

1. **Backend**: Editar `backend/api_server.py`
2. **Frontend**: Editar `frontend/app.py`
3. **Configuração**: Editar `backend/config.py`
4. **Testes**: Testar via curl e interface

### Debugging

**Backend:**
```python
# Adicionar logs em api_server.py
print(f"DEBUG: {variavel}")

# Acessar logs
# Windows: Ver console do backend
# Mac: Ver terminal do backend
```

**Frontend:**
```python
# Adicionar em app.py
st.write(f"DEBUG: {variavel}")

# Aparece na interface
```

### Adicionar Novo Modelo

```bash
# Baixar modelo
ollama pull nome-do-modelo

# Editar frontend/app.py
model_name = st.selectbox(
    "Modelo:",
    ["qwen2.5:7b", "llama3.2:3b", "nome-do-modelo"]
)
```

## 🔐 Segurança e Privacidade

- ✅ **100% Local**: Nenhum dado enviado para servidores externos
- ✅ **GPU/CPU Local**: Processamento totalmente on-premise
- ✅ **Sem internet necessária** (após setup inicial)
- ✅ **Dados privados**: Conversas salvas localmente

## 📚 Documentação Adicional

- [FastAPI](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://docs.trychroma.com/)
- [LangChain](https://python.langchain.com/)
- [Streamlit](https://docs.streamlit.io/)
- [PyTorch](https://pytorch.org/)

## 🤝 Contribuindo

Para contribuir:
1. Use o sistema normalmente
2. Avalie respostas (👍😐👎)
3. Deixe comentários detalhados
4. Reporte bugs via issues

## 📄 Licença

MIT License - Uso educacional e religioso.

Obras espíritas utilizadas são de domínio público (Allan Kardec).

## ✨ Créditos

- Allan Kardec - Codificação Espírita
- FEB - Federação Espírita Brasileira
- Comunidade Open Source

---

## 📊 Status de Implementação das Funcionalidades

| Funcionalidade | Status | Detalhes |
|---------------|--------|----------|
| Out-of-Context Detection | ✅ **IMPLEMENTADO** | Sistema de 3 camadas validando perguntas (2025-02-01) |
| Context Correlation | ✅ **IMPLEMENTADO** | Histórico de conversa funcional |
| Multiple Search | 🔴 **PENDENTE** | Ver [proposta 002](docs/proposed/002-multiple-search-capability.md) |
| Real-Time Progress | 🟡 **50% PRONTO** | Backend completo, frontend pendente ([proposta 003](docs/proposed/003-real-time-progress-indicators.md)) |
| Source Prioritization | ✅ **IMPLEMENTADO** | Sistema de prioridades funcionando |
| Streaming Responses | ✅ **IMPLEMENTADO** | Streaming via SSE funcionando |
| Portuguese UI/AI | ✅ **IMPLEMENTADO** | 100% em português brasileiro |
| Feedback System | ✅ **IMPLEMENTADO** | Sistema de feedback funcionando |

### Arquivos de Implementação - Out-of-Context Detection

- `backend/context_validator.py` - Validador de contexto
- `backend/config.py` - Configurações (threshold: 0.35)
- `backend/api_server.py` - Integração nos endpoints
- `backend/test_context_validation.py` - Testes
- `backend/README_TESTING.md` - Documentação de testes
- `docs/completed/001-out-of-context-detection.md` - Proposta completa

### Como Testar Out-of-Context Detection

```bash
cd backend
source venv/bin/activate
python test_context_validation.py
```

Ou via API:
```bash
# Pergunta válida
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "O que é reencarnação?", "model_name": "qwen2.5:7b"}'

# Pergunta inválida (será rejeitada)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Qual a receita de bolo?", "model_name": "qwen2.5:7b"}'
```

---

**Versão**: 1.2.2
**Última atualização**: Fevereiro 2025
**Desenvolvido com**: Claude Sonnet 4.5
