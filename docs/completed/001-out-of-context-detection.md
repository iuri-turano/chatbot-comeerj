# Proposta 001: Detecção de Perguntas Fora de Contexto

**Status**: ✅ IMPLEMENTADO
**Data de Implementação**: 2025-02-01
**Prioridade**: 🔥 CRÍTICA
**Esforço Real**: ~3 horas
**Impacto**: Alto - Funcionalidade central do produto

---

## 🎉 IMPLEMENTAÇÃO CONCLUÍDA

Esta funcionalidade foi totalmente implementada conforme especificado na proposta.

### Arquivos Criados/Modificados:
- ✅ `backend/context_validator.py` - Novo arquivo com classe ContextValidator
- ✅ `backend/config.py` - Adicionadas configurações de validação
- ✅ `backend/api_server.py` - Integrada validação nos endpoints /query e /query_stream
- ✅ `backend/test_context_validation.py` - Script de testes
- ✅ `backend/README_TESTING.md` - Documentação de testes

### Como Testar:
```bash
cd backend
source venv/bin/activate  # Mac/Linux
python test_context_validation.py
```

Ver `backend/README_TESTING.md` para instruções completas.

---

---

## 📋 Resumo

Implementar sistema de detecção e rejeição automática de perguntas que não estão relacionadas ao Espiritismo e Doutrina Espírita.

## 🎯 Objetivo Declarado (CLAUDE.md)

> "Identifica e recusa perguntas FORA DE CONTEXTO (não relacionadas ao Espiritismo)"

**Comportamento Esperado:**
```
Pergunta IN CONTEXT: "O que é reencarnação?"
→ Processa normalmente

Pergunta OUT OF CONTEXT: "Qual a receita de bolo?"
→ Responde: "Desculpe, só posso responder perguntas sobre Espiritismo
            e Doutrina Espírita. Por favor, faça uma pergunta relacionada
            às obras de Allan Kardec."
```

## ❌ Situação Atual

**Implementação**: Inexistente

**Comportamento Atual:**
- O sistema aceita QUALQUER pergunta
- Tenta responder usando os documentos disponíveis
- Não há validação de relevância
- Perguntas sobre culinária, esportes, política, etc. são processadas

**Problemas:**
1. Viola promessa central do produto (especialização em Espiritismo)
2. Respostas ruins para perguntas fora de contexto
3. Perda de credibilidade do sistema
4. Uso desnecessário de recursos computacionais
5. Experiência ruim do usuário

**Arquivos Afetados:**
- `backend/api_server.py` (linhas 366-384): Prompt sem instrução de recusa
- `backend/api_server.py` (linhas 403-520): Endpoint `/query` sem validação
- `backend/api_server.py` (linhas 526-623): Endpoint `/query_stream` sem validação
- `backend/priority_retriever.py`: Busca sem validação de contexto

## ✅ Solução Proposta

### Abordagem: Sistema de Validação em 3 Camadas

#### **Camada 1: Análise Semântica Rápida (Pré-filtro)**

**Objetivo**: Rejeitar rapidamente perguntas obviamente fora de contexto

**Método**: Comparar embedding da pergunta com embeddings de tópicos espíritas

