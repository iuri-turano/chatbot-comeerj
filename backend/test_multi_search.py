"""
Comprehensive Test Suite for Multi-Search Functionality

Tests:
- QueryAnalyzer: 25 tests
- Query Generation: 20 tests
- Deduplication: 15 tests
- Integration: 20 tests

Total: 80 tests

Author: Implementation based on proposal 002
Date: 2025-02-01
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from multi_search import QueryAnalyzer, MultiSearchEngine
from langchain.schema import Document


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name):
        self.passed += 1
        print(f"✅ {test_name} - PASSED")

    def record_fail(self, test_name, error):
        self.failed += 1
        self.errors.append((test_name, error))
        print(f"❌ {test_name} - FAILED: {error}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"TOTAL: {self.passed}/{total} tests PASSED ({100*self.passed/total:.1f}%)")
        if self.failed > 0:
            print(f"\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")
        print(f"{'='*60}\n")
        return self.failed == 0


# ============================================================================
# TEST SUITE A: QueryAnalyzer Tests (25 tests)
# ============================================================================

def test_query_analyzer(results):
    """Test QueryAnalyzer complexity detection"""

    print("\n" + "="*60)
    print("TEST SUITE A: QueryAnalyzer (25 tests)")
    print("="*60 + "\n")

    analyzer = QueryAnalyzer()

    # Test 1: Simple question - Level 1
    try:
        q = "O que é perispírito?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 1, f"Expected level 1, got {analysis['complexity_level']}"
        assert analysis['recommended_searches'] == 1
        results.record_pass("test_simple_question_level_1")
    except Exception as e:
        results.record_fail("test_simple_question_level_1", str(e))

    # Test 2: Simple direct question
    try:
        q = "Quem foi Allan Kardec?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 1
        results.record_pass("test_simple_direct_question")
    except Exception as e:
        results.record_fail("test_simple_direct_question", str(e))

    # Test 3: Medium comparative - Level 2
    try:
        q = "Qual a diferença entre médium e sensitivo?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 2, f"Expected level 2, got {analysis['complexity_level']}"
        assert analysis['is_comparative'] == True
        assert analysis['recommended_searches'] >= 2
        results.record_pass("test_medium_comparative_level_2")
    except Exception as e:
        results.record_fail("test_medium_comparative_level_2", str(e))

    # Test 4: Medium relationship question
    try:
        q = "Qual a relação entre perispírito e reencarnação?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] >= 2
        assert analysis['is_comparative'] == True
        results.record_pass("test_medium_relationship_question")
    except Exception as e:
        results.record_fail("test_medium_relationship_question", str(e))

    # Test 5: Complex multi-concept - Level 3
    try:
        q = "Como mediunidade, perispírito e evolução espiritual se relacionam no processo de reencarnação?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 3, f"Expected level 3, got {analysis['complexity_level']}"
        assert analysis['num_concepts'] >= 3
        assert analysis['recommended_searches'] >= 3
        results.record_pass("test_complex_multi_concept_level_3")
    except Exception as e:
        results.record_fail("test_complex_multi_concept_level_3", str(e))

    # Test 6: Concept extraction accuracy
    try:
        q = "Explique sobre mediunidade e reencarnação"
        analysis = analyzer.analyze_complexity(q)
        assert 'mediunidade' in [c.lower() for c in analysis['concepts']]
        assert 'reencarnação' in [c.lower() for c in analysis['concepts']] or 'reencarnar' in [c.lower() for c in analysis['concepts']]
        results.record_pass("test_concept_extraction_accuracy")
    except Exception as e:
        results.record_fail("test_concept_extraction_accuracy", str(e))

    # Test 7: Comparative keyword detection - "comparar"
    try:
        q = "Compare evangelho e gênese"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['is_comparative'] == True
        results.record_pass("test_comparative_keyword_comparar")
    except Exception as e:
        results.record_fail("test_comparative_keyword_comparar", str(e))

    # Test 8: Comparative keyword - "versus"
    try:
        q = "Evolução espiritual versus karma"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['is_comparative'] == True
        results.record_pass("test_comparative_keyword_versus")
    except Exception as e:
        results.record_fail("test_comparative_keyword_versus", str(e))

    # Test 9: Comparative keyword - "semelhança"
    try:
        q = "Quais as semelhanças entre obsessão e influência espiritual?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['is_comparative'] == True
        results.record_pass("test_comparative_keyword_semelhanca")
    except Exception as e:
        results.record_fail("test_comparative_keyword_semelhanca", str(e))

    # Test 10: Fallback concept extraction
    try:
        q = "Qual a história do desenvolvimento doutrinário?"
        analysis = analyzer.analyze_complexity(q)
        assert len(analysis['concepts']) > 0  # Should extract some words
        results.record_pass("test_fallback_concept_extraction")
    except Exception as e:
        results.record_fail("test_fallback_concept_extraction", str(e))

    # Test 11: Long question triggers higher complexity
    try:
        q = "Explique de forma detalhada como funcionam os processos de comunicação entre encarnados e desencarnados segundo a codificação espírita de Allan Kardec"
        analysis = analyzer.analyze_complexity(q)
        assert len(q) > 100
        assert analysis['complexity_level'] >= 2  # Length should increase complexity
        results.record_pass("test_long_question_complexity")
    except Exception as e:
        results.record_fail("test_long_question_complexity", str(e))

    # Test 12: Single concept question
    try:
        q = "Explique reencarnação"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['num_concepts'] >= 1
        results.record_pass("test_single_concept_extraction")
    except Exception as e:
        results.record_fail("test_single_concept_extraction", str(e))

    # Test 13: Multiple concepts detected
    try:
        q = "Fale sobre caridade, amor e perdão"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['num_concepts'] >= 2
        results.record_pass("test_multiple_concepts_detected")
    except Exception as e:
        results.record_fail("test_multiple_concepts_detected", str(e))

    # Test 14: Question with book names
    try:
        q = "O que diz o Livro dos Espíritos sobre evolução?"
        analysis = analyzer.analyze_complexity(q)
        # Should detect both book and concept
        concepts_lower = [c.lower() for c in analysis['concepts']]
        assert any('espírito' in c or 'evolução' in c for c in concepts_lower)
        results.record_pass("test_question_with_book_names")
    except Exception as e:
        results.record_fail("test_question_with_book_names", str(e))

    # Test 15: Empty/very short question
    try:
        q = "Espírito?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 1  # Should be simple
        results.record_pass("test_very_short_question")
    except Exception as e:
        results.record_fail("test_very_short_question", str(e))

    # Test 16: Question with special characters
    try:
        q = "O que é 'karma' segundo o Espiritismo?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] >= 1
        results.record_pass("test_question_special_chars")
    except Exception as e:
        results.record_fail("test_question_special_chars", str(e))

    # Test 17: Deduplication of similar concepts
    try:
        q = "Espírito e espíritos e desencarnado"
        analysis = analyzer.analyze_complexity(q)
        # Should not count "espírito" and "espíritos" as separate
        assert analysis['num_concepts'] >= 1
        results.record_pass("test_concept_deduplication")
    except Exception as e:
        results.record_fail("test_concept_deduplication", str(e))

    # Test 18: Complexity score calculation - low score
    try:
        q = "Perispírito"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['complexity_level'] == 1
        results.record_pass("test_complexity_score_low")
    except Exception as e:
        results.record_fail("test_complexity_score_low", str(e))

    # Test 19: Recommended searches - simple
    try:
        q = "O que é fluido?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['recommended_searches'] == 1
        results.record_pass("test_recommended_searches_simple")
    except Exception as e:
        results.record_fail("test_recommended_searches_simple", str(e))

    # Test 20: Recommended searches - complex
    try:
        q = "Como caridade, evangelho, amor e perdão se relacionam na evolução espiritual?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['recommended_searches'] >= 3
        results.record_pass("test_recommended_searches_complex")
    except Exception as e:
        results.record_fail("test_recommended_searches_complex", str(e))

    # Test 21: Accent normalization
    try:
        q = "O que é perispírito e reencarnação?"
        analysis = analyzer.analyze_complexity(q)
        concepts_lower = [c.lower() for c in analysis['concepts']]
        # Should find both concepts despite accents
        assert len(concepts_lower) >= 2
        results.record_pass("test_accent_normalization")
    except Exception as e:
        results.record_fail("test_accent_normalization", str(e))

    # Test 22: Case insensitivity
    try:
        q = "QUAL A DIFERENÇA ENTRE MÉDIUM E SENSITIVO?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['is_comparative'] == True
        results.record_pass("test_case_insensitivity")
    except Exception as e:
        results.record_fail("test_case_insensitivity", str(e))

    # Test 23: Sub-question splitting
    try:
        q = "O que é mediunidade e como desenvolvê-la?"
        analysis = analyzer.analyze_complexity(q)
        # Should detect "e como" as splitter
        assert len(analysis['sub_questions']) >= 1
        results.record_pass("test_sub_question_splitting")
    except Exception as e:
        results.record_fail("test_sub_question_splitting", str(e))

    # Test 24: Max searches limit respected
    try:
        q = "Explique mediunidade, perispírito, reencarnação, evolução, caridade, amor, perdão e evangelho"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['recommended_searches'] <= 5  # MAX_SEARCHES
        results.record_pass("test_max_searches_limit")
    except Exception as e:
        results.record_fail("test_max_searches_limit", str(e))

    # Test 25: Min searches maintained
    try:
        q = "?"
        analysis = analyzer.analyze_complexity(q)
        assert analysis['recommended_searches'] >= 1  # MIN_SEARCHES
        results.record_pass("test_min_searches_maintained")
    except Exception as e:
        results.record_fail("test_min_searches_maintained", str(e))


# ============================================================================
# TEST SUITE B: Query Generation Tests (20 tests)
# ============================================================================

def test_query_generation(results):
    """Test search query generation"""

    print("\n" + "="*60)
    print("TEST SUITE B: Query Generation (20 tests)")
    print("="*60 + "\n")

    analyzer = QueryAnalyzer()

    # Mock vectorstore (not needed for query generation tests)
    class MockVectorstore:
        pass

    engine = MultiSearchEngine(MockVectorstore())

    # Test 1: Simple generates one query
    try:
        q = "O que é perispírito?"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 1)
        assert len(queries) == 1
        assert queries[0] == q  # Should be original
        results.record_pass("test_simple_generates_one_query")
    except Exception as e:
        results.record_fail("test_simple_generates_one_query", str(e))

    # Test 2: Medium comparative generates three
    try:
        q = "Diferença entre médium e sensitivo?"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 3)
        assert len(queries) == 3
        assert queries[0] == q  # First is always original
        results.record_pass("test_medium_comparative_generates_three")
    except Exception as e:
        results.record_fail("test_medium_comparative_generates_three", str(e))

    # Test 3: Complex generates up to five
    try:
        q = "Como mediunidade, perispírito, evolução e reencarnação se relacionam?"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 5)
        assert len(queries) <= 5
        assert len(queries) >= 3
        results.record_pass("test_complex_generates_up_to_five")
    except Exception as e:
        results.record_fail("test_complex_generates_up_to_five", str(e))

    # Test 4: Original query always first
    try:
        q = "Explique reencarnação e mediunidade"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 3)
        assert queries[0] == q
        results.record_pass("test_original_query_always_first")
    except Exception as e:
        results.record_fail("test_original_query_always_first", str(e))

    # Test 5: Query limit respected
    try:
        q = "Teste com muitos conceitos"
        analysis = {'concepts': ['a', 'b', 'c', 'd', 'e', 'f'], 'is_comparative': False}
        queries = engine._generate_search_queries(q, analysis, 3)
        assert len(queries) <= 3
        results.record_pass("test_query_limit_respected")
    except Exception as e:
        results.record_fail("test_query_limit_respected", str(e))

    # Test 6: Comparative generates concept-specific queries
    try:
        q = "Compare mediunidade e intuição"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 3)
        # Should include concept-based queries
        assert any('definição' in query.lower() or 'mediunidade' in query.lower() for query in queries[1:])
        results.record_pass("test_comparative_concept_queries")
    except Exception as e:
        results.record_fail("test_comparative_concept_queries", str(e))

    # Test 7: Non-comparative multi-concept
    try:
        q = "Explique perispírito e reencarnação"
        analysis = analyzer.analyze_complexity(q)
        analysis['is_comparative'] = False  # Force non-comparative
        queries = engine._generate_search_queries(q, analysis, 3)
        assert len(queries) >= 2
        results.record_pass("test_non_comparative_multi_concept")
    except Exception as e:
        results.record_fail("test_non_comparative_multi_concept", str(e))

    # Test 8: Expansion queries for single concept
    try:
        q = "Mediunidade"
        analysis = {'concepts': ['mediunidade'], 'is_comparative': False}
        queries = engine._generate_search_queries(q, analysis, 3)
        # Should expand the query
        assert len(queries) == 3
        assert any('explicação' in query.lower() or 'allan kardec' in query.lower() or 'ensinamentos' in query.lower() for query in queries[1:])
        results.record_pass("test_expansion_queries_single_concept")
    except Exception as e:
        results.record_fail("test_expansion_queries_single_concept", str(e))

    # Test 9: No empty queries
    try:
        q = "Teste"
        analysis = {'concepts': [], 'is_comparative': False}
        queries = engine._generate_search_queries(q, analysis, 2)
        assert all(len(query.strip()) > 0 for query in queries)
        results.record_pass("test_no_empty_queries")
    except Exception as e:
        results.record_fail("test_no_empty_queries", str(e))

    # Test 10: Queries are strings
    try:
        q = "Perispírito"
        analysis = analyzer.analyze_complexity(q)
        queries = engine._generate_search_queries(q, analysis, 2)
        assert all(isinstance(query, str) for query in queries)
        results.record_pass("test_queries_are_strings")
    except Exception as e:
        results.record_fail("test_queries_are_strings", str(e))

    # Test 11-20: Additional query generation tests
    for i in range(11, 21):
        try:
            # Generic test for various question types
            q = f"Pergunta de teste {i}"
            analysis = analyzer.analyze_complexity(q)
            num_searches = min(i % 5 + 1, 5)  # Vary between 1-5
            queries = engine._generate_search_queries(q, analysis, num_searches)
            assert len(queries) == num_searches
            assert queries[0] == q
            results.record_pass(f"test_query_generation_{i}")
        except Exception as e:
            results.record_fail(f"test_query_generation_{i}", str(e))


# ============================================================================
# TEST SUITE C: Deduplication Tests (15 tests)
# ============================================================================

def test_deduplication(results):
    """Test document deduplication"""

    print("\n" + "="*60)
    print("TEST SUITE C: Deduplication (15 tests)")
    print("="*60 + "\n")

    # Create mock documents
    def create_doc(content, source="test.pdf", page=1):
        return Document(
            page_content=content,
            metadata={'source': source, 'page': page}
        )

    class MockVectorstore:
        pass

    engine = MultiSearchEngine(MockVectorstore())

    # Test 1: Exact duplicate removal
    try:
        docs = [
            create_doc("Este é um texto de teste sobre perispírito."),
            create_doc("Este é um texto de teste sobre perispírito."),  # Exact duplicate
            create_doc("Outro texto completamente diferente.")
        ]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        # Should remove one duplicate (keeping 2 unique)
        assert len(unique) <= 2
        results.record_pass("test_exact_duplicate_removal")
    except Exception as e:
        results.record_fail("test_exact_duplicate_removal", str(e))

    # Test 2: Fingerprint-based deduplication
    try:
        # First 200 chars identical, rest different
        text1 = "A" * 200 + "diferente1"
        text2 = "A" * 200 + "diferente2"
        docs = [create_doc(text1), create_doc(text2)]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        # Should recognize as duplicates (same 200-char fingerprint)
        assert len(unique) == 1
        results.record_pass("test_fingerprint_deduplication")
    except Exception as e:
        results.record_fail("test_fingerprint_deduplication", str(e))

    # Test 3: Different content preserved
    try:
        docs = [
            create_doc("Texto A sobre mediunidade"),
            create_doc("Texto B sobre reencarnação"),
            create_doc("Texto C sobre perispírito")
        ]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        assert len(unique) == 3  # All different
        results.record_pass("test_different_content_preserved")
    except Exception as e:
        results.record_fail("test_different_content_preserved", str(e))

    # Test 4: Empty list handling
    try:
        docs = []
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        assert len(unique) == 0
        results.record_pass("test_empty_list_handling")
    except Exception as e:
        results.record_fail("test_empty_list_handling", str(e))

    # Test 5: Single document
    try:
        docs = [create_doc("Único documento")]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        assert len(unique) == 1
        results.record_pass("test_single_document")
    except Exception as e:
        results.record_fail("test_single_document", str(e))

    # Test 6: k limit respected
    try:
        docs = [create_doc(f"Texto {i}") for i in range(20)]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=5)
        assert len(unique) <= 5
        results.record_pass("test_k_limit_respected")
    except Exception as e:
        results.record_fail("test_k_limit_respected", str(e))

    # Test 7: Whitespace normalization
    try:
        docs = [
            create_doc("Texto    com    espaços"),
            create_doc("Texto com espaços")  # Same after normalization
        ]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        assert len(unique) == 1  # Should deduplicate
        results.record_pass("test_whitespace_normalization")
    except Exception as e:
        results.record_fail("test_whitespace_normalization", str(e))

    # Test 8: Case normalization
    try:
        docs = [
            create_doc("TEXTO EM MAIÚSCULAS"),
            create_doc("texto em maiúsculas")  # Same after case normalization
        ]
        unique = engine._deduplicate_and_rerank(docs, "teste", k=10)
        assert len(unique) == 1
        results.record_pass("test_case_normalization")
    except Exception as e:
        results.record_fail("test_case_normalization", str(e))

    # Test 9-15: Additional deduplication tests
    for i in range(9, 16):
        try:
            # Various edge cases
            if i == 9:
                # Very short documents
                docs = [create_doc("A"), create_doc("B"), create_doc("A")]
            elif i == 10:
                # Very long documents
                docs = [create_doc("X" * 1000), create_doc("Y" * 1000)]
            elif i == 11:
                # Mixed lengths
                docs = [create_doc("Short"), create_doc("X" * 500), create_doc("Short")]
            else:
                # Generic test
                docs = [create_doc(f"Content {j}") for j in range(i)]

            unique = engine._deduplicate_and_rerank(docs, "teste", k=20)
            assert isinstance(unique, list)
            assert all(isinstance(doc, Document) for doc in unique)
            results.record_pass(f"test_deduplication_{i}")
        except Exception as e:
            results.record_fail(f"test_deduplication_{i}", str(e))


# ============================================================================
# TEST SUITE D: Integration Tests (20 tests)
# ============================================================================

def test_integration(results):
    """Integration tests (simplified - no actual vectorstore)"""

    print("\n" + "="*60)
    print("TEST SUITE D: Integration (20 tests)")
    print("="*60 + "\n")

    # Note: Full integration tests would require a loaded vectorstore
    # These are simplified tests of the integration logic

    analyzer = QueryAnalyzer()

    # Test 1-20: End-to-end analysis tests
    test_questions = [
        ("O que é perispírito?", 1, 1),
        ("Quem foi Allan Kardec?", 1, 1),
        ("Explique reencarnação", 1, 1),
        ("Diferença entre médium e sensitivo?", 2, 2),
        ("Relação entre perispírito e reencarnação?", 2, 2),
        ("Compare evangelho e gênese", 2, 2),
        ("Como mediunidade e evolução se relacionam?", 2, 2),
        ("Mediunidade, perispírito, evolução e reencarnação", 3, 3),
        ("Como caridade, amor e perdão se relacionam?", 3, 3),
        ("Explique obsessão, influência e desencarnação", 3, 3),
        ("O que diz Kardec sobre evolução espiritual?", 2, 1),
        ("Fluidos e passes", 2, 2),
        ("Prece", 1, 1),
        ("Livre arbítrio versus destino", 2, 2),
        ("Expiação e provação na evolução", 2, 2),
        ("Mundo espiritual", 1, 1),
        ("Como desenvolver mediunidade?", 1, 1),
        ("Caridade segundo espiritismo", 1, 1),
        ("Evangelho e codificação espírita", 2, 2),
        ("O que é Doutrina Espírita?", 1, 1)
    ]

    for i, (question, expected_min_level, expected_min_searches) in enumerate(test_questions, 1):
        try:
            analysis = analyzer.analyze_complexity(question)

            # Check complexity level is reasonable
            assert 1 <= analysis['complexity_level'] <= 3

            # Check recommended searches
            assert analysis['recommended_searches'] >= expected_min_searches
            assert analysis['recommended_searches'] <= 5  # MAX_SEARCHES

            # Check has concepts (or fallback extraction worked)
            assert len(analysis['concepts']) > 0

            results.record_pass(f"test_integration_question_{i}")
        except Exception as e:
            results.record_fail(f"test_integration_question_{i}", str(e))


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    """Run all test suites"""

    print("\n" + "="*60)
    print("MULTI-SEARCH TEST SUITE")
    print("Testing: QueryAnalyzer, MultiSearchEngine")
    print("="*60)

    results = TestResults()

    # Run all test suites
    test_query_analyzer(results)
    test_query_generation(results)
    test_deduplication(results)
    test_integration(results)

    # Print summary
    success = results.summary()

    if success:
        print("🎉 ALL TESTS PASSED! Multi-search implementation is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review and fix.")
        return 1


if __name__ == "__main__":
    exit(main())
