# 📚 Assistente Espírita - Sistema RAG com Priorização de Fontes

Sistema de assistente conversacional especializado em Doutrina Espírita, utilizando RAG (Retrieval-Augmented Generation) com priorização inteligente das obras da Codificação.

## 🎯 Características Principais

- **Priorização de Fontes**: Sistema que prioriza O Livro dos Espíritos sobre demais obras
- **Busca Semântica**: ChromaDB com embeddings multilíngues otimizados para português
- **LLM Local**: Ollama com modelo Llama 3.2:3b rodando localmente
- **Interface Web**: Streamlit com feedback colaborativo
- **Arquitetura Cliente-Servidor**: Backend local (GPU) + Frontend na nuvem

## 📋 Hierarquia de Fontes

1. 🥇 **Prioridade Máxima** (peso 100): O Livro dos Espíritos
2. 🥈 **Obras Fundamentais** (peso 70): Evangelho, Médiuns, Gênese, Céu e Inferno, O que é o Espiritismo
3. 🥉 **Complementar** (peso 40): Revista Espírita (1858-1869)
4. 📄 **Outras Obras** (peso 10): Demais livros

## 🏗️ Arquitetura
```
    ┌─────────────────┐
    │   Usuários      │
    │   (Internet)    │
    └────────┬────────┘
             │
    ┌────────▼───────────────┐
    │  Frontend (Cloud)      │
    │  Streamlit Cloud       │
    └────────┬───────────────┘
             │ HTTPS/API
    ┌────────▼───────────────┐
    │  ngrok Tunnel          │
    └────────┬───────────────┘
             │
    ┌────────▼───────────────┐
    │  Backend (Local PC)    │
    │  • FastAPI             │
    │  • ChromaDB            │
    │  • Ollama (GPU)        │
    └────────────────────────┘
```

## 🖥️ Stack Tecnológico

### Backend
- **FastAPI**: API REST
- **Ollama**: Servidor LLM local
- **Llama 3.2:3b**: Modelo de linguagem otimizado para português
- **ChromaDB**: Banco de dados vetorial
- **LangChain**: Framework RAG
- **Sentence Transformers**: Embeddings multilíngues
- **PyTorch**: GPU acceleration (CUDA)

### Frontend
- **Streamlit**: Interface web
- **Requests**: Cliente HTTP para API

### Infraestrutura
- **ngrok**: Túnel seguro para expor backend
- **Streamlit Cloud**: Hospedagem do frontend
- **GitHub**: Versionamento

## 📦 Instalação

### Pré-requisitos

- Python 3.11
- NVIDIA GPU com CUDA (recomendado)
- Ollama instalado
- ngrok account (para deploy)

### Backend Setup
```bash
cd backend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar PyTorch com CUDA (para GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Instalar Ollama
# Baixar de: https://ollama.com/download

# Baixar modelo
ollama pull llama3.2:3b

# Adicionar livros espíritas em PDF na pasta books/

# Processar livros (criar banco vetorial)
python process_books.py

# Iniciar API
python api_server.py
```

API estará disponível em: `http://localhost:8000`

### Frontend Setup (Local)
```bash
cd frontend

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Configurar API URL
# Criar .streamlit/secrets.toml:
mkdir .streamlit
echo API_URL = "http://localhost:8000" > .streamlit\secrets.toml

# Rodar frontend
streamlit run app.py
```

Frontend estará disponível em: `http://localhost:8501`

## 🚀 Deploy

### 1. Backend (ngrok)
```bash
cd backend

# Terminal 1: Rodar backend
python api_server.py

# Terminal 2: Expor via ngrok
ngrok http 8000

# Copiar URL gerada (ex: https://abc-123.ngrok-free.app)
```

### 2. Frontend (Streamlit Cloud)
```bash
cd frontend

# Inicializar Git
git init
git add .
git commit -m "Initial commit"

# Criar repositório no GitHub
# Depois fazer push

# Deploy no Streamlit Cloud:
# 1. Acesse https://share.streamlit.io
# 2. New app
# 3. Conecte seu repositório GitHub
# 4. Configure secrets:
#    API_URL = "https://sua-url-ngrok.ngrok-free.app"
# 5. Deploy!
```

## 📊 Sistema de Feedback

O sistema coleta feedback colaborativo de usuários para melhorar continuamente:

- **Avaliações**: Boa (👍), Regular (😐), Ruim (👎)
- **Comentários**: Feedback textual detalhado
- **Armazenamento**: JSONL local para análise
- **Análise**: Script `view_feedback.py` para visualizar estatísticas

### Visualizar Feedback
```bash
cd frontend
streamlit run view_feedback.py
```

## 🧪 Testes Locais

### Testar Backend
```bash
# Verificar status
curl http://localhost:8000/

# Testar query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "O que é o perispírito?",
    "model_name": "llama3.2:3b",
    "temperature": 0.3,
    "top_k": 8,
    "fetch_k": 20
  }'

# Ver documentação interativa
# Abrir no navegador: http://localhost:8000/docs
```

