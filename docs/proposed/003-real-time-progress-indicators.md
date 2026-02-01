# Proposta 003: Indicadores de Progresso em Tempo Real (Estilo Perplexity)

**Status**: 🟡 PARCIALMENTE IMPLEMENTADO
**Prioridade**: 🔶 ALTA
**Esforço Estimado**: Médio (4-5 horas)
**Impacto**: Alto - UX/UI significativamente melhorada

---

## 📋 Resumo

Completar a implementação dos indicadores de progresso em tempo real que mostram ao usuário exatamente o que o sistema está fazendo durante o processamento, similar à experiência do Perplexity AI.

## 🎯 Objetivo Declarado (CLAUDE.md)

> "Interface Estilo Perplexity com indicadores de processo em tempo real"

**Comportamento Esperado (CLAUDE.md linhas 30-35):**
```
🔍 Consultando os livros...
├─ [10%] Criando modelo LLM
├─ [30%] Buscando nos livros espíritas
├─ [50%] Construindo contexto
├─ [70%] Gerando resposta
└─ [90%] Formatando resposta
```

**Experiência Desejada:**
- Usuário vê **5 estágios distintos** de processamento
- Cada estágio mostra **texto descritivo** + **porcentagem**
- **Animação visual** (barra de progresso ou spinner)
- **Transparência total** sobre o que está acontecendo
- **Feedback contínuo** durante todo o processamento

## ❌ Situação Atual

### ✅ O que está IMPLEMENTADO (Backend)

**Backend tem infraestrutura completa:**

1. **Sistema de Status** (`api_server.py` linhas 46-136):
   ```python
   class ServerStatus:
       def update_task(self, task_id: str, stage: str, progress: int)
   ```

2. **Stages Definidos** (`api_server.py`):
   - ✅ "creating_llm" (10%)
   - ✅ "searching_books" (30%)
   - ✅ "building_context" (50%)
   - ✅ "generating_answer" (70%)
   - ✅ "formatting_response" (90%)

3. **Tracking Interno** (linhas 425, 432, 450, 470, 476):
   ```python
   status_tracker.update_task(task_id, "creating_llm", 10)
   status_tracker.update_task(task_id, "searching_books", 30)
   status_tracker.update_task(task_id, "building_context", 50)
   status_tracker.update_task(task_id, "generating_answer", 70)
   status_tracker.update_task(task_id, "formatting_response", 90)
   ```

### ❌ O que está FALTANDO

**Problema 1: Backend não envia todos os stages para o frontend**

Código atual (`api_server.py` linhas 549-583):
```python
# Apenas 2 de 5 stages são enviados via streaming:
yield f"data: {json.dumps({'type': 'status', 'stage': 'searching', 'progress': 30})}\n\n"
# ^ Linha 550

yield f"data: {json.dumps({'type': 'status', 'stage': 'generating', 'progress': 70})}\n\n"
# ^ Linha 583

# FALTAM: creating_llm (10%), building_context (50%), formatting_response (90%)
```

**Problema 2: Frontend não exibe os indicadores**

Código atual (`frontend/app.py` linhas 545, 584):
```python
# Apenas um spinner genérico:
with st.spinner("🔍 Consultando os livros..."):
    # Processa resposta mas NÃO mostra progresso

# Não processa eventos de status:
for chunk, chunk_sources in stream_api_response(...):
    if chunk:
        full_response += chunk
    # NÃO verifica se é evento de status!
```

**Problema 3: stream_api_response não extrai status**

Código atual (`frontend/app.py` linhas 211-263):
```python
def stream_api_response(...):
    for line in response.iter_lines():
        data = json.loads(line[6:])

        if data['type'] == 'token':
            yield data['content'], None
        elif data['type'] == 'sources':
            sources = data['sources']
        # FALTA: elif data['type'] == 'status'
```

## ✅ Solução Proposta

### Arquitetura de 3 Camadas

```
┌───────────────────────────────────────────────────┐
│  CAMADA 1: BACKEND (api_server.py)                │
│  - Yield ALL 5 stages via streaming               │
│  - Enviar task_id, stage, progress, description   │
└───────────┬───────────────────────────────────────┘
            │ SSE Stream
            ▼
┌───────────────────────────────────────────────────┐
│  CAMADA 2: FRONTEND API (app.py)                  │
│  - Parsear eventos de status                      │
│  - Separar status, tokens, sources                │
│  - Yield tuplas (chunk, sources, status)          │
└───────────┬───────────────────────────────────────┘
            │ Generator
            ▼
┌───────────────────────────────────────────────────┐
│  CAMADA 3: FRONTEND UI (app.py)                   │
│  - Exibir barra de progresso                      │
│  - Mostrar texto do stage atual                   │
│  - Animar transições entre stages                 │
└───────────────────────────────────────────────────┘
```

