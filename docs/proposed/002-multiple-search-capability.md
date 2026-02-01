# Proposta 002: Capacidade de Múltiplas Buscas

**Status**: 🔴 NÃO IMPLEMENTADO
**Prioridade**: 🔥 CRÍTICA
**Esforço Estimado**: Médio-Alto (6-8 horas)
**Impacto**: Alto - Melhora significativa na qualidade das respostas

---

## 📋 Resumo

Implementar sistema de múltiplas buscas automáticas que identifica quando uma pergunta precisa de informações adicionais e realiza buscas complementares para fornecer respostas mais completas e precisas.

## 🎯 Objetivo Declarado (CLAUDE.md)

> "Múltiplas buscas automáticas quando necessário para respostas mais completas"

**Comportamento Esperado:**
```
Pergunta Simples: "O que é perispírito?"
→ 1 busca suficiente

Pergunta Complexa: "Qual a relação entre perispírito, reencarnação e evolução espiritual?"
→ 3 buscas:
   1. "perispírito função estrutura"
   2. "reencarnação processo"
   3. "evolução espiritual perispírito reencarnação"
→ Correlaciona informações de múltiplas fontes
→ Resposta mais completa e fundamentada
```

## ❌ Situação Atual

**Implementação**: Inexistente

**Comportamento Atual:**
- Apenas UMA busca por pergunta
- Usa query original sem expansão
- Não detecta necessidade de contexto adicional
- Não faz buscas complementares
- Pode perder informações relevantes em perguntas complexas

**Código Atual:**
```python
# backend/api_server.py (linha 435-440)
sources = prioritized_search(
    vectorstore,
    request.question,  # Query direta, sem expansão
    k=request.top_k,
    fetch_k=request.fetch_k
)
# UMA única busca, resultado final
```

**Problemas:**
1. Respostas incompletas para perguntas complexas
2. Perda de contexto relevante em tópicos inter-relacionados
3. Não aproveita múltiplas perspectivas das obras
4. Viola promessa de "múltiplas buscas automáticas"
5. Qualidade inferior comparada a sistemas como Perplexity

**Arquivos Afetados:**
- `backend/api_server.py` (linhas 435-440, 552-557): Chamada única de busca
- `backend/priority_retriever.py`: Apenas função de busca simples

## ✅ Solução Proposta

### Abordagem: Sistema Adaptativo Multi-Search

#### **Estratégia: 3 Níveis de Complexidade**

```
NÍVEL 1 - Pergunta Simples (1 busca)
├─ Pergunta direta sobre 1 conceito
├─ Ex: "O que é perispírito?"
└─ Estratégia: 1 busca com query original

NÍVEL 2 - Pergunta Média (2-3 buscas)
├─ Pergunta sobre relação entre 2-3 conceitos
├─ Ex: "Qual a relação entre perispírito e reencarnação?"
└─ Estratégia: 1 busca geral + 1-2 buscas específicas

NÍVEL 3 - Pergunta Complexa (3-5 buscas)
├─ Pergunta multi-facetada ou comparativa
├─ Ex: "Compare as visões sobre evolução espiritual
│      em O Livro dos Espíritos e O Evangelho"
└─ Estratégia: 1 busca geral + múltiplas específicas + síntese
```

### Implementação Detalhada

#### **Componente 1: Analisador de Complexidade**

