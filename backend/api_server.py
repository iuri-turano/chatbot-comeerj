from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
import json
from typing import List, Optional

app = FastAPI(
    title="Assistente Espírita API",
    description="Backend API para o Assistente Espírita com Ollama",
    version="2.0.0"
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

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    model_name: str = "qwen2.5:7b"
    temperature: float = 0.3
    top_k: int = 3
    fetch_k: int = 15
    conversation_history: Optional[List[Message]] = None

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

class StreamChunk(BaseModel):
    type: str  # "token" or "sources" or "done"
    content: Optional[str] = None
    sources: Optional[list[Source]] = None

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
    print("🚀 Iniciando Assistente Espírita API v2.0")
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

def build_context_with_history(conversation_history: List[Message], max_history: int = 5) -> str:
    """Build conversation context from history"""
    if not conversation_history or len(conversation_history) == 0:
        return ""
    
    # Take last N messages (excluding current question)
    recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history
    
    context_parts = []
    for msg in recent_history:
        if msg.role == "user":
            context_parts.append(f"Consulente: {msg.content}")
        elif msg.role == "assistant":
            context_parts.append(f"Assistente: {msg.content}")
    
    return "\n".join(context_parts)

def create_llm_and_prompt(model_name: str, temperature: float):
    """Create LLM and prompt template with conversation context support"""
    
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
9. Mantenha coerência com o contexto da conversa anterior
10. Se a pergunta se referir a algo mencionado anteriormente, use esse contexto
11. Apenas se não encontrar a resposta no contexto, diga claramente: "Não encontrei essa informação específica nos livros fornecidos"

HIERARQUIA DE FONTES (use nesta ordem de importância):
1️⃣ O Livro dos Espíritos
2️⃣ Obras complementares (Evangelho, Médiuns, Gênese, Céu e Inferno, O que é o Espiritismo)
3️⃣ Revista Espírita

{conversation_context}

CONTEXTO DOS LIVROS ESPÍRITAS (já ordenado por prioridade):
{context}

PERGUNTA DO CONSULENTE: {question}

RESPOSTA (em português correto, reflexiva, priorizando O Livro dos Espíritos e citando todas as fontes):"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["conversation_context", "context", "question"]
    )
    
    llm = Ollama(
        model=model_name,
        temperature=temperature,
        num_ctx=CONTEXT_WINDOW,
        system="Você é um especialista em Doutrina Espírita codificada por Allan Kardec. PRIORIZE sempre O Livro dos Espíritos como fonte principal. Responda em português brasileiro fluente e correto. Seja reflexivo, faça conexões entre os conceitos espíritas e sempre cite as fontes com precisão, dando destaque às obras fundamentais. Mantenha coerência com o histórico da conversa.",
    )
    
    return llm, prompt

@app.get("/", response_model=StatusResponse)
async def root():
    """Health check and status endpoint"""
    return StatusResponse(
        status="online",
        message="Assistente Espírita API v2.0 - Backend rodando",
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
        print(f"🔍 Nova pergunta: {request.question[:100]}...")
        print(f"⚙️  Modelo: {request.model_name} | Temp: {request.temperature}")
        
        # Create LLM for this request
        llm, prompt_template = create_llm_and_prompt(
            request.model_name, 
            request.temperature
        )
        
        print(f"📖 Buscando nos livros espíritas...")
        
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
        
        # Build context from books
        context = "\n\n---\n\n".join([
            f"[Trecho {i+1} - {get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
            for i, doc in enumerate(sources)
        ])
        
        # Build conversation context
        conversation_context = ""
        if request.conversation_history and len(request.conversation_history) > 0:
            history_text = build_context_with_history(request.conversation_history)
            if history_text:
                conversation_context = f"\nHISTÓRICO DA CONVERSA (para contexto):\n{history_text}\n"
        
        # Format prompt
        formatted_prompt = prompt_template.format(
            conversation_context=conversation_context,
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

@app.post("/query_stream")
async def query_stream(request: QueryRequest):
    """Process a question and stream the response"""
    
    if vectorstore is None:
        raise HTTPException(
            status_code=503, 
            detail="Banco de dados não carregado. Verifique os logs do servidor."
        )
    
    async def generate():
        try:
            print(f"\n{'='*60}")
            print(f"🔍 Nova pergunta (streaming): {request.question[:100]}...")
            
            # Create LLM for this request
            llm, prompt_template = create_llm_and_prompt(
                request.model_name, 
                request.temperature
            )
            
            # Search with priority
            sources = prioritized_search(
                vectorstore, 
                request.question, 
                k=request.top_k, 
                fetch_k=request.fetch_k
            )
            
            # Add priority metadata
            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)
            
            # Build context
            context = "\n\n---\n\n".join([
                f"[Trecho {i+1} - {get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                for i, doc in enumerate(sources)
            ])
            
            # Build conversation context
            conversation_context = ""
            if request.conversation_history and len(request.conversation_history) > 0:
                history_text = build_context_with_history(request.conversation_history)
                if history_text:
                    conversation_context = f"\nHISTÓRICO DA CONVERSA (para contexto):\n{history_text}\n"
            
            # Format prompt
            formatted_prompt = prompt_template.format(
                conversation_context=conversation_context,
                context=context,
                question=request.question
            )
            
            # Stream tokens
            for chunk in llm.stream(formatted_prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
            
            # Send sources at the end
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
                
                formatted_sources.append({
                    "content": source.page_content[:500],
                    "source": os.path.basename(source_path),
                    "page": source.metadata.get('page', 0),
                    "priority": priority,
                    "priority_label": priority_label,
                    "display_name": get_book_display_name(source_path)
                })
            
            yield f"data: {json.dumps({'type': 'sources', 'sources': formatted_sources})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            print(f"❌ Erro no streaming: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

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
    print("\n🚀 Iniciando servidor API v2.0...")
    print("📍 Rodando em: http://localhost:8000")
    print("📖 Documentação: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")