### Implementação Detalhada

#### **PARTE 1: Backend - Enviar Todos os Stages**

```python
# backend/api_server.py

# Linha ~538 (modificar função query_stream)

@app.post("/query_stream")
async def query_stream(request: QueryRequest):
    """Process a question and stream the response with status tracking"""

    if vectorstore is None:
        raise HTTPException(status_code=503, detail="Banco de dados não carregado.")

    task_id = status_tracker.start_request(request.question, mode="streaming")

    async def generate():
        try:
            # Send task_id first
            yield f"data: {json.dumps({'type': 'task_id', 'task_id': task_id})}\n\n"

            # STAGE 1: Creating LLM (10%)
            status_tracker.update_task(task_id, "creating_llm", 10)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'creating_llm',
                'progress': 10,
                'description': 'Criando modelo LLM'
            })}\n\n"

            llm, prompt_template = create_llm_and_prompt(
                request.model_name,
                request.temperature
            )

            # STAGE 2: Searching books (30%)
            status_tracker.update_task(task_id, "searching_books", 30)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'searching_books',
                'progress': 30,
                'description': 'Buscando nos livros espíritas'
            })}\n\n"

            sources = prioritized_search(
                vectorstore,
                request.question,
                k=request.top_k,
                fetch_k=request.fetch_k
            )

            for source in sources:
                source_path = source.metadata.get('source', '')
                source.metadata['priority'] = get_book_priority(source_path)

            # STAGE 3: Building context (50%)
            status_tracker.update_task(task_id, "building_context", 50)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'building_context',
                'progress': 50,
                'description': 'Construindo contexto'
            })}\n\n"

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

            # STAGE 4: Generating answer (70%)
            status_tracker.update_task(task_id, "generating_answer", 70)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'generating_answer',
                'progress': 70,
                'description': 'Gerando resposta'
            })}\n\n"

            # Stream tokens
            for chunk in llm.stream(formatted_prompt):
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"

            # STAGE 5: Formatting response (90%)
            status_tracker.update_task(task_id, "formatting_response", 90)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'formatting_response',
                'progress': 90,
                'description': 'Formatando resposta'
            })}\n\n"

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

            # COMPLETE (100%)
            yield f"data: {json.dumps({
                'type': 'status',
                'stage': 'complete',
                'progress': 100,
                'description': 'Concluído'
            })}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            status_tracker.complete_request(task_id, success=True)

        except Exception as e:
            print(f"❌ Erro no streaming: {str(e)}")
            status_tracker.complete_request(task_id, success=False, error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### **PARTE 2: Frontend - Parsear Status Events**

```python
# frontend/app.py

# Linha ~211 (modificar stream_api_response)

def stream_api_response(
    question: str,
    model_name: str,
    temperature: float,
    top_k: int,
    fetch_k: int,
    conversation_history: list = None
):
    """Stream response from API with status updates"""
    try:
        # Prepare conversation history
        api_history = []
        if conversation_history:
            for msg in conversation_history:
                api_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = requests.post(
            f"{API_URL}/query_stream",
            json={
                "question": question,
                "model_name": model_name,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k,
                "conversation_history": api_history
            },
            stream=True,
            timeout=600
        )
        response.raise_for_status()

        full_text = ""
        sources = None
        current_status = None

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    import json
                    data = json.loads(line[6:])

                    if data['type'] == 'task_id':
                        # Initial task ID
                        pass

                    elif data['type'] == 'status':
                        # NOVO: Capturar eventos de status
                        current_status = {
                            'stage': data.get('stage'),
                            'progress': data.get('progress'),
                            'description': data.get('description')
                        }
                        yield None, None, current_status  # Yield status

                    elif data['type'] == 'token':
                        full_text += data['content']
                        yield data['content'], None, None  # Yield token

                    elif data['type'] == 'sources':
                        sources = data['sources']
                        # Não yield aqui, vai retornar no final

                    elif data['type'] == 'done':
                        # Final: retornar sources
                        yield None, sources, None
                        break

                    elif data['type'] == 'error':
                        raise Exception(data['content'])

    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: A resposta demorou muito.")
    except Exception as e:
        raise Exception(f"❌ Erro: {str(e)}")
```

#### **PARTE 3: Frontend - Exibir Progress UI**

```python
# frontend/app.py