```python
# backend/multi_search.py (NOVO ARQUIVO)

from typing import List, Dict, Tuple
import re
from langchain_community.llms import Ollama

class QueryAnalyzer:
    """Analisa complexidade de perguntas e extrai conceitos-chave"""

    # Palavras-chave que indicam comparação/relação
    COMPARATIVE_KEYWORDS = [
        "diferença", "comparar", "relação", "relaciona",
        "versus", "vs", "contraste", "semelhança",
        "conexão", "liga", "influência"
    ]

    # Palavras-chave que indicam múltiplos conceitos
    MULTI_CONCEPT_KEYWORDS = [
        "e", "ou", "além", "também", "junto",
        "combinado", "integrado"
    ]

    # Conectores que dividem perguntas complexas
    QUESTION_SPLITTERS = [
        "e como", "e por que", "e quando", "e qual",
        "além disso", "ademais", "também"
    ]

    def __init__(self):
        pass

    def analyze_complexity(self, question: str) -> Dict:
        """
        Analisa complexidade da pergunta

        Returns:
            {
                'complexity_level': int (1-3),
                'num_concepts': int,
                'concepts': List[str],
                'is_comparative': bool,
                'sub_questions': List[str],
                'recommended_searches': int
            }
        """

        # Normalizar pergunta
        q_lower = question.lower()

        # Detectar comparação
        is_comparative = any(
            keyword in q_lower
            for keyword in self.COMPARATIVE_KEYWORDS
        )

        # Extrair conceitos espíritas principais
        concepts = self._extract_concepts(question)
        num_concepts = len(concepts)

        # Detectar sub-perguntas
        sub_questions = self._split_complex_question(question)

        # Determinar nível de complexidade
        complexity_level = self._determine_complexity_level(
            num_concepts,
            is_comparative,
            len(sub_questions),
            question
        )

        # Recomendar número de buscas
        recommended_searches = self._recommend_num_searches(
            complexity_level,
            num_concepts,
            is_comparative
        )

        return {
            'complexity_level': complexity_level,
            'num_concepts': num_concepts,
            'concepts': concepts,
            'is_comparative': is_comparative,
            'sub_questions': sub_questions,
            'recommended_searches': recommended_searches
        }

    def _extract_concepts(self, question: str) -> List[str]:
        """Extrai conceitos espíritas da pergunta"""

        # Lista de conceitos espíritas comuns
        SPIRITIST_CONCEPTS = [
            "perispírito", "reencarnação", "mediunidade", "médium",
            "espírito", "desencarnação", "obsessão", "caridade",
            "evangelho", "prece", "fluido", "passe", "evolução",
            "karma", "lei de causa e efeito", "livre arbítrio",
            "destino", "plano espiritual", "erraticidade",
            "expiação", "provação", "missão", "intuição"
        ]

        q_lower = question.lower()
        found_concepts = []

        for concept in SPIRITIST_CONCEPTS:
            if concept in q_lower:
                found_concepts.append(concept)

        # Se não encontrou conceitos específicos, tentar extrair substantivos
        if not found_concepts:
            # Extrair palavras principais (heurística simples)
            words = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', q_lower)
            # Pegar até 3 palavras mais longas como conceitos
            found_concepts = sorted(set(words), key=len, reverse=True)[:3]

        return found_concepts

    def _split_complex_question(self, question: str) -> List[str]:
        """Divide pergunta complexa em sub-perguntas"""

        sub_questions = []

        # Dividir por conectores
        for splitter in self.QUESTION_SPLITTERS:
            if splitter in question.lower():
                parts = re.split(
                    re.escape(splitter),
                    question,
                    flags=re.IGNORECASE
                )
                sub_questions.extend([p.strip() for p in parts if p.strip()])

        # Se não dividiu, retornar pergunta original
        if not sub_questions:
            sub_questions = [question]

        return sub_questions

    def _determine_complexity_level(
        self,
        num_concepts: int,
        is_comparative: bool,
        num_sub_questions: int,
        question: str
    ) -> int:
        """
        Determina nível de complexidade (1, 2 ou 3)

        Critérios:
        - NÍVEL 1: Pergunta simples, 1 conceito, direta
        - NÍVEL 2: 2-3 conceitos OU comparativa OU 2 sub-perguntas
        - NÍVEL 3: 4+ conceitos OU 3+ sub-perguntas OU muito complexa
        """

        # Complexidade baseada em múltiplos fatores
        complexity_score = 0

        # Fator 1: Número de conceitos
        if num_concepts == 1:
            complexity_score += 1
        elif num_concepts <= 3:
            complexity_score += 2
        else:
            complexity_score += 3

        # Fator 2: Comparação
        if is_comparative:
            complexity_score += 1

        # Fator 3: Sub-perguntas
        if num_sub_questions > 2:
            complexity_score += 1

        # Fator 4: Comprimento da pergunta (proxy de complexidade)
        if len(question) > 100:
            complexity_score += 1

        # Mapear score para nível
        if complexity_score <= 2:
            return 1  # Simples
        elif complexity_score <= 4:
            return 2  # Média
        else:
            return 3  # Complexa

    def _recommend_num_searches(
        self,
        complexity_level: int,
        num_concepts: int,
        is_comparative: bool
    ) -> int:
        """Recomenda número de buscas baseado na complexidade"""

        if complexity_level == 1:
            return 1

        elif complexity_level == 2:
            if is_comparative:
                return 3  # 1 para cada lado + 1 geral
            else:
                return min(num_concepts + 1, 3)

        else:  # complexity_level == 3
            if is_comparative:
                return min(num_concepts * 2, 5)
            else:
                return min(num_concepts + 2, 5)


class MultiSearchEngine:
    """Engine para realizar múltiplas buscas e combinar resultados"""

    def __init__(self, vectorstore, llm=None):
        self.vectorstore = vectorstore
        self.llm = llm
        self.analyzer = QueryAnalyzer()

    def multi_search(
        self,
        question: str,
        k: int = 3,
        fetch_k: int = 15,
        max_searches: int = 5
    ) -> Tuple[List, Dict]:
        """
        Realiza múltiplas buscas e combina resultados

        Returns:
            (combined_sources, metadata)
            - combined_sources: Lista de documentos únicos
            - metadata: Informações sobre as buscas realizadas
        """

        # Analisar complexidade
        analysis = self.analyzer.analyze_complexity(question)

        # Limitar número de buscas
        num_searches = min(
            analysis['recommended_searches'],
            max_searches
        )

        print(f"🔍 Análise: Nível {analysis['complexity_level']}, "
              f"{analysis['num_concepts']} conceitos, "
              f"{num_searches} buscas recomendadas")

        # Gerar queries para cada busca
        search_queries = self._generate_search_queries(
            question,
            analysis,
            num_searches
        )

        print(f"📝 Queries geradas:")
        for i, query in enumerate(search_queries, 1):
            print(f"   {i}. {query}")

        # Realizar buscas
        all_sources = []
        search_results = []

        for i, query in enumerate(search_queries):
            print(f"🔎 Busca {i+1}/{len(search_queries)}: {query[:50]}...")

            from priority_retriever import prioritized_search

            sources = prioritized_search(
                self.vectorstore,
                query,
                k=k,
                fetch_k=fetch_k
            )

            search_results.append({
                'query': query,
                'num_results': len(sources),
                'sources': sources
            })

            all_sources.extend(sources)

        # Remover duplicatas e reranquear
        unique_sources = self._deduplicate_and_rerank(
            all_sources,
            question,
            k=k * num_searches  # Mais resultados para perguntas complexas
        )

        print(f"✅ Total: {len(all_sources)} documentos, "
              f"{len(unique_sources)} únicos")

        metadata = {
            'complexity_analysis': analysis,
            'num_searches': num_searches,
            'search_queries': search_queries,
            'search_results': search_results,
            'total_documents': len(all_sources),
            'unique_documents': len(unique_sources)
        }

        return unique_sources, metadata

    def _generate_search_queries(
        self,
        question: str,
        analysis: Dict,
        num_searches: int
    ) -> List[str]:
        """Gera múltiplas queries de busca"""

        queries = []

        # Query 1: Sempre incluir pergunta original
        queries.append(question)

        if num_searches == 1:
            return queries

        # Query 2+: Baseado em conceitos e complexidade
        concepts = analysis['concepts']

        if analysis['is_comparative'] and len(concepts) >= 2:
            # Buscas separadas para cada lado da comparação
            for concept in concepts[:num_searches-1]:
                queries.append(f"{concept} definição características")

        elif len(concepts) > 1:
            # Buscas para cada conceito principal
            for concept in concepts[:num_searches-1]:
                queries.append(concept)

        else:
            # Expansões da query original
            expansions = [
                f"{question} explicação detalhada",
                f"{question} Allan Kardec codificação",
                f"{question} ensinamentos espíritas"
            ]
            queries.extend(expansions[:num_searches-1])

        # Garantir que temos exatamente num_searches queries
        return queries[:num_searches]

    def _deduplicate_and_rerank(
        self,
        sources: List,
        original_question: str,
        k: int
    ) -> List:
        """Remove duplicatas e reranqueia por relevância"""

        # Remover duplicatas baseado no conteúdo
        seen_contents = set()
        unique_sources = []

        for source in sources:
            # Usar primeiros 200 caracteres como identificador
            content_id = source.page_content[:200].strip()

            if content_id not in seen_contents:
                seen_contents.add(content_id)
                unique_sources.append(source)

        # Reranquear por prioridade + relevância
        # (priority_retriever.py já faz isso, mas reforçar)
        from priority_retriever import rerank_by_priority
        reranked = rerank_by_priority(unique_sources)

        # Retornar top-k
        return reranked[:k]
```

