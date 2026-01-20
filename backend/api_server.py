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

# Modelos
FAST_MODEL = "llama3.2:3b"      # Para preview rápido
QUALITY_MODEL = "qwen2.5:7b"    # Para resposta final

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

# LLMs
fast_llm = None
quality_llm = None

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
    # Preview fields
    has_preview: bool = False
    preview_answer: Optional[str] = None
    validation_notes: Optional[str] = None

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    global vectorstore, fast_llm, quality_llm, startup_time
    
    startup_time = time.time()
    
    print("=" * 70)
    print("🚀 Assistente Espírita API v1.5.0")
    print("   Sistema com Preview Automático")
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
    
    # Load LLMs
    print("\n🤖 Carregando modelos...")
    print(f"  1/2 {FAST_MODEL} (preview rápido)...")
    fast_llm = Ollama(model=FAST_MODEL, temperature=0.3, num_ctx=4096)
    print(f"      ✅ Carregado")
    
    print(f"  2/2 {QUALITY_MODEL} (resposta final)...")
    quality_llm = Ollama(model=QUALITY_MODEL, temperature=0.3, num_ctx=CONTEXT_WINDOW)
    print(f"      ✅ Carregado")
    
    print("\n✅ Sistema pronto!")
    print("=" * 70)
    print("💡 MODO PREVIEW:")
    print("   1. LLM gera resposta rápida (conhecimento geral)")
    print("   2. Sistema busca nos livros")
    print("   3. LLM valida e corrige a resposta")
    print("   4. Retorna: preview + resposta final + correções")
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

def create_preview_prompt() -> PromptTemplate:
    """Prompt para resposta prévia rápida (sem livros)"""
    template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

{conversation_context}

IMPORTANTE: Você DEVE responder APENAS perguntas relacionadas a:
- Espiritismo e Doutrina Espírita
- Allan Kardec e a Codificação Espírita
- Temas espirituais, religião, filosofia relacionados ao Espiritismo
- Mediunidade, perispírito, reencarnação, evolução espiritual
- Moral, ética e ensinamentos dos Espíritos

Se a pergunta NÃO for relacionada a estes temas, responda EXATAMENTE:
"Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita. Não posso responder perguntas sobre outros assuntos. Por favor, faça uma pergunta relacionada ao Espiritismo."

Se a pergunta for sobre Espiritismo, siga estas instruções:
1. Responda APENAS a pergunta atual (não repita respostas anteriores)
2. Use o histórico APENAS se a pergunta atual fizer referência direta a algo anterior (ex: "e sobre isso?", "pode explicar melhor?", "qual a diferença?")
3. Se a pergunta atual for completamente nova e independente, IGNORE o histórico
4. Seja conciso (2-3 parágrafos) e correto
5. Se você NÃO tiver certeza ou conhecimento suficiente, responda: "Preciso consultar os livros da Codificação para responder com precisão."

PERGUNTA ATUAL: {question}

RESPOSTA PRÉVIA (baseada em conhecimento geral):"""

    return PromptTemplate(
        template=template,
        input_variables=["conversation_context", "question"]
    )

def create_validation_prompt() -> PromptTemplate:
    """Prompt para validar preview com os livros"""
    template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

TAREFA: Validar e melhorar a resposta prévia usando os trechos dos livros.

{conversation_context}

PERGUNTA ATUAL: {question}

RESPOSTA PRÉVIA (baseada em conhecimento geral):
{preview_answer}

TRECHOS DOS LIVROS ESPÍRITAS (priorizados):
{context}

RESTRIÇÃO DE ESCOPO:
Se a resposta prévia indica que a pergunta está FORA DO ESCOPO do Espiritismo (contém a mensagem "Desculpe, sou um assistente especializado..."), você DEVE:
1. Manter EXATAMENTE a mesma mensagem de rejeição
2. NÃO tentar responder a pergunta
3. NÃO adicionar notas de validação
4. Retornar apenas a mensagem de rejeição

Se a pergunta for sobre Espiritismo, siga estas INSTRUÇÕES CRÍTICAS:
1. Responda APENAS a pergunta atual - NUNCA repita respostas de perguntas anteriores
2. Use o histórico APENAS se a pergunta atual fizer referência direta ao contexto anterior
3. Se a pergunta for completamente nova e independente, trate-a isoladamente
4. MANTENHA o que está correto na resposta prévia
5. CORRIJA o que está errado ou impreciso usando os trechos dos livros
6. ADICIONE citações específicas dos livros para fundamentar a resposta
7. PRIORIZE O Livro dos Espíritos nas citações
8. Seja mais detalhado e fundamentado que a prévia

No final, adicione uma linha indicando:
[VALIDAÇÃO: o que foi mantido, corrigido ou adicionado]

RESPOSTA FINAL VALIDADA (responda APENAS a pergunta atual):"""

    return PromptTemplate(
        template=template,
        input_variables=["conversation_context", "question", "preview_answer", "context"]
    )