**Implementação**:
```python
# backend/context_validator.py (NOVO ARQUIVO)

from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL
import numpy as np

class ContextValidator:
    """Valida se perguntas estão relacionadas ao Espiritismo"""

    # Tópicos centrais do Espiritismo
    SPIRITIST_TOPICS = [
        "reencarnação e vidas sucessivas",
        "mediunidade e comunicação com espíritos",
        "perispírito e corpo espiritual",
        "lei de causa e efeito karma",
        "evolução espiritual",
        "Allan Kardec e codificação espírita",
        "O Livro dos Espíritos",
        "prece e evangelho",
        "obsessão espiritual",
        "mundo espiritual e planos",
        "desencarnação e morte",
        "livre arbítrio e destino",
        "Deus e leis divinas",
        "caridade e amor ao próximo",
        "passes e fluidos",
        "trabalho espiritual",
        "doutrina espírita Kardecista"
    ]

    # Keywords de rejeição rápida
    OFF_TOPIC_KEYWORDS = [
        # Culinária
        "receita", "cozinha", "ingrediente", "bolo", "comida",
        # Esportes
        "futebol", "jogo", "time", "campeonato", "gol",
        # Política
        "eleição", "presidente", "deputado", "partido", "governo",
        # Tecnologia não relacionada
        "celular", "computador", "software", "app", "internet",
        # Entretenimento
        "filme", "série", "novela", "música", "cantor",
        # Outros
        "moda", "carro", "viagem", "hotel", "shopping"
    ]

    def __init__(self, embeddings):
        self.embeddings = embeddings

        # Pre-calcular embeddings dos tópicos (cache)
        print("🔍 Calculando embeddings dos tópicos espíritas...")
        self.topic_embeddings = self._compute_topic_embeddings()
        print(f"✅ {len(self.topic_embeddings)} tópicos indexados")

    def _compute_topic_embeddings(self):
        """Pré-computar embeddings dos tópicos espíritas"""
        return [
            self.embeddings.embed_query(topic)
            for topic in self.SPIRITIST_TOPICS
        ]

    def _quick_keyword_check(self, question: str) -> bool:
        """
        Verifica keywords de rejeição rápida
        Returns: True se deve rejeitar
        """
        question_lower = question.lower()

        for keyword in self.OFF_TOPIC_KEYWORDS:
            if keyword in question_lower:
                return True  # Rejeitar

        return False  # Passar para próxima camada

    def _semantic_similarity(self, question: str) -> float:
        """
        Calcula similaridade semântica com tópicos espíritas
        Returns: Score 0.0 a 1.0
        """
        # Embedding da pergunta
        question_embedding = self.embeddings.embed_query(question)

        # Calcular similaridade com cada tópico
        similarities = []
        for topic_embedding in self.topic_embeddings:
            similarity = np.dot(question_embedding, topic_embedding) / (
                np.linalg.norm(question_embedding) * np.linalg.norm(topic_embedding)
            )
            similarities.append(similarity)

        # Retornar maior similaridade
        return max(similarities)

    def validate_question(
        self,
        question: str,
        threshold: float = 0.35  # Threshold ajustável
    ) -> tuple[bool, float, str]:
        """
        Valida se pergunta está relacionada ao Espiritismo

        Returns:
            (is_valid, confidence_score, reason)
            - is_valid: True se pergunta é válida
            - confidence_score: 0.0 a 1.0
            - reason: Explicação da decisão
        """

        # Camada 1: Quick keyword check
        if self._quick_keyword_check(question):
            return (False, 0.0, "Keywords fora de contexto detectadas")

        # Camada 2: Semantic similarity
        similarity_score = self._semantic_similarity(question)

        if similarity_score >= threshold:
            return (
                True,
                similarity_score,
                f"Pergunta relacionada ao Espiritismo (score: {similarity_score:.2f})"
            )
        else:
            return (
                False,
                similarity_score,
                f"Pergunta não relacionada ao Espiritismo (score: {similarity_score:.2f}, mínimo: {threshold})"
            )


def create_context_validator(embeddings) -> ContextValidator:
    """Factory function para criar validador"""
    return ContextValidator(embeddings)
```

#### **Camada 2: Validação por Resultados de Busca**

**Objetivo**: Validar baseado na qualidade dos documentos retornados

**Método**: Se os melhores documentos têm score muito baixo, provavelmente está fora de contexto

**Implementação**:
```python
# Adicionar em priority_retriever.py

def validate_search_results(sources, min_score: float = 0.4) -> bool:
    """
    Valida se os resultados da busca são relevantes

    Returns:
        True se resultados são relevantes, False se muito fracos
    """
    if not sources:
        return False

    # Pegar score do melhor documento
    # ChromaDB retorna distances, converter para similarity
    best_doc = sources[0]

    # Se até o melhor documento tem score baixo,
    # provavelmente a pergunta está fora de contexto
    if hasattr(best_doc, 'metadata') and 'score' in best_doc.metadata:
        best_score = best_doc.metadata['score']
        return best_score >= min_score

    return True  # Se não tem score, assume válido
```

#### **Camada 3: Instrução de Prompt (Fallback)**

**Objetivo**: LLM identifica e recusa perguntas fora de contexto

**Implementação**:
```python
# Modificar em api_server.py (linhas 366-384)

template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

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

{conversation_context}

CONTEXTO DOS LIVROS ESPÍRITAS:
{context}

PERGUNTA DO CONSULENTE: {question}

RESPOSTA (em português correto, reflexiva, citando fontes):"""
```

### Fluxo de Validação Proposto

