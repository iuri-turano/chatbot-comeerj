"""
Multi-Search Engine for Adaptive Query Processing

This module implements adaptive multi-search capability that analyzes question
complexity and performs 1-5 searches based on the detected complexity level.

Components:
- QueryAnalyzer: Analyzes question complexity and extracts concepts
- MultiSearchEngine: Orchestrates multiple searches and combines results

Author: Implementation based on proposal 002-multiple-search-capability
Date: 2025-02-01
"""

from typing import List, Dict, Tuple
import re
from langchain.schema import Document


class QueryAnalyzer:
    """
    Analyzes question complexity and extracts key spiritist concepts.

    Determines complexity level (1-3) based on multiple factors:
    - Number of spiritist concepts
    - Presence of comparative keywords
    - Number of sub-questions
    - Question length
    """

    # Keywords that indicate comparison/relationship questions
    COMPARATIVE_KEYWORDS = [
        "diferença", "diferenças", "diferenciar",
        "comparar", "comparação", "compare",
        "relação", "relacionar", "relaciona", "relacionam",
        "versus", "vs", "vs.",
        "contraste", "contrastar",
        "semelhança", "semelhanças", "similar",
        "conexão", "conectar", "liga", "ligação",
        "influência", "influenciar", "influencia",
        "como se relaciona", "qual a relação"
    ]

    # Multi-concept indicators
    MULTI_CONCEPT_KEYWORDS = [
        " e ", " ou ", " além ", " também ", " junto ",
        " combinado ", " integrado ", " ademais "
    ]

    # Question splitters for complex questions
    QUESTION_SPLITTERS = [
        "e como", "e por que", "e quando", "e qual",
        "além disso", "ademais", "também"
    ]

    # Core spiritist concepts (curated list)
    SPIRITIST_CONCEPTS = [
        "perispírito", "perispiritos",
        "reencarnação", "reencarnar",
        "mediunidade", "médium", "mediuns",
        "espírito", "espíritos", "desencarnado", "desencarnados",
        "desencarnação", "desencarnar",
        "obsessão", "obsessor", "obsessores",
        "caridade", "caridoso",
        "evangelho",
        "prece", "oração", "orações",
        "fluido", "fluidos", "fluídico",
        "passe", "passes",
        "evolução", "evoluir", "evolução espiritual",
        "karma", "lei de causa e efeito", "causa e efeito",
        "livre arbítrio", "livre-arbítrio",
        "destino",
        "plano espiritual", "mundo espiritual", "erraticidade",
        "expiação", "expiar",
        "provação", "provações",
        "missão", "missões",
        "intuição",
        "allan kardec", "kardec",
        "codificação", "doutrina espírita", "espiritismo",
        "livro dos espíritos", "evangelho segundo espiritismo",
        "livro dos médiuns", "gênese", "céu e inferno"
    ]

    def __init__(self):
        """Initialize the QueryAnalyzer"""
        pass

    def analyze_complexity(self, question: str) -> Dict:
        """
        Analyzes the complexity of a question.

        Args:
            question: The user's question

        Returns:
            Dictionary with:
            - complexity_level (int): 1, 2, or 3
            - num_concepts (int): Number of spiritist concepts found
            - concepts (List[str]): List of concepts extracted
            - is_comparative (bool): Whether question is comparative
            - sub_questions (List[str]): Sub-questions if complex
            - recommended_searches (int): Recommended number of searches (1-5)
        """

        # Normalize question
        q_lower = question.lower()

        # Detect if comparative
        is_comparative = any(
            keyword in q_lower
            for keyword in self.COMPARATIVE_KEYWORDS
        )

        # Extract spiritist concepts
        concepts = self._extract_concepts(question)
        num_concepts = len(concepts)

        # Detect sub-questions
        sub_questions = self._split_complex_question(question)

        # Determine complexity level
        complexity_level = self._determine_complexity_level(
            num_concepts,
            is_comparative,
            len(sub_questions),
            question
        )

        # Recommend number of searches
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
        """
        Extracts spiritist concepts from the question.

        Args:
            question: The user's question

        Returns:
            List of spiritist concepts found (or heuristic extraction if none)
        """

        q_lower = question.lower()

        # Remove accents for better matching
        q_normalized = q_lower.replace('í', 'i').replace('é', 'e').replace('ê', 'e').replace('ã', 'a').replace('ú', 'u')

        found_concepts = []

        # Check for each spiritist concept
        for concept in self.SPIRITIST_CONCEPTS:
            concept_normalized = concept.replace('í', 'i').replace('é', 'e').replace('ê', 'e').replace('ã', 'a').replace('ú', 'u')

            if concept_normalized in q_normalized:
                # Add original concept (not normalized) if not already present
                if concept not in found_concepts:
                    found_concepts.append(concept)

        # If no specific concepts found, use heuristic extraction
        if not found_concepts:
            # Extract words that are likely concepts (4+ characters, not common words)
            words = re.findall(r'\b[a-záàâãéèêíïóôõöúçñ]{4,}\b', q_lower)

            # Remove common Portuguese words
            common_words = [
                'qual', 'como', 'quando', 'onde', 'porque', 'para',
                'sobre', 'segundo', 'entre', 'existe', 'fazer',
                'significa', 'explique', 'entender', 'dizer'
            ]

            words = [w for w in words if w not in common_words]

            # Take up to 3 longest words as concepts
            found_concepts = sorted(set(words), key=len, reverse=True)[:3]

        # Remove duplicates while preserving order
        seen = set()
        unique_concepts = []
        for concept in found_concepts:
            if concept.lower() not in seen:
                seen.add(concept.lower())
                unique_concepts.append(concept)

        return unique_concepts

    def _split_complex_question(self, question: str) -> List[str]:
        """
        Splits a complex question into sub-questions.

        Args:
            question: The user's question

        Returns:
            List of sub-questions (or just the original if not split)
        """

        sub_questions = []

        # Try to split by connectors
        for splitter in self.QUESTION_SPLITTERS:
            if splitter in question.lower():
                parts = re.split(
                    re.escape(splitter),
                    question,
                    flags=re.IGNORECASE
                )
                sub_questions.extend([p.strip() for p in parts if p.strip()])
                break  # Use first matching splitter

        # If no split occurred, return original question
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
        Determines complexity level (1, 2, or 3) based on multiple factors.

        Scoring algorithm:
        - Concept count: 1=+1, 2-3=+2, 4+=+3
        - Comparative: +1
        - Sub-questions (3+): +1
        - Length (>100 chars): +1

        Mapping:
        - Score ≤ 2: Level 1 (Simple)
        - Score 3-4: Level 2 (Medium)
        - Score ≥ 5: Level 3 (Complex)

        Args:
            num_concepts: Number of concepts found
            is_comparative: Whether question is comparative
            num_sub_questions: Number of sub-questions
            question: Original question text

        Returns:
            Complexity level (1, 2, or 3)
        """

        complexity_score = 0

        # Factor 1: Number of concepts
        if num_concepts == 1:
            complexity_score += 1
        elif num_concepts <= 3:
            complexity_score += 2
        else:  # 4+
            complexity_score += 3

        # Factor 2: Comparative question
        if is_comparative:
            complexity_score += 1

        # Factor 3: Multiple sub-questions
        if num_sub_questions > 2:
            complexity_score += 1

        # Factor 4: Long question (proxy for complexity)
        if len(question) > 100:
            complexity_score += 1

        # Map score to level
        if complexity_score <= 2:
            return 1  # Simple
        elif complexity_score <= 4:
            return 2  # Medium
        else:
            return 3  # Complex

    def _recommend_num_searches(
        self,
        complexity_level: int,
        num_concepts: int,
        is_comparative: bool
    ) -> int:
        """
        Recommends number of searches based on complexity.

        Args:
            complexity_level: 1, 2, or 3
            num_concepts: Number of concepts
            is_comparative: Whether comparative

        Returns:
            Number of searches (1-5)
        """

        if complexity_level == 1:
            return 1

        elif complexity_level == 2:
            if is_comparative:
                return 3  # Original + 1 for each side of comparison
            else:
                return min(num_concepts + 1, 3)

        else:  # complexity_level == 3
            if is_comparative:
                return min(num_concepts * 2, 5)
            else:
                return min(num_concepts + 2, 5)


class MultiSearchEngine:
    """
    Engine for executing multiple adaptive searches and combining results.

    Orchestrates:
    1. Complexity analysis
    2. Query generation
    3. Multiple searches
    4. Deduplication and reranking
    """

    def __init__(self, vectorstore, llm=None):
        """
        Initialize the MultiSearchEngine.

        Args:
            vectorstore: ChromaDB vectorstore instance
            llm: Optional LLM instance (for future query expansion)
        """
        self.vectorstore = vectorstore
        self.llm = llm
        self.analyzer = QueryAnalyzer()

    def multi_search(
        self,
        question: str,
        k: int = 3,
        fetch_k: int = 15,
        max_searches: int = 5
    ) -> Tuple[List[Document], Dict]:
        """
        Performs multiple adaptive searches and combines results.

        Args:
            question: User's question
            k: Number of final documents to return
            fetch_k: Number of documents to fetch per search
            max_searches: Maximum number of searches to perform

        Returns:
            Tuple of (combined_sources, metadata):
            - combined_sources: List of unique, reranked documents
            - metadata: Information about searches performed
        """

        # Step 1: Analyze complexity
        analysis = self.analyzer.analyze_complexity(question)

        # Limit number of searches
        num_searches = min(
            analysis['recommended_searches'],
            max_searches
        )

        print(f"🔍 Análise: Nível {analysis['complexity_level']}, "
              f"{analysis['num_concepts']} conceitos, "
              f"{num_searches} buscas recomendadas")

        # Step 2: Generate search queries
        search_queries = self._generate_search_queries(
            question,
            analysis,
            num_searches
        )

        print(f"📝 Queries geradas:")
        for i, query in enumerate(search_queries, 1):
            print(f"   {i}. {query}")

        # Step 3: Execute searches
        all_sources = []
        search_results = []

        for i, query in enumerate(search_queries):
            print(f"🔎 Busca {i+1}/{len(search_queries)}: {query[:50]}...")

            # Import here to avoid circular dependency
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

        # Step 4: Deduplicate and rerank
        result_multiplier = {
            1: 1,    # Simple: return k documents
            2: 2,    # Medium: return k*2 documents
            3: num_searches  # Complex: return k*num_searches documents
        }

        target_k = k * result_multiplier.get(analysis['complexity_level'], 1)

        unique_sources = self._deduplicate_and_rerank(
            all_sources,
            question,
            k=target_k
        )

        print(f"✅ Total: {len(all_sources)} documentos, "
              f"{len(unique_sources)} únicos")

        # Step 5: Build metadata
        metadata = {
            'complexity_analysis': analysis,
            'num_searches': num_searches,
            'search_queries': search_queries,
            'search_results': search_results,
            'total_documents': len(all_sources),
            'unique_documents': len(unique_sources),
            'deduplication_ratio': len(unique_sources) / len(all_sources) if all_sources else 0
        }

        return unique_sources, metadata

    def _generate_search_queries(
        self,
        question: str,
        analysis: Dict,
        num_searches: int
    ) -> List[str]:
        """
        Generates multiple search queries based on complexity analysis.

        Strategy:
        - Level 1: [original]
        - Level 2 comparative: [original, concept_A defin., concept_B defin.]
        - Level 2 non-comparative: [original, concept_A, concept_B]
        - Level 3: [original, concepts..., expanded queries]

        Args:
            question: Original question
            analysis: Complexity analysis result
            num_searches: Number of queries to generate

        Returns:
            List of search query strings
        """

        queries = []
        concepts = analysis['concepts']
        is_comparative = analysis['is_comparative']

        # Query 1: Always include original question
        queries.append(question)

        if num_searches == 1:
            return queries

        # Generate additional queries based on strategy
        if is_comparative and len(concepts) >= 2:
            # Comparative questions: search each concept with "definição características"
            for concept in concepts[:num_searches - 1]:
                queries.append(f"{concept} definição características")

        elif len(concepts) > 1:
            # Multi-concept non-comparative: search each concept individually
            for concept in concepts[:num_searches - 1]:
                queries.append(concept)

        else:
            # Single concept or no concepts: expand the query
            expansions = [
                f"{question} explicação detalhada",
                f"{question} Allan Kardec codificação",
                f"{question} ensinamentos espíritas"
            ]
            queries.extend(expansions[:num_searches - 1])

        # Ensure we have exactly num_searches queries
        return queries[:num_searches]

    def _deduplicate_and_rerank(
        self,
        sources: List[Document],
        original_question: str,
        k: int
    ) -> List[Document]:
        """
        Removes duplicate documents and reranks by priority.

        Uses 200-character fingerprint for deduplication, then applies
        existing priority-based reranking.

        Args:
            sources: List of documents from all searches
            original_question: Original user question
            k: Number of documents to return

        Returns:
            List of unique, reranked documents
        """

        # Step 1: Remove duplicates based on content fingerprint
        seen_fingerprints = set()
        unique_sources = []

        for source in sources:
            # Use first 200 characters as fingerprint
            content = source.page_content.strip()

            if len(content) > 200:
                fingerprint = content[:200]
            else:
                fingerprint = content

            # Normalize fingerprint (remove extra spaces, lowercase)
            fingerprint = " ".join(fingerprint.split()).lower()

            if fingerprint not in seen_fingerprints:
                seen_fingerprints.add(fingerprint)
                unique_sources.append(source)

        # Step 2: Rerank by priority using existing function
        from priority_retriever import rerank_by_priority

        reranked = rerank_by_priority(unique_sources, top_k=k)

        # Return top k
        return reranked[:k]
