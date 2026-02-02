# Proposta 004: Feedback no Banco de Dados, Redesign Visual e Auto-Save

**Status**: 📝 PROPOSTA
**Prioridade**: 🔶 ALTA
**Impacto**: Alto - UX, qualidade de dados, simplificação de fluxo

---

## 📋 Resumo

Esta proposta cobre três mudanças inter-relacionadas:

1. **Sistema de Feedback no SQLite** — Migrar avaliações de JSONL para banco de dados, coletar informações do usuário, criar endpoint administrativo para consulta
2. **Redesign Visual Completo** — Corrigir cores sólidas/planas, adicionar padrões de fundo, cores mais vivas, corrigir tema claro sem contraste
3. **Auto-Save e Remoção do Botão Salvar** — Salvar automaticamente para usuários logados, remover botão manual, sessão-only para anônimos

---

## Parte 1: Sistema de Feedback no Banco de Dados

### ❌ Situação Atual

O feedback é salvo em arquivos JSONL (`frontend/feedback/responses_feedback.jsonl` e `backend/feedback/responses_feedback.jsonl`):

```json
{
  "timestamp": "2025-02-01T14:35:10",
  "user": "Anônimo",
  "question": "O que é reencarnação?",
  "answer": "A reencarnação é...",
  "keywords": [],
  "sources": ["truncado..."],
  "rating": "good",
  "comment": "Resposta clara"
}
```

**Problemas:**
- Dados soltos em arquivos JSONL sem estrutura relacional
- Sem ligação com o sistema de autenticação (campo `user` é texto livre)
- Sem painel para visualizar e analisar feedback
- Impossível filtrar, ordenar ou buscar avaliações de forma eficiente
- Para anônimos, nenhuma identificação é coletada
- Dados não podem ser usados facilmente para melhorar prompts

### ✅ Solução Proposta

#### Nova Tabela no SQLite (`backend/database.py`)

```sql
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,                          -- NULL para anônimos
    anonymous_name TEXT DEFAULT 'Anônimo',     -- Nome opcional para anônimos
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources_json TEXT,                          -- Fontes usadas (JSON)
    rating TEXT NOT NULL CHECK(rating IN ('good', 'neutral', 'bad')),
    comment TEXT,
    conversation_id INTEGER,                   -- Referência à conversa
    message_index INTEGER,                     -- Índice da mensagem na conversa
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_feedback_rating ON feedback(rating);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback(created_at);
```

#### Novas Funções CRUD (`backend/database.py`)

```python
def save_feedback(user_id, anonymous_name, question, answer, sources_json,
                  rating, comment, conversation_id=None, message_index=None) -> int

def get_feedback(limit=50, offset=0, rating_filter=None) -> List[Dict]

def get_feedback_stats() -> Dict
# Retorna: {total, good, neutral, bad, by_month: [{month, count, good, bad}]}

def get_top_rated_feedback(limit=10) -> List[Dict]
# Retorna os feedbacks com rating='good' mais recentes para uso como exemplos
```

#### Endpoint Administrativo (`backend/api_server.py`)

```python
# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@app.get("/admin/feedback")
async def admin_feedback(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    rating: Optional[str] = None
):
    """
    Painel administrativo de feedback.
    Retorna feedbacks paginados com filtros.
    Requer autenticação.
    """
    user = auth.get_optional_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado.")

    feedbacks = database.get_feedback(limit, offset, rating)
    stats = database.get_feedback_stats()
    top_rated = database.get_top_rated_feedback(10)

    return {
        "feedbacks": feedbacks,
        "stats": stats,
        "top_rated": top_rated,
        "pagination": {"limit": limit, "offset": offset}
    }

@app.get("/admin/feedback/export")
async def admin_feedback_export(request: Request):
    """Exportar todos os feedbacks como JSON para análise offline."""
    user = auth.get_optional_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado.")

    all_feedback = database.get_feedback(limit=10000)
    return {"feedbacks": all_feedback, "total": len(all_feedback)}
```