```
┌─────────────────────┐
│  Pergunta do        │
│  Usuário            │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ CAMADA 1: Quick Keyword Check       │
│ - Verifica keywords off-topic       │
│ - Muito rápido (~1ms)               │
└──────────┬──────────────────────────┘
           │
           ├─── ❌ Keywords off-topic → REJEITAR
           │
           ▼ ✅ Passou
┌─────────────────────────────────────┐
│ CAMADA 2: Semantic Similarity       │
│ - Compara com tópicos espíritas     │
│ - Rápido (~50ms)                    │
└──────────┬──────────────────────────┘
           │
           ├─── ❌ Score < 0.35 → REJEITAR
           │
           ▼ ✅ Score >= 0.35
┌─────────────────────────────────────┐
│ CAMADA 3: Busca no ChromaDB         │
│ - Busca documentos relevantes       │
│ - Valida score dos resultados       │
└──────────┬──────────────────────────┘
           │
           ├─── ❌ Resultados fracos → REJEITAR
           │
           ▼ ✅ Resultados bons
┌─────────────────────────────────────┐
│ CAMADA 4: LLM (Fallback)            │
│ - Prompt instrui recusar off-topic  │
│ - Última linha de defesa            │
└──────────┬──────────────────────────┘
           │
           ▼
    📝 Gerar Resposta
```

## 🔧 Implementação Detalhada

### 1. Criar Novo Arquivo

**Arquivo**: `backend/context_validator.py`

**Conteúdo**: Ver código acima (ContextValidator class)

### 2. Modificar api_server.py

#### 2.1 Adicionar Import
```python
# Linha ~26 (após outros imports)
from context_validator import ContextValidator
```

#### 2.2 Inicializar Validador no Startup
```python
# Linha ~210 (dentro de startup_event)

@app.on_event("startup")
async def startup_event():
    global vectorstore, startup_time, context_validator  # Adicionar context_validator

    # ... código existente ...

    # Após criar embeddings (linha ~239)
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device}
    )

    # NOVO: Criar validador de contexto
    print("🔍 Inicializando validador de contexto...")
    context_validator = ContextValidator(embeddings)
    print("✅ Validador de contexto pronto!")

    # ... resto do código ...
```

#### 2.3 Adicionar Validação no Endpoint /query
```python
# Linha ~403 (início do endpoint /query)

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process a question and return answer with sources"""

    if vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados não carregado."
        )

    # NOVO: Validar contexto da pergunta
    is_valid, confidence, reason = context_validator.validate_question(
        request.question,
        threshold=0.35
    )

    if not is_valid:
        # Pergunta fora de contexto - retornar resposta de recusa
        rejection_message = (
            "Desculpe, sou um assistente especializado em Espiritismo e "
            "Doutrina Espírita. Só posso responder perguntas relacionadas "
            "às obras de Allan Kardec e aos ensinamentos espíritas.\n\n"
            "Por favor, faça uma pergunta sobre Espiritismo, como:\n"
            "- O que é reencarnação?\n"
            "- Como funciona a mediunidade?\n"
            "- O que Allan Kardec diz sobre [tema espírita]?"
        )

        return QueryResponse(
            task_id="rejected",
            answer=rejection_message,
            sources=[],
            processing_time=0.0
        )

    # Continuar com processamento normal...
    task_id = status_tracker.start_request(request.question, mode="normal")
    # ... resto do código existente ...
```

#### 2.4 Adicionar Validação no Endpoint /query_stream
```python
# Linha ~526 (início do endpoint /query_stream)

@app.post("/query_stream")
async def query_stream(request: QueryRequest):
    """Process a question and stream the response"""

    if vectorstore is None:
        raise HTTPException(
            status_code=503,
            detail="Banco de dados não carregado."
        )

    # NOVO: Validar contexto da pergunta
    is_valid, confidence, reason = context_validator.validate_question(
        request.question,
        threshold=0.35
    )

    if not is_valid:
        # Retornar rejection via streaming
        async def generate_rejection():
            rejection_message = (
                "Desculpe, sou um assistente especializado em Espiritismo e "
                "Doutrina Espírita. Só posso responder perguntas relacionadas "
                "às obras de Allan Kardec e aos ensinamentos espíritas.\n\n"
                "Por favor, faça uma pergunta sobre Espiritismo."
            )

            yield f"data: {json.dumps({'type': 'task_id', 'task_id': 'rejected'})}\n\n"
            yield f"data: {json.dumps({'type': 'token', 'content': rejection_message})}\n\n"
            yield f"data: {json.dumps({'type': 'sources', 'sources': []})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(generate_rejection(), media_type="text/event-stream")

    # Continuar com processamento normal...
    task_id = status_tracker.start_request(request.question, mode="streaming")
    # ... resto do código existente ...
```