#### **Componente 2: Integração com API**

```python
# Modificar backend/api_server.py

# Linha ~16 (adicionar import)
from multi_search import MultiSearchEngine

# Linha ~143 (adicionar variável global)
multi_search_engine = None

# Linha ~253 (inicializar no startup)
@app.on_event("startup")
async def startup_event():
    global vectorstore, startup_time, multi_search_engine

    # ... código existente ...

    # NOVO: Inicializar multi-search engine
    print("🔍 Inicializando motor de múltiplas buscas...")
    multi_search_engine = MultiSearchEngine(vectorstore)
    print("✅ Motor de múltiplas buscas pronto!")

# Linha ~435 (substituir busca simples por multi-search)
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # ... validação existente ...

    # SUBSTITUIR:
    # sources = prioritized_search(...)

    # POR:
    # Multi-search adaptativo
    status_tracker.update_task(task_id, "multi_searching", 30)
    print(f"🔍 Iniciando multi-search adaptativo...")

    sources, search_metadata = multi_search_engine.multi_search(
        request.question,
        k=request.top_k,
        fetch_k=request.fetch_k,
        max_searches=5  # Limite máximo de buscas
    )

    print(f"✅ Multi-search completo: {search_metadata['num_searches']} buscas, "
          f"{search_metadata['unique_documents']} documentos únicos")

    # Adicionar metadata às fontes
    for source in sources:
        source.metadata['search_metadata'] = search_metadata

    # ... resto do código existente ...
```