# Linha ~537 (modificar chat input handling)

# Chat input
if prompt := st.chat_input("Digite sua pergunta sobre Espiritismo..."):
    if not api_status:
        st.error("❌ Backend offline. Não é possível processar perguntas.")
        return

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant", avatar="🤖"):
        if enable_streaming:
            # NOVO: Progress indicator
            progress_placeholder = st.empty()
            progress_bar = st.progress(0)
            response_placeholder = st.empty()

            full_response = ""
            sources = None
            current_stage = None

            try:
                for chunk, chunk_sources, status_update in stream_api_response(
                    prompt, model_name, temperature, top_k, fetch_k,
                    st.session_state.messages[:-1]
                ):
                    # Handle status updates
                    if status_update:
                        current_stage = status_update
                        progress = status_update['progress']
                        description = status_update['description']

                        # Update progress bar
                        progress_bar.progress(progress / 100)

                        # Update status text
                        progress_placeholder.markdown(
                            f"**🔍 {description}** ({progress}%)"
                        )

                    # Handle text chunks
                    elif chunk:
                        # Clear progress display when text starts
                        if current_stage and current_stage['stage'] == 'generating_answer':
                            progress_placeholder.empty()
                            progress_bar.empty()

                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")

                    # Handle sources
                    elif chunk_sources:
                        sources = chunk_sources

                # Clear progress indicators
                progress_placeholder.empty()
                progress_bar.empty()

                # Final response
                response_placeholder.markdown(full_response)

                # Show sources
                if sources:
                    with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                        for i, source in enumerate(sources, 1):
                            display_source(source, i)

                # Add to messages
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources
                })

                # Auto-save
                save_conversation(
                    st.session_state.current_chat_id,
                    st.session_state.messages,
                    st.session_state.user_name
                )

                st.rerun()

            except Exception as e:
                progress_placeholder.empty()
                progress_bar.empty()
                st.error(str(e))

        else:
            # Non-streaming response (código existente)
            # ...
```

#### **PARTE 4: UI Aprimorada com CSS**

```python
# frontend/app.py

# Adicionar no CSS (após linha 24)