#### Coleta de Nome para Anônimos (`frontend/app.py`)

Na seção de feedback de cada mensagem, adicionar campo de nome opcional para usuários não logados:

```python
# Dentro da seção de feedback, antes do botão "Enviar"
if not is_logged_in():
    anonymous_name = st.text_input(
        "Seu nome (opcional):",
        value="",
        placeholder="Como podemos te chamar?",
        key=f"anon_name_{idx}"
    )
else:
    anonymous_name = None  # Usa dados da conta

# No submit:
if st.button("✅ Enviar Feedback", key=f"submit_{idx}"):
    requests.post(
        f"{API_URL}/feedback",
        headers=_auth_headers(),
        json={
            "question": question,
            "answer": message["content"],
            "sources": [...],
            "rating": rating,
            "comment": comment,
            "anonymous_name": anonymous_name or "Anônimo"
        }
    )
```

#### Novo Endpoint de Feedback (`backend/api_server.py`)

```python
class FeedbackRequest(BaseModel):
    question: str
    answer: str
    sources: Optional[List] = None
    rating: str  # "good", "neutral", "bad"
    comment: Optional[str] = None
    anonymous_name: str = "Anônimo"
    conversation_id: Optional[str] = None
    message_index: Optional[int] = None

@app.post("/feedback")
async def submit_feedback(request: Request, body: FeedbackRequest):
    """Salvar feedback no banco de dados."""
    user = auth.get_optional_user(request)
    user_id = user["id"] if user else None

    sources_json = json.dumps(body.sources, ensure_ascii=False) if body.sources else None

    feedback_id = database.save_feedback(
        user_id=user_id,
        anonymous_name=body.anonymous_name if not user else user.get("display_name"),
        question=body.question,
        answer=body.answer,
        sources_json=sources_json,
        rating=body.rating,
        comment=body.comment
    )

    return {"success": True, "feedback_id": feedback_id}
```

### Uso Futuro: Exemplos para Melhoria de Prompts

O endpoint `GET /admin/feedback` retorna `top_rated` — os melhores feedbacks avaliados como "good". Um administrador pode:

1. Acessar `http://localhost:8000/admin/feedback`
2. Ver os top 10 pares pergunta/resposta mais bem avaliados
3. Copiar exemplos relevantes e adicioná-los ao prompt template em `api_server.py` como few-shot examples
4. Exportar via `/admin/feedback/export` para análise offline em planilha ou notebook

---

## Parte 2: Redesign Visual Completo

### ❌ Problemas Atuais

1. **Cores muito sólidas/planas** — Fundos `#1a1a1a` (dark) e `#FFFFF0` (light) são blocos de cor sem textura
2. **Tema claro sem contraste** — Tudo parece branco/creme, elementos não se destacam, fontes e cards se misturam com o fundo
3. **Falta de padrão visual** — Sem texturas ou padrões que dêem profundidade
4. **Elementos indistintos** — Badges, cards, botões parecem todos iguais no tema claro
5. **Sidebar monótona** — Bloco sólido de cor sem interesse visual

### ✅ Solução Proposta

#### Conceito: "Livro Antigo com Energia Moderna"

Combinar a sobriedade de um livro espírita com a energia visual de cores vivas e padrões sutis.

#### 1. Padrões de Fundo (Background Patterns)

**Dark Theme — Padrão geométrico sutil:**
```css
.stApp {
    background-color: #121212 !important;
    background-image:
        radial-gradient(circle at 25% 25%, rgba(255, 215, 0, 0.03) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(255, 193, 7, 0.03) 0%, transparent 50%),
        linear-gradient(rgba(255, 215, 0, 0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 215, 0, 0.02) 1px, transparent 1px) !important;
    background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px !important;
}
```