async def generate_preview(llm, prompt, question: str, conversation_context: str) -> str:
    """Gera resposta prévia em thread separada"""
    loop = asyncio.get_event_loop()

    def _generate():
        formatted = prompt.format(
            conversation_context=conversation_context,
            question=question
        )
        return llm.invoke(formatted)

    return await loop.run_in_executor(executor, _generate)

async def search_books_async(question: str, top_k: int, fetch_k: int) -> List:
    """Busca nos livros de forma assíncrona"""
    loop = asyncio.get_event_loop()
    
    def _search():
        return prioritized_search(vectorstore, question, k=top_k, fetch_k=fetch_k)
    
    return await loop.run_in_executor(executor, _search)

def extract_validation_notes(validated_answer: str) -> Tuple[str, str]:
    """Extrai notas de validação da resposta"""
    if "[VALIDAÇÃO:" in validated_answer:
        parts = validated_answer.split("[VALIDAÇÃO:")
        answer = parts[0].strip()
        notes = parts[1].strip().rstrip("]")
        return answer, notes
    return validated_answer, ""

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
        "models_loaded": {
            "fast": FAST_MODEL,
            "quality": QUALITY_MODEL,
            "both_ready": fast_llm is not None and quality_llm is not None
        },
        "cache": cache_stats,
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# QUERY ENDPOINT COM PREVIEW AUTOMÁTICO
# ============================================================================

