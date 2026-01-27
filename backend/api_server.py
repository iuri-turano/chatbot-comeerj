from fastapi import FastAPI, HTTPException, Request
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
import asyncio
import time
import hashlib
from typing import List, Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from collections import deque, defaultdict
import threading

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

MAX_CONCURRENT_REQUESTS = 4
CACHE_SIZE = 500
RATE_LIMIT_PER_MINUTE = 15

# Modelo único
MODEL = "llama3.1:8b"  # Modelo principal para todas as operações

app = FastAPI(
    title="Assistente Espírita API",
    description="Sistema com Preview Automático - Responde Rápido e Valida com Livros",
    version="1.5.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CACHE E RATE LIMITER
# ============================================================================

class ResponseCache:
    def __init__(self, max_size=CACHE_SIZE):
        self._cache = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self.max_size = max_size
    
    def _hash_query(self, question: str, model: str, temp: float) -> str:
        key = f"{question.lower().strip()}|{model}|{temp:.1f}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, question: str, model: str, temp: float) -> Optional[Dict]:
        with self._lock:
            cache_key = self._hash_query(question, model, temp)
            if cache_key in self._cache:
                self._hits += 1
                return self._cache[cache_key].copy()
            self._misses += 1
            return None
    
    def set(self, question: str, model: str, temp: float, response: Dict):
        with self._lock:
            cache_key = self._hash_query(question, model, temp)
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[cache_key] = {**response, 'cached_at': datetime.now().isoformat()}
    
    def get_stats(self) -> Dict:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1f}%"
            }

class RateLimiter:
    def __init__(self, max_per_minute=RATE_LIMIT_PER_MINUTE):
        self._requests = defaultdict(deque)
        self._lock = threading.Lock()
        self.max_per_minute = max_per_minute
    
    def check_rate_limit(self, ip: str) -> Tuple[bool, int]:
        with self._lock:
            now = time.time()
            minute_ago = now - 60
            requests = self._requests[ip]
            while requests and requests[0] < minute_ago:
                requests.popleft()
            if len(requests) >= self.max_per_minute:
                return False, 0
            requests.append(now)
            return True, self.max_per_minute - len(requests)

# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

startup_time = time.time()
vectorstore = None
executor = ThreadPoolExecutor(max_workers=4)

response_cache = ResponseCache(max_size=CACHE_SIZE)
rate_limiter = RateLimiter(max_per_minute=RATE_LIMIT_PER_MINUTE)

# LLM
llm = None  # Modelo único para todas as operações

# ============================================================================
# MODELS
# ============================================================================

class Message(BaseModel):
    role: str
    content: str