#### 2.5 Atualizar Prompt Template
```python
# Linha ~366 (substituir template existente)

template = """Você é um assistente especializado em Espiritismo e Doutrina Espírita.

REGRA FUNDAMENTAL - VALIDAÇÃO DE CONTEXTO:
- Você SOMENTE responde perguntas sobre Espiritismo, Doutrina Espírita e obras de Allan Kardec
- Se a pergunta NÃO for sobre estes temas, responda EXATAMENTE:
  "Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita.
   Só posso responder perguntas relacionadas às obras de Allan Kardec e aos
   ensinamentos espíritas. Por favor, faça uma pergunta sobre Espiritismo."

INSTRUÇÕES IMPORTANTES (apenas para perguntas VÁLIDAS sobre Espiritismo):
1. Responda SEMPRE em português brasileiro correto e fluente
2. DÊ PRIORIDADE às informações de "O Livro dos Espíritos" quando disponível
3. Depois, priorize as outras obras fundamentais
4. SEMPRE cite os livros de onde extraiu as informações
5. Faça correlações entre diferentes trechos quando relevante
6. Reflita sobre as implicações dos ensinamentos apresentados
7. Mantenha coerência com o contexto da conversa anterior

{conversation_context}

CONTEXTO DOS LIVROS ESPÍRITAS:
{context}

PERGUNTA DO CONSULENTE: {question}

RESPOSTA (em português correto, reflexiva, citando fontes):"""
```

### 3. Adicionar Configuração

#### 3.1 Adicionar em config.py
```python
# Linha ~58 (após BOOK_PRIORITIES)

# Context validation settings
CONTEXT_VALIDATION_THRESHOLD = 0.35  # Similaridade mínima (0.0 a 1.0)
MIN_SEARCH_SCORE = 0.4  # Score mínimo dos resultados de busca

# Mensagem de rejeição padrão
REJECTION_MESSAGE = """Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita.

Só posso responder perguntas relacionadas às obras de Allan Kardec e aos ensinamentos espíritas.

Por favor, faça uma pergunta sobre Espiritismo, como:
- O que é reencarnação?
- Como funciona a mediunidade?
- O que Allan Kardec diz sobre a vida após a morte?
- Qual o papel da caridade no Espiritismo?
"""
```

## 📊 Testes Propostos

### Casos de Teste

#### ✅ Perguntas VÁLIDAS (Devem Passar):
1. "O que é o perispírito?"
2. "Explique sobre reencarnação"
3. "O que Allan Kardec diz sobre mediunidade?"
4. "Qual a diferença entre médium e sensitivo?"
5. "Como funciona a comunicação com espíritos?"

#### ❌ Perguntas INVÁLIDAS (Devem Ser Rejeitadas):
1. "Qual a receita de bolo de chocolate?"
2. "Quem ganhou a Copa do Mundo?"
3. "Como consertar meu computador?"
4. "Qual o melhor time de futebol?"
5. "Recomende uma série de TV"

### Script de Teste

```python
# tests/test_context_validation.py

import sys
sys.path.append('../backend')

from context_validator import ContextValidator
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL

def test_context_validation():
    print("🧪 Testando Validação de Contexto\n")

    # Criar embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}
    )

    # Criar validador
    validator = ContextValidator(embeddings)

    # Perguntas válidas
    valid_questions = [
        "O que é o perispírito?",
        "Explique sobre reencarnação segundo Allan Kardec",
        "Como funciona a mediunidade?",
        "O que acontece após a morte segundo o Espiritismo?",
        "Qual o papel da caridade?"
    ]

    # Perguntas inválidas
    invalid_questions = [
        "Qual a receita de bolo de chocolate?",
        "Quem ganhou a Copa do Mundo 2022?",
        "Como consertar meu computador?",
        "Recomende uma série de TV",
        "Qual o melhor restaurante da cidade?"
    ]

    print("✅ PERGUNTAS VÁLIDAS:")
    for q in valid_questions:
        is_valid, score, reason = validator.validate_question(q)
        status = "✅ PASSOU" if is_valid else "❌ FALHOU"
        print(f"{status} [{score:.2f}] {q[:50]}")

    print("\n❌ PERGUNTAS INVÁLIDAS:")
    for q in invalid_questions:
        is_valid, score, reason = validator.validate_question(q)
        status = "✅ PASSOU" if not is_valid else "❌ FALHOU"
        print(f"{status} [{score:.2f}] {q[:50]}")

if __name__ == "__main__":
    test_context_validation()
```