**Light Theme — Padrão pontilhado com contraste:**
```css
.stApp {
    background-color: #F5F0E8 !important;  /* Bege mais quente, NÃO branco */
    background-image:
        radial-gradient(circle, rgba(0, 0, 0, 0.06) 1px, transparent 1px),
        radial-gradient(circle at 50% 50%, rgba(249, 168, 37, 0.05) 0%, transparent 70%) !important;
    background-size: 20px 20px, 100% 100% !important;
}
```

#### 2. Paleta de Cores Revisada

**Dark Theme — Mais vivo:**

| Elemento | Antes | Depois |
|----------|-------|--------|
| Fundo principal | `#1a1a1a` (preto puro) | `#121212` + padrão dourado |
| Fundo sidebar | `#0d0d0d` | `#0a0a0a` + gradiente sutil dourado |
| Msg usuário | `#FFD700→#FFA000` | `#FFD700→#FF8F00` (mais saturado) |
| Msg assistente | `#2d2d2d→#3a3a3a` | `#1E1E2E→#2A2A3E` (tom azulado escuro) |
| Cards fonte | `rgba(255,215,0,0.05)` | `rgba(255,215,0,0.08)` + sombra |
| Badges | Gradientes suaves | Gradientes mais vibrantes + sombra |
| Botões | Sem destaque | Borda dourada + hover glow |

**Light Theme — Com contraste real:**

| Elemento | Antes | Depois |
|----------|-------|--------|
| Fundo principal | `#FFFFF0` (quase branco) | `#F5F0E8` (bege quente) + padrão pontilhado |
| Fundo sidebar | `#FFFDE7` (creme claro) | `#EDE7D9` (bege mais escuro) |
| Msg usuário | `#FFD700→#FFCA28` (amarelo claro) | `#F9A825→#FF8F00` (âmbar forte) |
| Msg assistente | `#FAFAFA→#F5F5F5` (quase branco) | `#FFFFFF` + borda `#E0D5C5` + sombra |
| Cards fonte | `rgba(0,0,0,0.03)` (invisível) | `#FFFFFF` + borda `#D4C4A8` + sombra |
| Badges | Gradientes fracos | Cores sólidas vibrantes + borda |
| Botões | Sem destaque | Fundo `#F9A825` + texto escuro |
| Texto | `#212121` | `#2C1810` (marrom escuro, mais legível) |

#### 3. Sombras e Profundidade

Adicionar sombras para criar camadas visuais:

```css
/* Cards de fonte - Dark */
.source-card {
    box-shadow: 0 2px 8px rgba(255, 215, 0, 0.1),
                inset 0 1px 0 rgba(255, 215, 0, 0.05);
}

/* Cards de fonte - Light */
.source-card {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08),
                0 1px 2px rgba(0, 0, 0, 0.04);
    border: 1px solid #E0D5C5;
}

/* Mensagens do assistente - Light */
.stChatMessage[data-testid="assistant-message"] {
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
    border: 1px solid #E0D5C5 !important;
}
```

#### 4. Sidebar com Gradiente

```css
/* Dark */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0a0a 0%, #121212 50%, #0a0a0a 100%) !important;
    border-right: 1px solid rgba(255, 215, 0, 0.1);
}

/* Light */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #EDE7D9 0%, #F5F0E8 50%, #EDE7D9 100%) !important;
    border-right: 1px solid #D4C4A8;
}
```

#### 5. Botões com Destaque

```css
/* Dark */
.stButton button {
    border: 1px solid rgba(255, 215, 0, 0.3) !important;
    transition: all 0.3s ease !important;
}

.stButton button:hover {
    border-color: #FFD700 !important;
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.2) !important;
}

/* Light */
.stButton button {
    border: 1px solid #D4C4A8 !important;
    background: #FFFFFF !important;
}

.stButton button:hover {
    border-color: #F9A825 !important;
    box-shadow: 0 2px 8px rgba(249, 168, 37, 0.2) !important;
}
```

#### 6. Badges com Mais Vida

