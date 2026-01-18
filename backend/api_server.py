from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from config import (
    DB_DIR, 
    EMBEDDING_MODEL, 
    CONTEXT_WINDOW,
    get_book_priority,
    get_book_display_name
)
from priority_retriever import prioritized_search
import torch
import os

app = FastAPI(
    title="Assistente Espírita API",
    description="Backend API para o Assistente Espírita com Ollama",
    version="1.0.0"
)

# Enable CORS for Streamlit Cloud
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
vectorstore = None

class QueryRequest(BaseModel):
    question: str
    model_name: str = "qwen2.5:7b"
    temperature: float = 0.3
    top_k: int = 8
    fetch_k: int = 20

class Source(BaseModel):
    content: str
    source: str
    page: int
    priority: int
    priority_label: str
    display_name: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]

class StatusResponse(BaseModel):
    status: str
    message: str
    cuda_available: bool
    gpu: str
    vectorstore_loaded: bool

@app.on_event("startup")
async def startup_event():
    """Load vectorstore on startup"""
    global vectorstore
    
    print("=" * 60)
    print("🚀 Iniciando Assistente Espírita API")
    print("=" * 60)
    
    # Check if database exists
    if not os.path.exists(DB_DIR):
        print(f"❌ Banco de dados não encontrado em: {DB_DIR}")
        print(f"⚠️  Execute: python process_books.py")
        return
    
    print(f"📚 Carregando banco de dados vetorial de: {DB_DIR}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"📊 Dispositivo: {device}")
    
    if torch.cuda.is_available():
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device}
    )
    
    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )
    
    print("✅ Banco de dados carregado com sucesso!")
    print("=" * 60)
    print("🌐 API pronta em: http://localhost:8000")
    print("📖 Documentação em: http://localhost:8000/docs")
    print("=" * 60)

def create_llm_and_prompt(model_name: str, temperature: float):
    """Create LLM and prompt template"""
    
    template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

INSTRUÇÕES IMPORTANTES:
1. Responda SEMPRE em português brasileiro correto e fluente
2. DÊ PRIORIDADE às informações de "O Livro dos Espíritos" quando disponível
3. Depois, priorize as outras obras fundamentais: O Evangelho Segundo o Espiritismo, O Livro dos Médiuns, A Gênese, O Céu e o Inferno, O que é o Espiritismo
4. Use as Revistas Espíritas como complemento
5. SEMPRE cite os livros de onde extraiu as informações (ex: "Segundo O Livro dos Espíritos, questão 150..." ou "Conforme O Evangelho Segundo o Espiritismo, capítulo 5...")
6. Quando houver informações de múltiplas obras, CITE TODAS mas destaque O Livro dos Espíritos
7. Faça correlações entre diferentes trechos quando relevante
8. Reflita sobre as implicações dos ensinamentos apresentados
9. Apenas se não encontrar a resposta no contexto, diga claramente: "Não encontrei essa informação específica nos livros fornecidos"

HIERARQUIA DE FONTES (use nesta ordem de importância):
1️⃣ O Livro dos Espíritos
2️⃣ Obras complementares (Evangelho, Médiuns, Gênese, Céu e Inferno, O que é o Espiritismo)
3️⃣ Revista Espírita

CONTEXTO DOS LIVROS ESPÍRITAS (já ordenado por prioridade):
{context}

PERGUNTA DO CONSULENTE: {question}

RESPOSTA (em português correto, reflexiva, priorizando O Livro dos Espíritos e citando todas as fontes):"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["context", "question"]
    )
    
    llm = Ollama(
        model=model_name,
        temperature=temperature,
        num_ctx=CONTEXT_WINDOW,
        system="Você é um especialista em Doutrina Espírita codificada por Allan Kardec. PRIORIZE sempre O Livro dos Espíritos como fonte principal. Responda em português brasileiro fluente e correto. Seja reflexivo, faça conexões entre os conceitos espíritas e sempre cite as fontes com precisão, dando destaque às obras fundamentais.",
    )
    
    return llm, prompt

@app.get("/", response_model=StatusResponse)
async def root():
    """Health check and status endpoint"""
    return StatusResponse(
        status="online",
        message="Assistente Espírita API - Backend rodando",
        cuda_available=torch.cuda.is_available(),
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        vectorstore_loaded=vectorstore is not None
    )

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a question and return answer with sources"""
    
    if vectorstore is None:
        raise HTTPException(
            status_code=503, 
            detail="Banco de dados não carregado. Verifique os logs do servidor."
        )
    
    try:
        print(f"\n{'='*60}")
        print(f"📝 Nova pergunta: {request.question[:100]}...")
        print(f"⚙️  Modelo: {request.model_name} | Temp: {request.temperature}")
        
        # Create LLM for this request
        llm, prompt_template = create_llm_and_prompt(
            request.model_name, 
            request.temperature
        )
        
        print(f"🔍 Buscando nos livros espíritas...")
        
        # Search with priority and deduplication
        sources = prioritized_search(
            vectorstore, 
            request.question, 
            k=request.top_k, 
            fetch_k=request.fetch_k
        )
        
        print(f"✅ Encontradas {len(sources)} fontes relevantes")
        
        # Add priority metadata
        for source in sources:
            source_path = source.metadata.get('source', '')
            source.metadata['priority'] = get_book_priority(source_path)
        
        # Build context
        context = "\n\n---\n\n".join([
            f"[Trecho {i+1} - {get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
            for i, doc in enumerate(sources)
        ])
        
        # Format prompt
        formatted_prompt = prompt_template.format(
            context=context,
            question=request.question
        )
        
        print(f"🤖 Gerando resposta com {request.model_name}...")
        
        # Get answer from LLM
        answer = llm.invoke(formatted_prompt)
        
        print(f"✅ Resposta gerada com sucesso!")
        print(f"{'='*60}\n")
        
        # Format sources for response
        formatted_sources = []
        for source in sources:
            source_path = source.metadata.get('source', 'Desconhecido')
            priority = source.metadata.get('priority', 10)
            
            if priority >= 100:
                priority_label = "PRIORIDADE MÁXIMA"
            elif priority >= 70:
                priority_label = "OBRA FUNDAMENTAL"
            elif priority >= 40:
                priority_label = "COMPLEMENTAR"
            else:
                priority_label = "OUTRAS OBRAS"
            
            formatted_sources.append(Source(
                content=source.page_content[:500],
                source=os.path.basename(source_path),
                page=source.metadata.get('page', 0),
                priority=priority,
                priority_label=priority_label,
                display_name=get_book_display_name(source_path)
            ))
        
        return QueryResponse(
            answer=answer,
            sources=formatted_sources
        )
        
    except Exception as e:
        print(f"❌ Erro ao processar pergunta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

@app.get("/models")
async def list_models():
    """List available Ollama models"""
    import subprocess
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        return {"status": "success", "models": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor API...")
    print("📍 Rodando em: http://localhost:8000")
    print("📖 Documentação: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")