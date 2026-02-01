from fastapi import FastAPI, HTTPException, BackgroundTasks
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
    get_book_display_name,
    CONTEXT_VALIDATION_THRESHOLD,
    REJECTION_MESSAGE
)
from priority_retriever import prioritized_search
from context_validator import ContextValidator
import torch
import os
import json
import asyncio
import time
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import deque
import threading

app = FastAPI(
    title="Assistente Espírita API",
    description="Backend API com Sistema de Status Dedicado",
    version="1.2.1"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SISTEMA DE MONITORAMENTO GLOBAL
# ============================================================================

class ServerStatus:
    """Thread-safe status monitoring system"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._active_requests = 0
        self._total_requests = 0
        self._last_request_time = None
        self._request_history = deque(maxlen=100)  # Last 100 requests
        self._current_tasks = {}  # task_id -> task_info
        self._task_counter = 0
        
    def start_request(self, question: str, mode: str = "normal") -> str:
        """Register new request and return task_id"""
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}"
            
            self._active_requests += 1
            self._total_requests += 1
            self._last_request_time = datetime.now()
            
            task_info = {
                "task_id": task_id,
                "question": question[:100],  # Truncate
                "mode": mode,
                "status": "processing",
                "started_at": datetime.now().isoformat(),
                "stage": "initialized",
                "progress": 0
            }
            
            self._current_tasks[task_id] = task_info
            
            return task_id
    
    def update_task(self, task_id: str, stage: str, progress: int):
        """Update task progress"""
        with self._lock:
            if task_id in self._current_tasks:
                self._current_tasks[task_id]["stage"] = stage
                self._current_tasks[task_id]["progress"] = progress
    
    def complete_request(self, task_id: str, success: bool = True, error: str = None):
        """Mark request as complete"""
        with self._lock:
            if task_id in self._current_tasks:
                task = self._current_tasks[task_id]
                task["status"] = "completed" if success else "failed"
                task["completed_at"] = datetime.now().isoformat()
                task["progress"] = 100 if success else task.get("progress", 0)
                
                if error:
                    task["error"] = error
                
                # Move to history
                self._request_history.append(task)
                del self._current_tasks[task_id]
            
            self._active_requests = max(0, self._active_requests - 1)
    
    def get_status(self) -> Dict:
        """Get current server status (thread-safe, non-blocking)"""
        with self._lock:
            return {
                "status": "busy" if self._active_requests > 0 else "idle",
                "active_requests": self._active_requests,
                "total_requests": self._total_requests,
                "last_request": self._last_request_time.isoformat() if self._last_request_time else None,
                "current_tasks": list(self._current_tasks.values()),
                "uptime_seconds": time.time() - startup_time if 'startup_time' in globals() else 0
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get status of specific task"""
        with self._lock:
            # Check active tasks
            if task_id in self._current_tasks:
                return self._current_tasks[task_id]
            
            # Check history
            for task in self._request_history:
                if task["task_id"] == task_id:
                    return task
            
            return None
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent request history"""
        with self._lock:
            return list(self._request_history)[-limit:]

# Global status tracker
status_tracker = ServerStatus()
startup_time = time.time()

# Global variables
vectorstore = None
context_validator = None
executor = ThreadPoolExecutor(max_workers=3)

# ============================================================================
# MODELS
# ============================================================================

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
    task_id: str
    answer: str
    sources: list[Source]
    processing_time: float

class ServerStatusResponse(BaseModel):
    """Lightweight status response - ALWAYS returns quickly"""
    online: bool
    status: str  # "idle", "busy", "error"
    active_requests: int
    cuda_available: bool
    gpu: str
    vectorstore_loaded: bool
    uptime_seconds: float
    timestamp: str

class DetailedStatusResponse(BaseModel):
    """Detailed status with current tasks"""
    online: bool
    status: str
    active_requests: int
    total_requests: int
    last_request: Optional[str]
    current_tasks: List[Dict]
    cuda_available: bool
    gpu: str
    vectorstore_loaded: bool
    uptime_seconds: float
    timestamp: str

class TaskStatusResponse(BaseModel):
    """Status of specific task"""
    found: bool
    task_info: Optional[Dict]

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Load vectorstore on startup"""
    global vectorstore, context_validator, startup_time
    
    startup_time = time.time()
    
    print("=" * 60)
    print("🚀 Iniciando Assistente Espírita API v1.2.1")
    print("   (Sistema de Status Dedicado)")
    print("=" * 60)
    
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

    # Initialize context validator
    print("🔍 Inicializando validador de contexto...")
    context_validator = ContextValidator(embeddings)
    print("✅ Validador de contexto pronto!")
    print("=" * 60)
    print("🌐 API pronta em: http://localhost:8000")
    print("📖 Documentação em: http://localhost:8000/docs")
    print("🔍 Status: http://localhost:8000/status")
    print("📊 Status detalhado: http://localhost:8000/status/detailed")
    print("=" * 60)

# ============================================================================
# STATUS ENDPOINTS (NON-BLOCKING)
# ============================================================================

@app.get("/", response_model=ServerStatusResponse)
async def root():
    """
    LIGHTWEIGHT health check - ALWAYS returns quickly
    Use this for checking if backend is online
    """
    current_status = status_tracker.get_status()
    
    return ServerStatusResponse(
        online=True,
        status=current_status["status"],
        active_requests=current_status["active_requests"],
        cuda_available=torch.cuda.is_available(),
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        vectorstore_loaded=vectorstore is not None,
        uptime_seconds=current_status["uptime_seconds"],
        timestamp=datetime.now().isoformat()
    )

@app.get("/status", response_model=ServerStatusResponse)
async def quick_status():
    """
    Quick status check - identical to /
    Dedicated endpoint for status monitoring
    """
    return await root()

@app.get("/status/detailed", response_model=DetailedStatusResponse)
async def detailed_status():
    """
    Detailed status including current tasks
    Still non-blocking and fast
    """
    current_status = status_tracker.get_status()
    
    return DetailedStatusResponse(
        online=True,
        status=current_status["status"],
        active_requests=current_status["active_requests"],
        total_requests=current_status["total_requests"],
        last_request=current_status["last_request"],
        current_tasks=current_status["current_tasks"],
        cuda_available=torch.cuda.is_available(),
        gpu=torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
        vectorstore_loaded=vectorstore is not None,
        uptime_seconds=current_status["uptime_seconds"],
        timestamp=datetime.now().isoformat()
    )

@app.get("/status/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get status of specific task
    Useful for tracking long-running queries
    """
    task_info = status_tracker.get_task_status(task_id)
    
    return TaskStatusResponse(
        found=task_info is not None,
        task_info=task_info
    )

@app.get("/status/history")
async def get_request_history(limit: int = 10):
    """
    Get recent request history
    """
    history = status_tracker.get_history(limit)
    
    return {
        "history": history,
        "count": len(history)
    }

@app.get("/health")
async def health_check():
    """
    Ultra-lightweight health check
    Returns immediately with minimal processing
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def build_context_with_history(conversation_history: List[Message], max_history: int = 5) -> str:
    """Build conversation context from history"""
    if not conversation_history or len(conversation_history) == 0:
        return ""
    
    recent_history = conversation_history[-max_history:] if len(conversation_history) > max_history else conversation_history
    
    context_parts = []
    for msg in recent_history:
        if msg.role == "user":
            context_parts.append(f"Consulente: {msg.content}")
        elif msg.role == "assistant":
            context_parts.append(f"Assistente: {msg.content}")
    
    return "\n".join(context_parts)

def create_llm_and_prompt(model_name: str, temperature: float):
    """Create LLM and prompt template"""
    
    template = """Você é um assistante especializado em Espiritismo e Doutrina Espírita.

REGRA FUNDAMENTAL - VALIDAÇÃO DE CONTEXTO:
- Você SOMENTE responde perguntas sobre Espiritismo, Doutrina Espírita e obras de Allan Kardec
- Se a pergunta NÃO for sobre estes temas, responda EXATAMENTE:
  "Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita.
   Só posso responder perguntas relacionadas às obras de Allan Kardec e aos
   ensinamentos espíritas. Por favor, faça uma pergunta sobre Espiritismo."
- NÃO tente responder perguntas sobre: culinária, esportes, política, tecnologia,
  entretenimento, ou qualquer assunto não relacionado ao Espiritismo

INSTRUÇÕES IMPORTANTES (apenas para perguntas VÁLIDAS sobre Espiritismo):
1. Responda SEMPRE em português brasileiro correto e fluente
2. DÊ PRIORIDADE às informações de "O Livro dos Espíritos" quando disponível
3. Depois, priorize as outras obras fundamentais
4. SEMPRE cite os livros de onde extraiu as informações
5. Faça correlações entre diferentes trechos quando relevante
6. Reflita sobre as implicações dos ensinamentos apresentados
7. Mantenha coerência com o contexto da conversa anterior

PROCESSO DE RACIOCÍNIO (siga este método antes de responder):
Antes de formular sua resposta, analise mentalmente:

a) ANÁLISE DA PERGUNTA:
   - Quais conceitos espíritas estão sendo questionados?
   - A pergunta requer explicação simples ou síntese de múltiplas ideias?
   - Há algum equívoco comum que devo esclarecer?

b) ANÁLISE DAS FONTES:
   - Quais trechos são mais relevantes e autoritativos?
   - Há prioridade de "O Livro dos Espíritos" disponível?
   - Os trechos se complementam ou apresentam perspectivas diferentes?

c) SÍNTESE E CONEXÕES:
   - Como conectar as informações de forma coerente?
   - Que correlações posso fazer entre diferentes passagens?
   - Como relacionar com o histórico da conversa (se houver)?

d) VERIFICAÇÃO:
   - Minha resposta está fiel à Codificação?
   - Estou citando as fontes corretamente?
   - A explicação está clara e acessível?

{conversation_context}

CONTEXTO DOS LIVROS ESPÍRITAS:
{context}

PERGUNTA DO CONSULENTE: {question}

RESPOSTA (em português correto, reflexiva, citando fontes - aplique o raciocínio acima mentalmente):"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["conversation_context", "context", "question"]
    )
    
    llm = Ollama(
        model=model_name,
        temperature=temperature,
        num_ctx=CONTEXT_WINDOW,
    )
    
    return llm, prompt

# ============================================================================
# QUERY ENDPOINT (WITH STATUS TRACKING)
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Process a question and return answer with sources
    Now with status tracking
    """
    
    if vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados não carregado."
        )

    # Validate context of the question
    if context_validator is not None:
        is_valid, confidence, reason = context_validator.validate_question(
            request.question,
            threshold=CONTEXT_VALIDATION_THRESHOLD
        )

        if not is_valid:
            # Question out of context - return rejection message
            print(f"❌ Pergunta fora de contexto: {request.question[:50]}... (score: {confidence:.2f})")

            return QueryResponse(
                task_id="rejected",
                answer=REJECTION_MESSAGE,
                sources=[],
                processing_time=0.0
            )

        print(f"✅ Pergunta validada (score: {confidence:.2f})")

    # Register request
    task_id = status_tracker.start_request(request.question, mode="normal")
    start_time = time.time()
    
    try:
        print(f"\n{'='*60}")
        print(f"🔍 [{task_id}] Nova pergunta: {request.question[:100]}...")
        
        # Update: Creating LLM
        status_tracker.update_task(task_id, "creating_llm", 10)
        llm, prompt_template = create_llm_and_prompt(
            request.model_name, 
            request.temperature
        )
        
        # Update: Searching books
        status_tracker.update_task(task_id, "searching_books", 30)
        print(f"📖 Buscando nos livros espíritas...")
        
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
        
        # Update: Building context
        status_tracker.update_task(task_id, "building_context", 50)
        
        context = "\n\n---\n\n".join([
            f"[Trecho {i+1} - {get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
            for i, doc in enumerate(sources)
        ])
        
        conversation_context = ""
        if request.conversation_history and len(request.conversation_history) > 0:
            history_text = build_context_with_history(request.conversation_history)
            if history_text:
                conversation_context = f"\nHISTÓRICO DA CONVERSA:\n{history_text}\n"
        
        formatted_prompt = prompt_template.format(
            conversation_context=conversation_context,
            context=context,
            question=request.question
        )
        
        # Update: Generating answer
        status_tracker.update_task(task_id, "generating_answer", 70)
        print(f"🤖 Gerando resposta com {request.model_name}...")
        
        answer = llm.invoke(formatted_prompt)
        
        # Update: Formatting response
        status_tracker.update_task(task_id, "formatting_response", 90)
        
        # Format sources
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
        
        processing_time = time.time() - start_time
        
        print(f"✅ Resposta gerada com sucesso em {processing_time:.2f}s!")
        print(f"{'='*60}\n")
        
        # Mark as complete
        status_tracker.complete_request(task_id, success=True)
        
        return QueryResponse(
            task_id=task_id,
            answer=answer,
            sources=formatted_sources,
            processing_time=processing_time
        )
        
    except Exception as e:
        print(f"❌ Erro ao processar pergunta: {str(e)}")
        status_tracker.complete_request(task_id, success=False, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

# ============================================================================
# STREAMING ENDPOINT (WITH STATUS)
# ============================================================================

@app.post("/query_stream")
async def query_stream(request: QueryRequest):
    """Process a question and stream the response with status tracking"""

    if vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados não carregado."
        )

    # Validate context of the question
    if context_validator is not None:
        is_valid, confidence, reason = context_validator.validate_question(
            request.question,
            threshold=CONTEXT_VALIDATION_THRESHOLD
        )

        if not is_valid:
            # Return rejection via streaming
            print(f"❌ Pergunta fora de contexto: {request.question[:50]}... (score: {confidence:.2f})")

            async def generate_rejection():
                yield f"data: {json.dumps({'type': 'task_id', 'task_id': 'rejected'})}\n\n"
                yield f"data: {json.dumps({'type': 'token', 'content': REJECTION_MESSAGE})}\n\n"
                yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            return StreamingResponse(generate_rejection(), media_type="text/event-stream")

        print(f"✅ Pergunta validada (score: {confidence:.2f})")

    task_id = status_tracker.start_request(request.question, mode="streaming")
    
    async def generate():
        try:
            # Send task_id first
            yield f"data: {json.dumps({'type': 'task_id', 'task_id': task_id})}\n\n"
            
            status_tracker.update_task(task_id, "creating_llm", 10)
            llm, prompt_template = create_llm_and_prompt(
                request.model_name, 
                request.temperature
            )
            
            status_tracker.update_task(task_id, "searching_books", 30)
            yield f"data: {json.dumps({'type': 'status', 'stage': 'searching', 'progress': 30})}\n\n"
            
            sources = prioritized_search(
                vectorstore, 
                request.question, 
                k=request.top_k, 
                fetch_k=request.fetch_k
            )
            
            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)
            
            status_tracker.update_task(task_id, "building_context", 50)
            
            context = "\n\n---\n\n".join([
                f"[Trecho {i+1} - {get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                for i, doc in enumerate(sources)
            ])
            
            conversation_context = ""
            if request.conversation_history and len(request.conversation_history) > 0:
                history_text = build_context_with_history(request.conversation_history)
                if history_text:
                    conversation_context = f"\nHISTÓRICO DA CONVERSA:\n{history_text}\n"
            
            formatted_prompt = prompt_template.format(
                conversation_context=conversation_context,
                context=context,
                question=request.question
            )
            
            status_tracker.update_task(task_id, "generating_answer", 70)
            yield f"data: {json.dumps({'type': 'status', 'stage': 'generating', 'progress': 70})}\n\n"

            # Stream tokens (character by character for smoother display)
            import time
            for chunk in llm.stream(formatted_prompt):
                # Split chunk into smaller pieces for smoother streaming
                # Send every 2-3 characters for natural reading pace
                chunk_size = 3
                for i in range(0, len(chunk), chunk_size):
                    mini_chunk = chunk[i:i+chunk_size]
                    yield f"data: {json.dumps({'type': 'token', 'content': mini_chunk})}\n\n"
                    # Tiny delay for smoother display (optional, comment out if too slow)
                    # time.sleep(0.01)
            
            # Send sources
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
            
            status_tracker.complete_request(task_id, success=True)
            
        except Exception as e:
            print(f"❌ Erro no streaming: {str(e)}")
            status_tracker.complete_request(task_id, success=False, error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor API v1.2.1 (Status Tracking)...")
    print("🔍 Rodando em: http://localhost:8000")
    print("📖 Documentação: http://localhost:8000/docs")
    print("📊 Status: http://localhost:8000/status\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")