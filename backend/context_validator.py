"""
Context Validator - Valida se perguntas estão relacionadas ao Espiritismo

Este módulo implementa validação semântica para detectar e rejeitar
perguntas fora do contexto espírita usando embeddings.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL
import numpy as np
from typing import Tuple


class ContextValidator:
    """Valida se perguntas estão relacionadas ao Espiritismo

    Usa validação semântica comparando a similaridade da pergunta
    com tópicos espíritas vs tópicos não-espíritas.
    """

    # Exemplos de perguntas ESPÍRITAS (in-context)
    SPIRITIST_EXAMPLES = [
        "O que é o perispírito?",
        "Como funciona a reencarnação?",
        "O que Allan Kardec ensina sobre mediunidade?",
        "Qual a diferença entre espírito e alma?",
        "O que acontece após a morte segundo o Espiritismo?",
        "Como desenvolver a mediunidade?",
        "O que é obsessão espiritual?",
        "Qual o papel da caridade no Espiritismo?",
        "O que diz O Livro dos Espíritos sobre Deus?",
        "Como é a vida no mundo espiritual?",
        "O que é a lei de causa e efeito?",
        "Explique sobre a evolução espiritual",
        "O que é uma prova na vida segundo o Espiritismo?",
        "Como funciona a comunicação com espíritos?",
        "O que é o fluido universal?",
        "Qual a visão espírita sobre o suicídio?",
        "O que é uma missão espiritual?",
        "Como é o processo de desencarne?",
        "O que são espíritos superiores?",
        "Qual a relação entre Espiritismo e Cristianismo?"
    ]

    # Exemplos de perguntas NÃO-ESPÍRITAS (out-of-context)
    NON_SPIRITIST_EXAMPLES = [
        "Como fazer um bolo de chocolate?",
        "Qual time ganhou o campeonato?",
        "Quem é o presidente atual?",
        "Como instalar o Windows?",
        "Qual o melhor celular para comprar?",
        "Onde fica o hotel mais próximo?",
        "Qual a previsão do tempo?",
        "Como funciona um carro elétrico?",
        "Quem ganhou o Oscar este ano?",
        "Qual a melhor série na Netflix?",
        "Como aprender Python?",
        "Qual restaurante você recomenda?",
        "Quanto custa um apartamento?",
        "Como funciona a bolsa de valores?",
        "Qual a capital da França?",
        "Como fazer exercícios físicos?",
        "Qual a melhor roupa para comprar?",
        "Como viajar barato?",
        "Qual o melhor produto de limpeza?",
        "Como funciona o Instagram?"
    ]

    def __init__(self, embeddings):
        """Inicializa validador com embeddings pré-computados"""
        self.embeddings = embeddings
        print("🔍 Inicializando validador de contexto com embeddings...")

        # Criar embeddings para exemplos
        print("   Processando exemplos espíritas...")
        self.spiritist_embeddings = np.array([
            self.embeddings.embed_query(q) for q in self.SPIRITIST_EXAMPLES
        ])

        print("   Processando exemplos não-espíritas...")
        self.non_spiritist_embeddings = np.array([
            self.embeddings.embed_query(q) for q in self.NON_SPIRITIST_EXAMPLES
        ])

        print("✅ Context validator inicializado (validação semântica)")

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcula similaridade de cosseno entre dois vetores"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def _avg_similarity_to_group(self, query_embedding: np.ndarray, group_embeddings: np.ndarray) -> float:
        """Calcula similaridade média com um grupo de embeddings"""
        similarities = [
            self._cosine_similarity(query_embedding, example_emb)
            for example_emb in group_embeddings
        ]
        return float(np.mean(similarities))

    def validate_question(
        self,
        question: str,
        threshold: float = 0.10  # Diferença mínima entre scores espírita e não-espírita
    ) -> Tuple[bool, float, str]:
        """
        Valida se pergunta está relacionada ao Espiritismo usando análise semântica

        Compara a similaridade da pergunta com exemplos espíritas vs não-espíritas.
        Se a pergunta for mais similar a tópicos espíritas, é aceita.

        Args:
            question: Pergunta do usuário
            threshold: Diferença mínima entre similarity scores (0.10 = 10% mais similar a espírita)

        Returns:
            (is_valid, confidence_score, reason)
            - is_valid: True se é sobre Espiritismo
            - confidence_score: Diferença entre scores (positivo = espírita, negativo = não-espírita)
            - reason: Explicação da decisão
        """

        # Criar embedding da pergunta
        question_embedding = np.array(self.embeddings.embed_query(question))

        # Calcular similaridade média com exemplos espíritas
        spiritist_score = self._avg_similarity_to_group(
            question_embedding,
            self.spiritist_embeddings
        )

        # Calcular similaridade média com exemplos não-espíritas
        non_spiritist_score = self._avg_similarity_to_group(
            question_embedding,
            self.non_spiritist_embeddings
        )

        # Diferença entre scores (positivo = mais espírita, negativo = mais não-espírita)
        score_diff = spiritist_score - non_spiritist_score

        # Validar se é suficientemente mais similar a tópicos espíritas
        is_valid = score_diff >= threshold

        if is_valid:
            reason = (
                f"Pergunta validada como espírita "
                f"(similaridade: espírita={spiritist_score:.2f}, "
                f"não-espírita={non_spiritist_score:.2f}, "
                f"diferença={score_diff:.2f})"
            )
        else:
            reason = (
                f"Pergunta rejeitada: mais similar a tópicos não-espíritas "
                f"(similaridade: espírita={spiritist_score:.2f}, "
                f"não-espírita={non_spiritist_score:.2f}, "
                f"diferença={score_diff:.2f})"
            )

        return (is_valid, score_diff, reason)


def create_context_validator(embeddings) -> ContextValidator:
    """Factory function para criar validador"""
    return ContextValidator(embeddings)