```css
/* Badges mais vibrantes - ambos temas */
.badge-max {
    background: #FFD700 !important;
    color: #1a1a1a !important;
    box-shadow: 0 1px 4px rgba(255, 215, 0, 0.3);
    font-weight: 700 !important;
}

.badge-high {
    background: #FF6D00 !important;
    color: white !important;
    box-shadow: 0 1px 4px rgba(255, 109, 0, 0.3);
}

.badge-medium {
    background: #00BFA5 !important;
    color: white !important;
    box-shadow: 0 1px 4px rgba(0, 191, 165, 0.3);
}
```

### Mockup Visual

**Dark Theme:**
```
┌─────────────────────────────────────────────────────────┐
│ ░░░ SIDEBAR (gradiente escuro + borda dourada) ░░░      │
│                                                          │
│  🌐 Backend Online ✅                                    │
│  ─────────────────                                       │
│  👤 Olá, João!                                           │
│  ─────────────────                                       │
│  ⚙️ Modelo: llama3.2:3b                                 │
│  ─────────────────                                       │
│  💬 Conversas                                            │
│  [🆕 Nova Conversa]  ← sem botão Salvar                 │
│  📜 Conversa 1...                                        │
│  📜 Conversa 2...                                        │
├─────────────────────────────────────────────────────────┤
│ ·  ·  ·  ·  ·  ·  ·  CHAT AREA  ·  ·  ·  ·  ·  ·  · │
│ (fundo #121212 com grid dourado sutil)                   │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ 🧑 Mensagem do usuário               │  ← amarelo    │
│  │    (gradiente dourado vibrante)       │     vibrante  │
│  └──────────────────────────────────────┘                │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ 🤖 Resposta do assistente            │  ← azul       │
│  │    (gradiente escuro azulado)         │     escuro    │
│  │    ┌────────────────────────┐        │                │
│  │    │ 📖 3 Fontes Consultadas │ ← card com sombra     │
│  │    │ 📜 Ver Citações         │ ← card com sombra     │
│  │    └────────────────────────┘        │                │
│  │    📝 Esta resposta foi útil?        │                │
│  │    [👍] [😐] [👎]   Nome: ____      │  ← nome       │
│  └──────────────────────────────────────┘     opcional   │
│                                                          │
│  [Digite sua pergunta...]  ═══ borda dourada ═══        │
└─────────────────────────────────────────────────────────┘
```

**Light Theme:**
```
┌─────────────────────────────────────────────────────────┐
│ ░ SIDEBAR (bege quente, borda castanha) ░                │
│                                                          │
│  (mesma estrutura, cores quentes com contraste)          │
├─────────────────────────────────────────────────────────┤
│ ·  ·  ·  ·  CHAT AREA (bege #F5F0E8 pontilhado) ·  · │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ 🧑 Mensagem (âmbar forte #F9A825)   │  ← NÃO       │
│  │    texto escuro marrom               │     amarelo   │
│  └──────────────────────────────────────┘     pálido    │
│                                                          │
│  ┌──────────────────────────────────────┐                │
│  │ 🤖 Resposta (branco + borda bege    │  ← com        │
│  │    + sombra sutil)                    │     CONTRASTE │
│  │    texto marrom escuro #2C1810       │                │
│  └──────────────────────────────────────┘                │
│                                                          │
│  [Digite sua pergunta...]  ═ borda âmbar ═              │
└─────────────────────────────────────────────────────────┘
```

---

## Parte 3: Auto-Save e Remoção do Botão Salvar

### ❌ Situação Atual

```python
# Sidebar tem 2 botões:
col_new, col_save = st.columns(2)
with col_new:
    if st.button("🆕 Nova", ...): ...
with col_save:
    if st.button("💾 Salvar", ...):     # ← REMOVER
        do_save_conversation()
        st.success("✅ Salva!")
```