### Testar Frontend

1. Certifique-se que o backend está rodando
2. Execute `streamlit run app.py`
3. Faça perguntas de teste
4. Verifique as fontes retornadas
5. Teste o sistema de feedback

## 📈 Performance

### Benchmarks (RTX 3070 + Ryzen 7 5700x)

- **Processamento de livros**: ~15min para 22.868 chunks
- **Busca vetorial**: ~200ms para top 20 resultados
- **Geração de resposta**: 2-5s (dependendo do tamanho)
- **Throughput**: ~10-15 perguntas/minuto

### Otimizações Implementadas

- ✅ Processamento em batch (5000 chunks/vez)
- ✅ Deduplicação de chunks similares
- ✅ Cache de embeddings (GPU)
- ✅ Priorização antes da inferência
- ✅ Reranking baseado em relevância + prioridade

## 🔧 Configuração Avançada

### Ajustar Prioridades

Edite `backend/config.py`:
```python
BOOK_PRIORITIES = {
    "livro-dos-espiritos.pdf": 100,  # Alterar peso aqui
    "evangelho": 70,
    # ...
}
```

### Trocar Modelo LLM
```bash
# Listar modelos disponíveis
ollama list

# Baixar novo modelo
ollama pull llama3.2:1b

# Atualizar no frontend (sidebar)
model_name = st.selectbox(
    "Modelo:",
    ["llama3.2:3b", "llama3.2:1b", "llama3.2:1b"],  # Adicionar aqui
)
```

### Ajustar Chunk Size

Edite `backend/config.py`:
```python
CHUNK_SIZE = 1000      # Tamanho do chunk (caracteres)
CHUNK_OVERLAP = 200    # Sobreposição entre chunks
```

Depois reprocessar:
```bash
python process_books.py
```

## 📝 Estrutura de Arquivos
```
chatbot-comeerj/
├── README.md                    # Este arquivo
├── GUIA_TESTADORES.md          # Guia para testadores
│
├── backend/
│   ├── .gitignore
│   ├── api_server.py           # API FastAPI
│   ├── config.py               # Configurações
│   ├── priority_retriever.py  # Sistema de priorização
│   ├── feedback_system.py     # Sistema de feedback
│   ├── process_books.py       # Indexação de livros
│   ├── requirements.txt
│   ├── start_backend.bat       # Script Windows para iniciar
│   ├── start_with_ngrok.bat    # Script com ngrok
│   ├── books/                  # PDFs (não versionado)
│   ├── database/               # ChromaDB (não versionado)
│   └── feedback/               # Dados de feedback
│
└── frontend/
    ├── .gitignore
    ├── app.py                  # Interface Streamlit
    ├── feedback_system.py     # Sistema de feedback
    ├── view_feedback.py       # Análise de feedback
    ├── requirements.txt
    └── .streamlit/
        └── secrets.toml        # Config API URL (não versionado)
```

## 🐛 Troubleshooting

### Backend não inicia
```bash
# Verificar se Ollama está rodando
ollama list

# Se não, iniciar Ollama
ollama serve

# Verificar CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Reinstalar PyTorch com CUDA se necessário
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### Frontend não conecta
```bash
# Verificar se backend está rodando
curl http://localhost:8000/

# Verificar secrets.toml
cat frontend/.streamlit/secrets.toml

# Verificar ngrok (se usando)
# Acessar http://localhost:4040 para ver status do túnel
```

### Banco vetorial corrompido
```bash
cd backend

# Deletar banco
rm -rf database/

# Reprocessar livros
python process_books.py
```

### Respostas de baixa qualidade

1. **Temperatura muito alta**: Reduzir para 0.1-0.3
2. **Poucos trechos**: Aumentar `top_k` para 10-12
3. **Busca limitada**: Aumentar `fetch_k` para 30-40
4. **Modelo inadequado**: Testar outros modelos (llama3.2:1b)

## 📚 Documentação Adicional

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.com/)
- [ChromaDB](https://docs.trychroma.com/)
- [LangChain](https://python.langchain.com/)
- [Streamlit](https://docs.streamlit.io/)

## 🤝 Contribuindo

Este é um projeto colaborativo com sistema de feedback integrado. Para contribuir:

1. Use o sistema normalmente
2. Avalie cada resposta (👍😐👎)
3. Deixe comentários detalhados
4. Reporte bugs via issues

## 📄 Licença

Este projeto é para uso educacional e religioso. Os livros espíritas utilizados são de domínio público (obras de Allan Kardec).

## ✨ Agradecimentos

- Allan Kardec pela Codificação Espírita
- FEB (Federação Espírita Brasileira) pelas traduções
- Comunidade open-source pelos frameworks utilizados
- Testadores colaborativos pelo feedback

## 📧 Contato

Para dúvidas ou sugestões sobre o projeto, entre em contato através dos issues do GitHub.

---

**Versão**: 1.0.0  
**Última atualização**: Janeiro 2025
