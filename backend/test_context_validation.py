"""
Test script for context validation

Tests the ContextValidator to ensure it correctly identifies
in-context and out-of-context questions.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from context_validator import ContextValidator
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL, CONTEXT_VALIDATION_THRESHOLD


def test_context_validation():
    """Test context validation with various questions"""

    print("=" * 80)
    print("🧪 TESTANDO VALIDAÇÃO DE CONTEXTO")
    print("=" * 80)
    print()

    # Create embeddings
    print("📊 Carregando modelo de embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'}  # Use CPU for testing
    )
    print("✅ Embeddings carregados!")
    print()

    # Create validator
    print("🔧 Criando validador de contexto...")
    validator = ContextValidator(embeddings)
    print()

    # Test cases
    valid_questions = [
        "O que é o perispírito?",
        "Explique sobre reencarnação segundo Allan Kardec",
        "Como funciona a mediunidade?",
        "O que acontece após a morte segundo o Espiritismo?",
        "Qual o papel da caridade no Espiritismo?",
        "O que é a lei de causa e efeito?",
        "Allan Kardec escreveu sobre evolução espiritual?",
        "Diferença entre médium e sensitivo",
        "O que diz O Livro dos Espíritos sobre livre arbítrio?",
        "Como a prece pode ajudar os espíritos?",
    ]

    invalid_questions = [
        "Qual a receita de bolo de chocolate?",
        "Quem ganhou a Copa do Mundo 2022?",
        "Como consertar meu computador?",
        "Recomende uma série de TV",
        "Qual o melhor restaurante da cidade?",
        "Como fazer um bolo de cenoura?",
        "Quem é o presidente do Brasil?",
        "Qual time de futebol é melhor?",
        "Como programar em Python?",
        "Onde comprar um celular barato?",
    ]

    print("=" * 80)
    print("✅ TESTANDO PERGUNTAS VÁLIDAS (devem passar)")
    print("=" * 80)
    print()

    valid_passed = 0
    valid_total = len(valid_questions)

    for i, question in enumerate(valid_questions, 1):
        is_valid, score, reason = validator.validate_question(
            question,
            threshold=CONTEXT_VALIDATION_THRESHOLD
        )

        status = "✅ PASSOU" if is_valid else "❌ FALHOU"
        color = "\033[92m" if is_valid else "\033[91m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} [{score:.3f}] {question}")

        if is_valid:
            valid_passed += 1

    print()
    print(f"📊 Resultado: {valid_passed}/{valid_total} perguntas válidas aceitas "
          f"({100*valid_passed/valid_total:.1f}%)")
    print()

    print("=" * 80)
    print("❌ TESTANDO PERGUNTAS INVÁLIDAS (devem ser rejeitadas)")
    print("=" * 80)
    print()

    invalid_rejected = 0
    invalid_total = len(invalid_questions)

    for i, question in enumerate(invalid_questions, 1):
        is_valid, score, reason = validator.validate_question(
            question,
            threshold=CONTEXT_VALIDATION_THRESHOLD
        )

        # For invalid questions, we want is_valid to be False
        passed = not is_valid
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        color = "\033[92m" if passed else "\033[91m"
        reset = "\033[0m"

        print(f"{color}{status}{reset} [{score:.3f}] {question}")

        if passed:
            invalid_rejected += 1

    print()
    print(f"📊 Resultado: {invalid_rejected}/{invalid_total} perguntas inválidas rejeitadas "
          f"({100*invalid_rejected/invalid_total:.1f}%)")
    print()

    # Overall results
    print("=" * 80)
    print("📊 RESULTADO GERAL")
    print("=" * 80)
    print()

    total_correct = valid_passed + invalid_rejected
    total_questions = valid_total + invalid_total
    accuracy = 100 * total_correct / total_questions

    print(f"✅ Perguntas válidas aceitas: {valid_passed}/{valid_total} "
          f"({100*valid_passed/valid_total:.1f}%)")
    print(f"❌ Perguntas inválidas rejeitadas: {invalid_rejected}/{invalid_total} "
          f"({100*invalid_rejected/invalid_total:.1f}%)")
    print()
    print(f"🎯 ACURÁCIA TOTAL: {total_correct}/{total_questions} ({accuracy:.1f}%)")
    print()

    # Metrics
    print("📈 MÉTRICAS:")
    print(f"   - Precision (válidas aceitas): {100*valid_passed/valid_total:.1f}%")
    print(f"   - Recall (inválidas rejeitadas): {100*invalid_rejected/invalid_total:.1f}%")
    print(f"   - Threshold usado: {CONTEXT_VALIDATION_THRESHOLD}")
    print()

    # Pass/Fail
    if accuracy >= 90.0:
        print("✅ TESTE PASSOU! Acurácia >= 90%")
        return True
    else:
        print("❌ TESTE FALHOU! Acurácia < 90%")
        print("💡 Sugestão: Ajustar CONTEXT_VALIDATION_THRESHOLD em config.py")
        return False


if __name__ == "__main__":
    try:
        success = test_context_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro durante teste: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