### Fluxo de Múltiplas Buscas

```
┌──────────────────────┐
│   Pergunta do        │
│   Usuário            │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  1. ANÁLISE DE COMPLEXIDADE         │
│  - Extrair conceitos                │
│  - Detectar comparações             │
│  - Identificar sub-perguntas        │
│  - Determinar nível (1, 2 ou 3)     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  2. DECISÃO DE ESTRATÉGIA           │
│                                     │
│  Nível 1: 1 busca                   │
│  Nível 2: 2-3 buscas                │
│  Nível 3: 3-5 buscas                │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  3. GERAÇÃO DE QUERIES              │
│  - Query original                   │
│  - Queries por conceito             │
│  - Queries expandidas               │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  4. EXECUÇÃO DE BUSCAS              │
│  ┌─────────────────────────────┐   │
│  │ Busca 1: Query original     │   │
│  └──────────┬──────────────────┘   │
│  ┌──────────▼──────────────────┐   │
│  │ Busca 2: Conceito A         │   │
│  └──────────┬──────────────────┘   │
│  ┌──────────▼──────────────────┐   │
│  │ Busca 3: Conceito B         │   │
│  └──────────┬──────────────────┘   │
│             ...                     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  5. COMBINAÇÃO E DEDUPLICAÇÃO       │
│  - Remover documentos duplicados    │
│  - Reranquear por prioridade        │
│  - Selecionar top-K únicos          │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  6. GERAÇÃO DE RESPOSTA             │
│  - Contexto enriquecido             │
│  - Múltiplas perspectivas           │
│  - Resposta mais completa           │
└─────────────────────────────────────┘
```