st.markdown("""
<style>
    /* Existing CSS ... */

    /* Progress indicator styling */
    .progress-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }

    .progress-stage {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #667eea;
        font-weight: 500;
    }

    .progress-stage.active {
        color: #4ecdc4;
        font-weight: 600;
    }

    .progress-stage.completed {
        color: #95a5a6;
        opacity: 0.7;
    }

    .progress-icon {
        margin-right: 0.75rem;
        font-size: 1.2rem;
    }

    .progress-percentage {
        margin-left: auto;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Stage-specific colors */
    .stage-creating_llm { color: #3498db; }
    .stage-searching_books { color: #e74c3c; }
    .stage-building_context { color: #f39c12; }
    .stage-generating_answer { color: #2ecc71; }
    .stage-formatting_response { color: #9b59b6; }

    /* Animated progress bar */
    @keyframes progressAnimation {
        0% { width: 0%; }
        100% { width: 100%; }
    }

    .animated-progress {
        animation: progressAnimation 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)
```

### UI Mockup (Como Deve Ficar)

```
┌──────────────────────────────────────────────────┐
│  🤖 Assistente                                    │
├──────────────────────────────────────────────────┤
│                                                   │
│  🔍 Processando sua pergunta...                  │
│                                                   │
│  ┌────────────────────────────────────────────┐  │
│  │ ✓ Criando modelo LLM           [10%]      │  │
│  │ ✓ Buscando nos livros espíritas [30%]     │  │
│  │ ✓ Construindo contexto         [50%]      │  │
│  │ ▶ Gerando resposta              [70%]      │  │ ← ATIVO
│  │   Formatando resposta           [90%]      │  │
│  └────────────────────────────────────────────┘  │
│                                                   │
│  ████████████████████████░░░░░░░░ 70%            │
│                                                   │
│  [Texto sendo gerado aparece aqui...]▌           │
│                                                   │
└──────────────────────────────────────────────────┘
```

## 📊 Benefícios Esperados

### Experiência do Usuário
1. **Transparência**: Usuário sabe exatamente o que está acontecendo
2. **Confiança**: Ver processo reduz ansiedade de espera
3. **Engajamento**: Visualização torna espera mais interessante
4. **Profissionalismo**: Interface polida e moderna

### Alinhamento com Produto
1. **Cumpre Promessa**: "Estilo Perplexity" finalmente implementado
2. **Diferencial**: Poucos chatbots locais têm essa transparência
3. **Educativo**: Usuário aprende como sistema funciona

### Técnico
1. **Debugging**: Mais fácil identificar onde processo está travando
2. **Monitoramento**: Métricas por stage
3. **Feedback**: Usuários podem reportar problemas específicos por stage

## 🎯 Métricas de Sucesso

### KPIs
1. **Satisfação**: Feedback sobre nova UI
   - Meta: +30% de comentários positivos sobre interface
2. **Clareza**: % de usuários que entendem o que está acontecendo
   - Meta: >90%
3. **Performance**: Latência adicional da UI
   - Meta: <50ms overhead total

### Testes
- [ ] Testar todos os 5 stages aparecem corretamente
- [ ] Verificar transições suaves entre stages
- [ ] Validar barra de progresso atualiza corretamente
- [ ] Testar em diferentes navegadores
- [ ] Verificar responsividade mobile

## 📝 Documentação a Atualizar

### README.md
```markdown
## 🔍 Interface em Tempo Real

O assistente mostra exatamente o que está fazendo:

### Estágios Visíveis
1. **Criando modelo LLM** (10%) - Inicializando modelo de linguagem
2. **Buscando nos livros** (30%) - Procurando trechos relevantes
3. **Construindo contexto** (50%) - Organizando informações
4. **Gerando resposta** (70%) - LLM processando resposta
5. **Formatando resposta** (90%) - Preparando exibição

Você vê cada etapa em tempo real com barra de progresso!
```

## ⚙️ Configurações Ajustáveis

### Progress Descriptions
```python
# backend/api_server.py
STAGE_DESCRIPTIONS = {
    "creating_llm": "Criando modelo LLM",
    "searching_books": "Buscando nos livros espíritas",
    "building_context": "Construindo contexto",
    "generating_answer": "Gerando resposta",
    "formatting_response": "Formatando resposta"
}
```

### UI Customization
```python
# frontend/app.py
SHOW_PROGRESS_BAR = True
SHOW_PERCENTAGE = True
SHOW_STAGE_ICONS = True
ANIMATE_TRANSITIONS = True
```

## 🚀 Rollout Sugerido

### Fase 1: Backend (0.5 dia)
- [ ] Modificar `query_stream()` para yield todos os stages
- [ ] Testar via curl que todos eventos são enviados

### Fase 2: Frontend API (0.5 dia)
- [ ] Modificar `stream_api_response()` para parsear status
- [ ] Modificar signature para retornar tripla (chunk, sources, status)
- [ ] Testar parsing

### Fase 3: Frontend UI (2 dias)
- [ ] Adicionar progress bar e status display
- [ ] Implementar CSS styling
- [ ] Testar todas as animações
- [ ] Ajustar responsividade

### Fase 4: Polish (1 dia)
- [ ] Adicionar ícones por stage
- [ ] Melhorar animações
- [ ] Testar UX completa
- [ ] Documentação

## 🔄 Alternativas Consideradas

### Alternativa 1: Apenas Console Logs
**Prós**: Sem mudança de código
**Contras**: Usuário não vê nada
**Decisão**: ❌ Rejeitada - não atende requisito

### Alternativa 2: Polling de Status
**Prós**: Simples de implementar
**Contras**: Latência, menos eficiente que streaming
**Decisão**: ❌ Rejeitada - já temos streaming

### Alternativa 3: WebSocket
**Prós**: Bi-direcional, mais moderno
**Contras**: Mais complexo, Streamlit já usa SSE
**Decisão**: ❌ Rejeitada - over-engineering

### Alternativa 4: Completar Implementação SSE Existente (Escolhida)
**Prós**: Usa infraestrutura existente, eficiente
**Contras**: Nenhum significativo
**Decisão**: ✅ Adotada

## 🔮 Evoluções Futuras (v2.0)

1. **Estimativa de Tempo**: "~5s restantes"
2. **Sub-stages**: Breakdown detalhado de cada stage
3. **Livros Sendo Consultados**: Mostrar quais livros durante busca
4. **Animações Avançadas**: Transições mais suaves
5. **Dark/Light Mode**: Temas customizáveis
6. **Progress History**: Mostrar quanto tempo cada stage levou

## 📚 Referências

- [Streamlit Progress Bar](https://docs.streamlit.io/library/api-reference/status/st.progress)
- [Server-Sent Events (SSE)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Perplexity AI UX](https://www.perplexity.ai/)

---

**Data de Criação**: 2025-02-01
**Autor**: Sistema de Análise
**Revisão**: Pendente
**Status**: 📝 Proposta Inicial