@app.post("/query/stream")
async def query_stream(request_body: QueryRequest, request: Request):
    """
    Endpoint de streaming que envia preview primeiro, depois resposta final

    Retorna eventos Server-Sent Events (SSE):
    1. event: preview - Resposta rápida do modelo fast
    2. event: sources - Fontes encontradas nos livros
    3. event: answer - Resposta final validada
    4. event: done - Processamento completo
    """

    if vectorstore is None or fast_llm is None or quality_llm is None:
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

            # FASE 1: Gerar preview (enviar imediatamente)
            preview_prompt = create_preview_prompt()
            formatted_preview = preview_prompt.format(
                conversation_context=conversation_context,
                question=request_body.question
            )

            preview_answer = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: fast_llm.invoke(formatted_preview)
            )

            # Enviar preview
            yield f"event: preview\n"
            yield f"data: {json.dumps({'answer': preview_answer, 'task_id': task_id}, ensure_ascii=False)}\n\n"

            # Check if question is out of scope
            if "Desculpe, sou um assistente especializado" in preview_answer:
                # Question is off-topic, skip book search and validation
                processing_time = time.time() - start_time
                yield f"event: answer\n"
                yield f"data: {json.dumps({'answer': preview_answer, 'validation_notes': None, 'processing_time': processing_time, 'out_of_scope': True}, ensure_ascii=False)}\n\n"

                yield f"event: done\n"
                yield f"data: {json.dumps({'task_id': task_id, 'total_time': processing_time, 'out_of_scope': True}, ensure_ascii=False)}\n\n"
                return

            # FASE 2: Buscar nos livros (em paralelo ao preview sendo exibido)
            sources = await search_books_async(
                request_body.question,
                request_body.top_k,
                request_body.fetch_k
            )

            # Adicionar metadados
            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)

            # Formatar sources
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

            # Enviar sources
            yield f"event: sources\n"
            yield f"data: {json.dumps({'sources': formatted_sources, 'count': len(formatted_sources)}, ensure_ascii=False)}\n\n"

            # FASE 3: Validar com os livros
            context = "\n\n---\n\n".join([
                f"[{get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                for doc in sources
            ])

            validation_prompt = create_validation_prompt()
            formatted_validation = validation_prompt.format(
                conversation_context=conversation_context,
                question=request_body.question,
                preview_answer=preview_answer,
                context=context
            )

            validated_answer = await asyncio.get_event_loop().run_in_executor(
                executor,
                lambda: quality_llm.invoke(formatted_validation)
            )

            # Extrair notas de validação
            final_answer, validation_notes = extract_validation_notes(validated_answer)

            processing_time = time.time() - start_time

            # Enviar resposta final
            yield f"event: answer\n"
            yield f"data: {json.dumps({'answer': final_answer, 'validation_notes': validation_notes, 'processing_time': processing_time}, ensure_ascii=False)}\n\n"

            # Enviar done
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
    Endpoint principal com preview automático integrado
    
    Fluxo:
    1. Gera resposta prévia rápida (LLM sem livros)
    2. Busca nos livros (paralelo)
    3. Valida preview com os livros (LLM com contexto)
    4. Retorna ambas + notas de validação
    """
    
    if vectorstore is None or fast_llm is None or quality_llm is None:
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
            QUALITY_MODEL,
            request_body.temperature
        )
        if cached:
            print(f"✅ CACHE HIT")
            return QueryResponse(**cached)
    
    # 3. PROCESSAR COM PREVIEW
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
        
        if request_body.enable_preview:
            # ============================================================
            # MODO PREVIEW: Resposta rápida + validação
            # ============================================================
            
            print("⚡ Fase 1: Gerando preview + buscando livros (paralelo)...")
            
            # Preparar prompts
            preview_prompt = create_preview_prompt()
            
            # Executar em paralelo: preview + busca
            preview_task = generate_preview(
                fast_llm,
                preview_prompt,
                request_body.question,
                conversation_context
            )
            
            search_task = search_books_async(
                request_body.question,
                request_body.top_k,
                request_body.fetch_k
            )
            
            # Aguardar ambos
            preview_answer, sources = await asyncio.gather(preview_task, search_task)

            print(f"✅ Preview: {len(preview_answer)} chars")

            # Check if question is out of scope
            if "Desculpe, sou um assistente especializado" in preview_answer:
                print(f"⚠️ Pergunta fora do escopo do Espiritismo")
                final_answer = preview_answer
                validation_notes = None
                sources = []  # No sources for off-topic questions
            else:
                print(f"✅ Fontes: {len(sources)} trechos")

                # Adicionar metadados de prioridade
                for source in sources:
                    source_path = source.metadata.get('source', '')
                    source.metadata['priority'] = get_book_priority(source_path)

                # Construir contexto dos livros
                context = "\n\n---\n\n".join([
                    f"[{get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                    for doc in sources
                ])

                # Fase 2: Validar com os livros
                print("📚 Fase 2: Validando com os livros...")

                validation_prompt = create_validation_prompt()
                formatted_validation = validation_prompt.format(
                    conversation_context=conversation_context,
                    question=request_body.question,
                    preview_answer=preview_answer,
                    context=context
                )

                validated_answer = quality_llm.invoke(formatted_validation)

                # Extrair notas de validação
                final_answer, validation_notes = extract_validation_notes(validated_answer)

                print(f"✅ Validação completa!")
            
        else:
            # ============================================================
            # MODO NORMAL: Somente busca + resposta
            # ============================================================
            
            print("📚 Modo normal: Buscando nos livros...")
            
            sources = prioritized_search(
                vectorstore,
                request_body.question,
                k=request_body.top_k,
                fetch_k=request_body.fetch_k
            )
            
            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)
            
            context = "\n\n---\n\n".join([
                f"[{get_book_display_name(doc.metadata.get('source', 'Desconhecido'))}]\n{doc.page_content}"
                for doc in sources
            ])
            
            # Prompt simples
            simple_template = """Você é um assistente especializado em Espiritismo.

INSTRUÇÕES:
1. Responda em português brasileiro
2. PRIORIZE O Livro dos Espíritos
3. SEMPRE cite as fontes com precisão

{conversation_context}

CONTEXTO DOS LIVROS:
{context}

PERGUNTA: {question}

RESPOSTA:"""
            
            simple_prompt = PromptTemplate(
                template=simple_template,
                input_variables=["conversation_context", "context", "question"]
            )
            
            formatted = simple_prompt.format(
                conversation_context=conversation_context,
                context=context,
                question=request_body.question
            )
            
            final_answer = quality_llm.invoke(formatted)
            preview_answer = None
            validation_notes = None
        
        # Formatar sources
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
            "has_preview": request_body.enable_preview,
            "preview_answer": preview_answer,
            "validation_notes": validation_notes
        }
        
        # Cache
        if request_body.use_cache:
            response_cache.set(
                request_body.question,
                QUALITY_MODEL,
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