Existem 4 pontos onde `do_save_conversation()` é chamado:
1. Botão "Nova Conversa" (antes de limpar)
2. Botão "Salvar" (manual) ← **REMOVER**
3. Auto-save após resposta streaming (linha 1267)
4. Auto-save após resposta não-streaming (linha 1302)

### ✅ Solução Proposta

#### Mudanças no `frontend/app.py`:

**1. Remover botão "Salvar":**
```python
# ANTES:
col_new, col_save = st.columns(2)
with col_new:
    if st.button("🆕 Nova", use_container_width=True): ...
with col_save:
    if st.button("💾 Salvar", ...): ...

# DEPOIS:
if st.button("🆕 Nova Conversa", use_container_width=True):
    if len(st.session_state.messages) > 0 and is_logged_in():
        do_save_conversation()
    st.session_state.messages = []
    st.session_state.current_chat_id = generate_chat_id()
    st.rerun()
```

**2. Auto-save condicional (só para logados):**
```python
# ANTES (linhas 1267 e 1302):
do_save_conversation()  # Salva sempre

# DEPOIS:
if is_logged_in():
    do_save_conversation()
# Anônimos: mensagens vivem apenas em st.session_state
```

**3. Remover save para anônimos da função do_save_conversation():**
```python
def do_save_conversation():
    """Salva conversa APENAS para usuários logados."""
    if not is_logged_in():
        return  # Anônimos não salvam nada

    title = "Conversa sem título"
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            title = msg["content"][:50]
            break
    backend_save_conversation(
        st.session_state.current_chat_id,
        st.session_state.messages,
        title
    )
```

**4. Sidebar de conversas para anônimos:**
```python
# Seção de conversas recentes:
if is_logged_in():
    recent_convs = do_get_recent_conversations(10)
    if recent_convs:
        # Mostrar lista...
    else:
        st.caption("Nenhuma conversa salva ainda.")
else:
    st.info("🔒 Faça login para salvar suas conversas entre sessões.")
```

---

## Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `backend/database.py` | Adicionar tabela `feedback` + funções CRUD |
| `backend/api_server.py` | Adicionar `POST /feedback`, `GET /admin/feedback`, `GET /admin/feedback/export` |
| `frontend/app.py` | CSS redesign completo (padrões, contraste, sombras), remover botão Salvar, feedback via API com campo nome |
| `frontend/feedback_system.py` | Deprecado — feedback agora vai para o banco via API |

## Arquivos NÃO Modificados (mas observados)

| Arquivo | Motivo |
|---------|--------|
| `backend/auth.py` | Não precisa de mudanças |
| `backend/config.py` | Não precisa de mudanças |
| `frontend/chat_history.py` | Pode ser simplificado futuramente (anônimos não salvam mais) |

---

## Verificação

1. **Feedback**: Enviar feedback como anônimo com nome opcional → verificar em `/admin/feedback`
2. **Feedback logado**: Enviar feedback logado → verificar que `user_id` está preenchido
3. **Admin**: Acessar `GET /admin/feedback` → ver stats, feedbacks, top_rated
4. **UI Dark**: Verificar padrão de fundo, sombras nos cards, cores vibrantes
5. **UI Light**: Verificar contraste real — fundo bege, cards brancos com borda, texto marrom
6. **Auto-save logado**: Fazer pergunta logado → fechar aba → reabrir → conversa persiste
7. **Anônimo sem save**: Fazer pergunta anônimo → refrescar página → conversa sumiu
8. **Sem botão Salvar**: Verificar que botão "💾 Salvar" não aparece mais

---

## Métricas de Sucesso

| KPI | Meta |
|-----|------|
| Feedbacks coletados/semana | >10 (com dados estruturados) |
| Contraste tema claro (WCAG) | AA ou superior |
| Tempo de save | 0ms para anônimos (sem I/O) |
| Satisfação visual | Feedback positivo de usuários |

---

**Data de Criação**: 2025-02-01
**Autor**: Sistema de Análise
**Status**: 📝 PROPOSTA — Aguardando Aprovação