## 🎯 Métricas de Sucesso

### KPIs
1. **Precisão**: % de perguntas inválidas corretamente rejeitadas
   - Meta: > 95%
2. **Recall**: % de perguntas válidas corretamente aceitas
   - Meta: > 98%
3. **Latência**: Tempo adicional para validação
   - Meta: < 100ms
4. **Falsos Positivos**: Perguntas válidas rejeitadas incorretamente
   - Meta: < 2%

### Testes de Validação
- [ ] 50 perguntas válidas sobre Espiritismo
- [ ] 50 perguntas inválidas diversas
- [ ] Medição de performance (latência)
- [ ] Testes de edge cases (perguntas ambíguas)

## 📝 Documentação a Atualizar

### Arquivos:
1. **README.md**: Adicionar seção sobre validação de contexto
2. **CLAUDE.md**: Marcar feature como ✅ implementada
3. **API Docs** (`/docs`): Documentar comportamento de rejeição

### Exemplo de Documentação:

```markdown
## 🔍 Validação de Contexto

O sistema valida automaticamente se perguntas estão relacionadas ao Espiritismo:

### Perguntas Aceitas
- Sobre Doutrina Espírita
- Obras de Allan Kardec
- Conceitos espíritas (reencarnação, mediunidade, etc.)

### Perguntas Rejeitadas
- Temas não relacionados ao Espiritismo
- Culinária, esportes, política, tecnologia, etc.

### Resposta de Rejeição
Quando uma pergunta fora de contexto é detectada, o sistema responde:
"Desculpe, sou um assistente especializado em Espiritismo..."
```

## ⚙️ Configurações Ajustáveis

### Threshold de Validação
```python
# config.py
CONTEXT_VALIDATION_THRESHOLD = 0.35  # Mais baixo = mais permissivo
                                      # Mais alto = mais restritivo
```

**Recomendações:**
- 0.25-0.30: Muito permissivo (aceita mais perguntas)
- 0.35-0.40: Balanceado (recomendado)
- 0.45-0.50: Restritivo (pode rejeitar perguntas válidas)

### Personalizar Tópicos
```python
# context_validator.py
SPIRITIST_TOPICS = [
    "seu novo tópico aqui",
    # ... outros tópicos
]
```

## 🚀 Rollout Sugerido

### Fase 1: Desenvolvimento (1-2 dias)
- [ ] Criar `context_validator.py`
- [ ] Implementar classe `ContextValidator`
- [ ] Escrever testes unitários

### Fase 2: Integração (1 dia)
- [ ] Modificar `api_server.py`
- [ ] Integrar validação nos endpoints
- [ ] Atualizar prompt template

### Fase 3: Testes (1 dia)
- [ ] Testes com 100 perguntas diversas
- [ ] Ajustar threshold baseado em resultados
- [ ] Validar performance

### Fase 4: Deploy (1 dia)
- [ ] Documentação
- [ ] Deploy em produção
- [ ] Monitoramento inicial

## 🔄 Alternativas Consideradas

### Alternativa 1: Apenas Prompt
**Prós**: Simples, sem código adicional
**Contras**: Não confiável, consome recursos, respostas inconsistentes
**Decisão**: ❌ Rejeitada - insuficiente

### Alternativa 2: Modelo Classificador Específico
**Prós**: Alta precisão
**Contras**: Complexo, requer treinamento, mais recursos
**Decisão**: ❌ Over-engineering para esta fase

### Alternativa 3: Sistema de 3 Camadas (Escolhida)
**Prós**: Balanceado, eficiente, ajustável
**Contras**: Requer alguma manutenção
**Decisão**: ✅ Adotada

## 📚 Referências

- [Similarity Search Best Practices](https://www.pinecone.io/learn/similarity-search/)
- [LangChain Retrieval QA](https://python.langchain.com/docs/use_cases/question_answering/)
- [ChromaDB Filtering](https://docs.trychroma.com/usage-guide#filtering-by-metadata)

---

**Data de Criação**: 2025-02-01
**Autor**: Sistema de Análise
**Revisão**: Pendente
**Status**: 📝 Proposta Inicial