class QueryRequest(BaseModel):
    question: str
    temperature: float = 0.3
    top_k: int = 3
    fetch_k: int = 15
    conversation_history: Optional[List[Message]] = None
    use_cache: bool = True
    enable_preview: bool = True  # Ativa/desativa preview

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
    from_cache: bool = False
    search_plan: Optional[str] = None  # Plano de busca
    out_of_scope: bool = False  # Flag para perguntas fora do escopo

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    global vectorstore, llm, startup_time

    startup_time = time.time()

    print("=" * 70)
    print("🚀 Assistente Espírita API v2.0.0")
    print("   Sistema Simplificado com Plano de Busca")
    print("=" * 70)
    
    if not os.path.exists(DB_DIR):
        print(f"❌ Banco de dados não encontrado: {DB_DIR}")
        return
    
    print("📚 Carregando vectorstore...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    if torch.cuda.is_available():
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"💾 VRAM: {vram_gb:.1f} GB")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device}
    )
    
    vectorstore = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings
    )
    
    # Load LLM
    print("\n🤖 Carregando modelo...")
    print(f"   {MODEL}...")
    llm = Ollama(model=MODEL, temperature=0.3, num_ctx=CONTEXT_WINDOW)
    print(f"   ✅ Modelo carregado")

    print("\n✅ Sistema pronto!")
    print("=" * 70)
    print("💡 NOVO FLUXO:")
    print("   1. Detecção de tópico off-topic (semântica)")
    print("   2. Gera plano de busca nos livros")
    print("   3. Busca trechos relevantes")
    print("   4. Responde com base nos trechos encontrados")
    print("=" * 70)
    print("🌐 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("=" * 70)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

def build_context_with_history(conversation_history: List[Message], max_history: int = 5) -> str:
    if not conversation_history:
        return ""
    recent = conversation_history[-max_history:]
    parts = []
    for msg in recent:
        if msg.role == "user":
            parts.append(f"Consulente: {msg.content}")
        elif msg.role == "assistant":
            parts.append(f"Assistente: {msg.content}")
    return "\n".join(parts)

def detect_off_topic(question: str) -> Tuple[bool, str]:
    """
    Improved off-topic detection with ambiguous word handling

    Returns: (is_off_topic, reason)
    """
    question_lower = question.lower()

    # Ambiguous words that could be Spiritist or not
    ambiguous_terms = {
        "codificação": {
            "spiritist": ["kardec", "espírita", "livro", "doutrina", "espíritos"],
            "other": ["python", "utf", "caractere", "encoding", "programa", "código"]
        },
        "espírito": {
            "spiritist": ["alma", "reencarnação", "médium", "perispírito", "espírita"],
            "other": ["bebida", "álcool", "destilado", "cachaça"]
        },
        "médium": {
            "spiritist": ["psicografia", "incorporação", "comunicação", "espíritos", "faculdade"],
            "other": ["roupa", "tamanho", "vestuário", "p", "g", "gg"]
        }
    }

    # Check for ambiguous terms
    for term, contexts in ambiguous_terms.items():
        if term in question_lower:
            # Check for Spiritist context
            has_spiritist = any(kw in question_lower for kw in contexts["spiritist"])
            has_other = any(kw in question_lower for kw in contexts["other"])

            if has_other and not has_spiritist:
                return (True, f"Termo '{term}' usado em contexto não-espírita")
            # If spiritist context or unclear, continue (let LLM decide)

    # Check for obvious off-topic keywords
    off_topic_keywords = [
        "python", "javascript", "código", "programar", "script", "html", "css",
        "receita", "cozinha", "comida", "bolo", "prato",
        "futebol", "jogo", "esporte", "time", "partida",
        "filme", "série", "netflix", "cinema",
        "matemática", "física", "química", "cálculo"
    ]

    for keyword in off_topic_keywords:
        if keyword in question_lower:
            # Double-check it's not in a Spiritist context
            spiritist_keywords = ["kardec", "espírita", "espiritismo", "evangelho", "médium", "espírito", "doutrina"]
            if not any(sk in question_lower for sk in spiritist_keywords):
                return (True, f"Palavra-chave não relacionada: '{keyword}'")

    return (False, "")

def create_search_plan_prompt() -> PromptTemplate:
    """Prompt para gerar plano de busca nos livros"""
    template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

{conversation_context}

TAREFA: Analise a pergunta e crie um PLANO DE BUSCA conciso para consultar os livros da Codificação.

INSTRUÇÕES:
1. Identifique os conceitos-chave da pergunta
2. Liste 2-4 tópicos específicos para buscar nos livros
3. Seja objetivo e direto (máximo 4 linhas)
4. Use bullet points (-)
5. Não responda a pergunta, apenas planeje a busca

PERGUNTA: {question}

PLANO DE BUSCA:"""

    return PromptTemplate(
        template=template,
        input_variables=["conversation_context", "question"]
    )

def create_answer_prompt() -> PromptTemplate:
    """Prompt principal para responder com base nos livros"""
    template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

{conversation_context}

PERGUNTA: {question}

TRECHOS DOS LIVROS ESPÍRITAS (priorizados):
{context}

INSTRUÇÕES:
1. Responda APENAS a pergunta atual (não repita respostas anteriores)
2. Use o histórico apenas se a pergunta fizer referência direta ("isso", "aquilo", "pode explicar melhor")
3. Fundamente sua resposta nos trechos fornecidos acima
4. PRIORIZE citações do Livro dos Espíritos
5. Seja claro, detalhado e preciso
6. Cite as fontes quando relevante (ex: "Segundo O Livro dos Espíritos...")
7. Se os trechos não forem suficientes, diga que precisa consultar mais

RESPOSTA:"""

    return PromptTemplate(
        template=template,
        input_variables=["conversation_context", "question", "context"]
    )

async def generate_search_plan(llm_instance, prompt, question: str, conversation_context: str) -> str:
    """Gera plano de busca em thread separada"""
    loop = asyncio.get_event_loop()

    def _generate():
        formatted = prompt.format(
            conversation_context=conversation_context,
            question=question
        )
        return llm_instance.invoke(formatted)

    return await loop.run_in_executor(executor, _generate)

async def search_books_async(question: str, top_k: int, fetch_k: int) -> List:
    """Busca nos livros de forma assíncrona"""
    loop = asyncio.get_event_loop()
    
    def _search():
        return prioritized_search(vectorstore, question, k=top_k, fetch_k=fetch_k)
    
    return await loop.run_in_executor(executor, _search)


# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@app.get("/health")
async def health():
    """Health check with GPU info"""
    cuda_available = torch.cuda.is_available()
    gpu_name = "CPU"
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
    
    return {
        "status": "healthy",
        "cuda_available": cuda_available,
        "gpu": gpu_name,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/status")
async def status():
    cache_stats = response_cache.get_stats()

    # Check CUDA availability
    cuda_available = torch.cuda.is_available()
    gpu_name = "CPU"
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)

    return {
        "online": True,
        "uptime_seconds": time.time() - startup_time,
        "cuda_available": cuda_available,
        "gpu": gpu_name,
        "model": MODEL,
        "model_loaded": llm is not None,
        "cache": cache_stats,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# QUERY ENDPOINT COM PREVIEW AUTOMÁTICO
# ============================================================================

@app.post("/query/stream")
async def query_stream(request_body: QueryRequest, request: Request):
    """
    Endpoint de streaming com plano de busca

    Retorna eventos Server-Sent Events (SSE):
    1. event: search_plan - Plano de busca nos livros
    2. event: sources - Fontes encontradas nos livros
    3. event: answer - Resposta final baseada nas fontes
    4. event: done - Processamento completo
    """

    if vectorstore is None or llm is None:
        raise HTTPException(status_code=503, detail="Sistema não carregado")

    # Rate limit
    client_ip = get_client_ip(request)
    allowed, remaining = rate_limiter.check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Rate limit: {RATE_LIMIT_PER_MINUTE}/min")

    async def generate_stream():
        task_id = f"task_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            # Build conversation context
            conversation_context = ""
            if request_body.conversation_history:
                history = build_context_with_history(request_body.conversation_history)
                if history:
                    conversation_context = f"\nHISTÓRICO:\n{history}\n"

            # PHASE 1: Off-topic detection (improved)
            is_off_topic, reason = detect_off_topic(request_body.question)
            if is_off_topic:
                rejection_msg = f"Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita. Não posso responder perguntas sobre outros assuntos. ({reason})"
                processing_time = time.time() - start_time
                yield f"event: answer\n"
                yield f"data: {json.dumps({'answer': rejection_msg, 'out_of_scope': True, 'processing_time': processing_time}, ensure_ascii=False)}\n\n"
                yield f"event: done\n"
                yield f"data: {json.dumps({'task_id': task_id, 'total_time': processing_time, 'out_of_scope': True}, ensure_ascii=False)}\n\n"
                return

            # PHASE 2: Generate search plan
            search_plan_prompt = create_search_plan_prompt()
            search_plan = await generate_search_plan(
                llm,
                search_plan_prompt,
                request_body.question,
                conversation_context
            )

            # Send search plan to client
            yield f"event: search_plan\n"
            yield f"data: {json.dumps({'plan': search_plan, 'task_id': task_id}, ensure_ascii=False)}\n\n"

            # PHASE 3: Search books
            sources = await search_books_async(
                request_body.question,
                request_body.top_k,
                request_body.fetch_k
            )

            # Add metadata
            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)

            # Format sources
            formatted_sources = []
            for source in sources:
                source_path = source.metadata.get('source', 'Desconhecido')
                priority = source.metadata.get('priority', 10)

                priority_label = (
                    "PRIORIDADE MÁXIMA" if priority >= 100 else
                    "OBRA FUNDAMENTAL" if priority >= 70 else
                    "COMPLEMENTAR" if priority >= 40 else
                    "OUTRAS OBRAS"
                )

                formatted_sources.append({
                    "content": source.page_content[:500],
                    "source": os.path.basename(source_path),
                    "page": source.metadata.get('page', 0),
                    "priority": priority,
                    "priority_label": priority_label,
                    "display_name": get_book_display_name(source_path)
                })

            # Send sources
            yield f"event: sources\n"
            yield f"data: {json.dumps({'sources': formatted_sources, 'count': len(formatted_sources)}, ensure_ascii=False)}\n\n"

            # PHASE 4: Generate final answer
            context = "\n\n---\n\n".join([
                f"[{get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                for doc in sources
            ])

            answer_prompt = create_answer_prompt()
            formatted_answer = answer_prompt.format(
                conversation_context=conversation_context,
                question=request_body.question,
                context=context
            )

            final_answer = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: llm.invoke(formatted_answer)
            )

            processing_time = time.time() - start_time

            # Send final answer
            yield f"event: answer\n"
            yield f"data: {json.dumps({'answer': final_answer, 'processing_time': processing_time}, ensure_ascii=False)}\n\n"

            # Send done
            yield f"event: done\n"
            yield f"data: {json.dumps({'task_id': task_id, 'total_time': processing_time}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/query", response_model=QueryResponse)
