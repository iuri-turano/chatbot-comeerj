"""
Context Validator - Valida se perguntas estão relacionadas ao Espiritismo

Este módulo implementa um sistema de validação em 3 camadas para detectar
e rejeitar perguntas fora do contexto espírita.
"""

from langchain_community.embeddings import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL
import numpy as np
from typing import Tuple


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
        "doutrina espírita Kardecista",
        "expiação e provação",
        "erraticidade",
        "pluralidade dos mundos habitados"
    ]

    # Keywords de rejeição rápida
    OFF_TOPIC_KEYWORDS = [
        # Culinária
        "receita", "cozinha", "ingrediente", "bolo", "comida", "prato",
        "tempero", "cozinhar", "assar", "fritar",
        # Esportes
        "futebol", "jogo", "time", "campeonato", "gol", "basquete",
        "vôlei", "tênis", "corrida", "atleta",
        # Política
        "eleição", "presidente", "deputado", "partido", "governo",
        "senador", "voto", "política", "ministro",
        # Tecnologia não relacionada
        "celular", "computador", "software", "app", "internet",
        "programação", "código", "sistema operacional", "windows",
        # Entretenimento
        "filme", "série", "novela", "música", "cantor", "ator",
        "cinema", "teatro", "show", "banda",
        # Outros
        "moda", "carro", "viagem", "hotel", "shopping", "compra",
        "produto", "marca", "preço"
    ]

    def __init__(self, embeddings):
        self.embeddings = embeddings

        # Pre-calcular embeddings dos tópicos (cache)
        print("🔍 Calculando embeddings dos tópicos espíritas...")
        self.topic_embeddings = self._compute_topic_embeddings()
        print(f"✅ {len(self.topic_embeddings)} tópicos espíritas indexados")

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
            # Cosine similarity
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
    ) -> Tuple[bool, float, str]:
        """
        Valida se pergunta está relacionada ao Espiritismo

        Args:
            question: Pergunta do usuário
            threshold: Threshold mínimo de similaridade (0.0 a 1.0)

        Returns:
            (is_valid, confidence_score, reason)
            - is_valid: True se pergunta é válida
            - confidence_score: 0.0 a 1.0
            - reason: Explicação da decisão
        """

        # Camada 1: Quick keyword check
        if self._quick_keyword_check(question):
            return (
                False,
                0.0,
                "Keywords fora de contexto detectadas"
            )

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