## 🔧 Casos de Uso Detalhados

### Caso 1: Pergunta Simples
```
Entrada: "O que é perispírito?"

Análise:
- Complexidade: Nível 1
- Conceitos: ["perispírito"]
- Buscas recomendadas: 1

Execução:
- Busca 1: "O que é perispírito?"

Resultado: 3-5 documentos sobre perispírito
```

### Caso 2: Pergunta com Relação
```
Entrada: "Qual a relação entre perispírito e reencarnação?"

Análise:
- Complexidade: Nível 2
- Conceitos: ["perispírito", "reencarnação"]
- É comparativa: Sim
- Buscas recomendadas: 3

Execução:
- Busca 1: "Qual a relação entre perispírito e reencarnação?"
- Busca 2: "perispírito definição características"
- Busca 3: "reencarnação processo"

Resultado: 9-12 documentos cobrindo ambos conceitos e relações
```

### Caso 3: Pergunta Complexa Multi-Conceito
```
Entrada: "Como a mediunidade, o perispírito e a evolução espiritual
          se relacionam no processo de reencarnação?"

Análise:
- Complexidade: Nível 3
- Conceitos: ["mediunidade", "perispírito", "evolução", "reencarnação"]
- Buscas recomendadas: 5

Execução:
- Busca 1: "Como a mediunidade, o perispírito e a evolução espiritual..."
- Busca 2: "mediunidade"
- Busca 3: "perispírito"
- Busca 4: "evolução espiritual"
- Busca 5: "reencarnação processo"

Resultado: 15-20 documentos únicos cobrindo todos os aspectos
```

### Caso 4: Pergunta Comparativa entre Livros
```
Entrada: "Compare as visões sobre caridade em O Livro dos Espíritos
          e O Evangelho Segundo o Espiritismo"

Análise:
- Complexidade: Nível 3
- Conceitos: ["caridade", "livro dos espíritos", "evangelho"]
- É comparativa: Sim
- Buscas recomendadas: 4

Execução:
- Busca 1: "Compare as visões sobre caridade..."
- Busca 2: "caridade livro dos espíritos"
- Busca 3: "caridade evangelho segundo espiritismo"
- Busca 4: "caridade definição Allan Kardec"

Resultado: 12-15 documentos de ambas as obras sobre caridade
```

## 📊 Benefícios Esperados

### Qualidade das Respostas
1. **Maior Cobertura**: Perguntas complexas recebem informações de múltiplas fontes
2. **Mais Completas**: Respostas abordam diferentes ângulos do tema
3. **Melhor Correlação**: Informações complementares de diferentes obras
4. **Menos Lacunas**: Menor chance de perder informações relevantes

### Performance
1. **Adaptativo**: Perguntas simples não sofrem overhead desnecessário
2. **Otimizado**: Deduplicação evita redundância
3. **Balanceado**: Limite máximo de buscas previne lentidão excessiva

### Experiência do Usuário
1. **Transparência**: Usuário vê quantas buscas foram realizadas
2. **Confiança**: Respostas mais fundamentadas em múltiplas fontes
3. **Alinhado com Promessa**: Funcionalidade "estilo Perplexity" implementada

## 🎯 Métricas de Sucesso

### KPIs
1. **Melhoria na Completude**: % de respostas mais completas
   - Meta: +40% para perguntas complexas
2. **Satisfação do Usuário**: Feedback positivo
   - Meta: +25% de avaliações "Boa"
3. **Latência Aceitável**: Tempo de resposta
   - Meta: < 10s para 3 buscas, < 15s para 5 buscas
4. **Uso Adaptativo**: % de perguntas que realmente precisam múltiplas buscas
   - Esperado: 30-40% Nível 2-3, 60-70% Nível 1

### Testes de Validação
- [ ] 20 perguntas simples → Devem usar 1 busca
- [ ] 20 perguntas médias → Devem usar 2-3 buscas
- [ ] 20 perguntas complexas → Devem usar 3-5 buscas
- [ ] Comparar qualidade antes/depois (avaliação humana)
- [ ] Medir latência média por nível