async def query(request_body: QueryRequest, request: Request):
    """
    Endpoint principal simplificado

    Fluxo:
    1. Detecção de off-topic
    2. Gera plano de busca
    3. Busca nos livros
    4. Responde com base nos trechos
    """

    if vectorstore is None or llm is None:
        raise HTTPException(status_code=503, detail="Sistema não carregado")

    # 1. RATE LIMIT
    client_ip = get_client_ip(request)
    allowed, remaining = rate_limiter.check_rate_limit(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Rate limit: {RATE_LIMIT_PER_MINUTE}/min")

    # 2. CHECK CACHE
    if request_body.use_cache:
        cached = response_cache.get(
            request_body.question,
            MODEL,
            request_body.temperature
        )
        if cached:
            print(f"✅ CACHE HIT")
            return QueryResponse(**cached)

    # 3. PROCESS REQUEST
    task_id = f"task_{int(time.time() * 1000)}"
    start_time = time.time()

    try:
        print(f"\n{'='*70}")
        print(f"❓ Pergunta: {request_body.question[:80]}...")

        # Build conversation context
        conversation_context = ""
        if request_body.conversation_history:
            history = build_context_with_history(request_body.conversation_history)
            if history:
                conversation_context = f"\nHISTÓRICO:\n{history}\n"

        # PHASE 1: Off-topic detection
        is_off_topic, reason = detect_off_topic(request_body.question)
        if is_off_topic:
            print(f"⚠️ Pergunta fora do escopo: {reason}")
            rejection_msg = f"Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita. Não posso responder perguntas sobre outros assuntos. ({reason})"
            processing_time = time.time() - start_time

            response_data = {
                "task_id": task_id,
                "answer": rejection_msg,
                "sources": [],
                "processing_time": processing_time,
                "from_cache": False,
                "search_plan": None,
                "out_of_scope": True
            }
            return QueryResponse(**response_data)

        # PHASE 2: Generate search plan
        print("🔍 Fase 1: Gerando plano de busca...")
        search_plan_prompt = create_search_plan_prompt()
        search_plan = await generate_search_plan(
            llm,
            search_plan_prompt,
            request_body.question,
            conversation_context
        )
        print(f"✅ Plano: {len(search_plan)} chars")

        # PHASE 3: Search books
        print("📚 Fase 2: Buscando nos livros...")
        sources = prioritized_search(
            vectorstore,
            request_body.question,
            k=request_body.top_k,
            fetch_k=request_body.fetch_k
        )

        for source in sources:
            source_path = source.metadata.get('source', '')
            source.metadata['priority'] = get_book_priority(source_path)

        print(f"✅ Fontes: {len(sources)} trechos")

        # PHASE 4: Generate answer
        print("💬 Fase 3: Gerando resposta...")
        context = "\n\n---\n\n".join([
            f"[{get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
            for doc in sources
        ])

        answer_prompt = create_answer_prompt()
        formatted_answer = answer_prompt.format(
            conversation_context=conversation_context,
            question=request_body.question,
            context=context
        )

        final_answer = llm.invoke(formatted_answer)

        # Format sources
        formatted_sources = []
        for source in sources:
            source_path = source.metadata.get('source', 'Desconhecido')
            priority = source.metadata.get('priority', 10)

            priority_label = (
                "PRIORIDADE MÁXIMA" if priority >= 100 else
                "OBRA FUNDAMENTAL" if priority >= 70 else
                "COMPLEMENTAR" if priority >= 40 else
                "OUTRAS OBRAS"
            )

            formatted_sources.append(Source(
                content=source.page_content[:500],
                source=os.path.basename(source_path),
                page=source.metadata.get('page', 0),
                priority=priority,
                priority_label=priority_label,
                display_name=get_book_display_name(source_path)
            ))

        processing_time = time.time() - start_time
        print(f"✅ Concluído em {processing_time:.2f}s")
        print(f"{'='*70}\n")

        response_data = {
            "task_id": task_id,
            "answer": final_answer,
            "sources": [s.dict() for s in formatted_sources],
            "processing_time": processing_time,
            "from_cache": False,
            "search_plan": search_plan,
            "out_of_scope": False
        }

        # Cache
        if request_body.use_cache:
            response_cache.set(
                request_body.question,
                MODEL,
                request_body.temperature,
                response_data
            )

        return QueryResponse(**response_data)

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def save_feedback_endpoint(request: Request):
    """Save user feedback"""
    try:
        data = await request.json()
        
        # Create feedback directory if needed
        feedback_dir = "feedback"
        if not os.path.exists(feedback_dir):
            os.makedirs(feedback_dir)
        
        feedback_file = os.path.join(feedback_dir, "responses_feedback.jsonl")
        
        # Prepare feedback entry
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": data.get("user_name", "Anonymous"),
            "question": data.get("question", ""),
            "answer": data.get("answer", ""),
            "keywords": data.get("keywords", []),
            "sources": data.get("sources", []),
            "rating": data.get("rating", "neutral"),
            "comment": data.get("comment", "")
        }
        
        # Append to JSONL file
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')
        
        return {"status": "success", "message": "Feedback saved"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics"""
    try:
        feedback_file = os.path.join("feedback", "responses_feedback.jsonl")
        
        if not os.path.exists(feedback_file):
            return {
                "total": 0,
                "good": 0,
                "neutral": 0,
                "bad": 0,
                "feedbacks": []
            }
        
        feedbacks = []
        with open(feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    feedbacks.append(json.loads(line))
        
        stats = {
            "total": len(feedbacks),
            "good": sum(1 for f in feedbacks if f.get("rating") == "good"),
            "neutral": sum(1 for f in feedbacks if f.get("rating") == "neutral"),
            "bad": sum(1 for f in feedbacks if f.get("rating") == "bad"),
            "feedbacks": feedbacks[-100:]  # Last 100 feedbacks
        }
        
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando API v1.5.0 (Preview Automático)...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")