## 📝 Documentação a Atualizar

### README.md
```markdown
## 🔍 Sistema de Múltiplas Buscas

O assistente realiza **múltiplas buscas automáticas** para perguntas complexas:

### Níveis de Busca
- **Simples**: 1 busca para perguntas diretas
- **Média**: 2-3 buscas para relações entre conceitos
- **Complexa**: 3-5 buscas para perguntas multi-facetadas

### Exemplo
"Qual a relação entre perispírito e reencarnação?"
→ 3 buscas automáticas:
  1. Query original
  2. Foco em perispírito
  3. Foco em reencarnação
→ Resposta mais completa com múltiplas perspectivas
```

## ⚙️ Configurações Ajustáveis

### Limites de Busca
```python
# config.py
MAX_SEARCHES = 5           # Máximo de buscas por pergunta
MIN_SEARCHES = 1           # Mínimo (sempre 1)
COMPLEXITY_THRESHOLD_L2 = 2  # Score para nível 2
COMPLEXITY_THRESHOLD_L3 = 4  # Score para nível 3
```

### Deduplicação
```python
# multi_search.py
DEDUP_CONTENT_LENGTH = 200  # Caracteres para comparar duplicatas
```

## 🚀 Rollout Sugerido

### Fase 1: Desenvolvimento (2-3 dias)
- [ ] Criar `multi_search.py`
- [ ] Implementar `QueryAnalyzer`
- [ ] Implementar `MultiSearchEngine`
- [ ] Escrever testes unitários

### Fase 2: Integração (1-2 dias)
- [ ] Modificar `api_server.py`
- [ ] Integrar multi-search nos endpoints
- [ ] Testar com perguntas reais

### Fase 3: Testes e Ajustes (2 dias)
- [ ] Teste A/B: busca simples vs múltipla
- [ ] Ajustar thresholds de complexidade
- [ ] Otimizar geração de queries
- [ ] Validar performance

### Fase 4: Deploy (1 dia)
- [ ] Documentação completa
- [ ] Deploy gradual (feature flag)
- [ ] Monitoramento de latência
- [ ] Coleta de feedback

## 🔄 Alternativas Consideradas

### Alternativa 1: Sempre Fazer Múltiplas Buscas
**Prós**: Mais simples de implementar
**Contras**: Lento para perguntas simples, desperdício de recursos
**Decisão**: ❌ Rejeitada - não eficiente

### Alternativa 2: LLM Decide Número de Buscas
**Prós**: Decisão "inteligente"
**Contras**: Adiciona latência, custo computacional alto
**Decisão**: ❌ Rejeitada - over-engineering

### Alternativa 3: Sistema Adaptativo Baseado em Regras (Escolhida)
**Prós**: Rápido, eficiente, previsível, ajustável
**Contras**: Requer calibração inicial
**Decisão**: ✅ Adotada

### Alternativa 4: Query Expansion com Embeddings
**Prós**: Automático, baseado em similaridade
**Contras**: Menos controle, pode gerar queries ruins
**Decisão**: 🤔 Considerar para v2.0

## 🔮 Evoluções Futuras (v2.0)

1. **Query Expansion com LLM**: Usar LLM para gerar queries melhores
2. **Aprendizado de Padrões**: Aprender quais perguntas se beneficiam de múltiplas buscas
3. **Busca Iterativa**: Fazer buscas adicionais baseadas em qualidade dos resultados
4. **Fusão Semântica**: Combinar resultados de forma mais inteligente
5. **Cache de Multi-Search**: Cachear análises de perguntas similares

## 📚 Referências

- [Query Expansion Techniques](https://en.wikipedia.org/wiki/Query_expansion)
- [Multi-Query Retrieval in RAG](https://python.langchain.com/docs/modules/data_connection/retrievers/MultiQueryRetriever)
- [LangChain EnsembleRetriever](https://python.langchain.com/docs/modules/data_connection/retrievers/ensemble)

---

**Data de Criação**: 2025-02-01
**Autor**: Sistema de Análise
**Revisão**: Pendente
**Status**: 📝 Proposta Inicial
