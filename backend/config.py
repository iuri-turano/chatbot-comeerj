import os
from dotenv import load_dotenv

load_dotenv()

# Local model configuration - OS-specific
import platform

def get_default_model():
    """Select model based on operating system and hardware"""
    system = platform.system().lower()

    if system == "darwin":  # macOS
        # Mac M4 16GB - use 3B model (fits in memory)
        return "llama3.2:3b"
    elif system == "windows":
        # Windows with RTX 3070 8GB + 32GB RAM - use 8B model
        return "llama3.1:8b"
    elif system == "linux":
        # Linux - default to 3B (can be overridden with env var)
        return "llama3.2:3b"
    else:
        return "llama3.2:3b"

LOCAL_MODEL_NAME = os.getenv("LOCAL_MODEL_NAME", get_default_model())
DEFAULT_TEMPERATURE = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))

# Paths
BOOKS_DIR = "books"
DB_DIR = "database"

# Model parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K = 3  # Changed from 5 to 3 for better performance
CONTEXT_WINDOW = 8192  # Increased from 4096 to 8192 for conversation context

# Embedding model
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

# Book priorities (higher = more important)
# Based on exact filenames you have
BOOK_PRIORITIES = {
    # Tier 1 - O Livro dos Espíritos (peso 100)
    "livro-dos-espiritos.pdf": 100,
    "livro dos espiritos": 100,
    "espiritos": 100,
    
    # Tier 2 - Obras Fundamentais da Codificação (peso 70)
    "o-evangelho-segundo-o-espiritismo.pdf": 70,
    "evangelho": 70,
    
    "livro-dos-mediuns": 70,
    "mediuns": 70,
    "guillon": 70,  # Para reconhecer "Livro-dos-Mediuns_Guillon.pdf"
    
    "a-genese": 70,
    "genese": 70,
    "gênese": 70,
    
    "ceu-e-inferno": 70,
    "céu-e-inferno": 70,
    "quintao": 70,  # Para reconhecer "ceu-e-inferno-Manuel-Quintao.pdf"
    "quintão": 70,
    
    "o-que-e-o-espiritismo.pdf": 70,
    "o-que-e": 70,
    
    # Tier 3 - Revista Espírita (peso 40)
    "revista_espirita": 40,
    "revista espirita": 40,
    "feb_18": 40,  # Reconhece todos os anos 1858-1869
    
    # Tier 4 - Outras obras (peso 10)
    "default": 10
}

def get_book_priority(source_path: str) -> int:
    """
    Get priority weight for a book based on its filename.
    
    Your current books:
    - Tier 1 (100): Livro-dos-Espiritos.pdf
    - Tier 2 (70): O-evangelho-segundo-o-espiritismo.pdf, Livro-dos-Mediuns_Guillon.pdf,
                   A-genese_Guillon.pdf, ceu-e-inferno-Manuel-Quintao.pdf, o-que-e-o-espiritismo.pdf
    - Tier 3 (40): revista_espirita_feb_1858.pdf ... 1869.pdf
    """
    if not source_path:
        return BOOK_PRIORITIES["default"]
    
    # Get just the filename (without path)
    filename = os.path.basename(source_path).lower()
    
    # Remove accents for better matching
    filename = filename.replace('í', 'i').replace('é', 'e').replace('ê', 'e').replace('ã', 'a')
    
    # Priority 1: Livro dos Espíritos
    if "livro-dos-espiritos" in filename or "livro dos espiritos" in filename:
        return 100
    
    # Priority 2: Obras Fundamentais
    if any(keyword in filename for keyword in [
        "evangelho-segundo",
        "livro-dos-mediuns",
        "livro dos mediuns",
        "mediuns_guillon",
        "a-genese",
        "genese_guillon",
        "ceu-e-inferno",
        "ceu e inferno",
        "quintao",
        "o-que-e-o-espiritismo"
    ]):
        return 70
    
    # Priority 3: Revista Espírita
    if "revista_espirita" in filename or "revista espirita" in filename:
        return 40
    
    # Default: outras obras
    return BOOK_PRIORITIES["default"]

def get_book_display_name(source_path: str) -> str:
    """Get a friendly display name for the book"""
    if not source_path:
        return "Desconhecido"
    
    filename = os.path.basename(source_path).lower()
    
    # Map to friendly names
    if "livro-dos-espiritos" in filename:
        return "📘 O Livro dos Espíritos"
    elif "evangelho-segundo" in filename:
        return "📗 O Evangelho Segundo o Espiritismo"
    elif "mediuns" in filename:
        return "📙 O Livro dos Médiuns"
    elif "genese" in filename or "gênese" in filename:
        return "📕 A Gênese"
    elif "ceu-e-inferno" in filename or "céu-e-inferno" in filename:
        return "📔 O Céu e o Inferno"
    elif "o-que-e" in filename:
        return "📓 O que é o Espiritismo"
    elif "revista_espirita" in filename:
        # Extract year from filename (e.g., "1858" from "revista_espirita_feb_1858.pdf")
        import re
        year_match = re.search(r'18(\d{2})', filename)
        if year_match:
            year = "18" + year_match.group(1)
            return f"📰 Revista Espírita ({year})"
        return "📰 Revista Espírita"
    
    return os.path.basename(source_path)

# ============================================================================
# CONTEXT VALIDATION SETTINGS
# ============================================================================

# Context validation threshold (0.0 a 1.0)
# - 0.25-0.30: Muito permissivo (aceita mais perguntas)
# - 0.35-0.40: Balanceado (recomendado)
# - 0.45-0.50: Restritivo (pode rejeitar perguntas válidas)
CONTEXT_VALIDATION_THRESHOLD = 0.35

# Score mínimo dos resultados de busca
MIN_SEARCH_SCORE = 0.4

# Mensagem de rejeição padrão
REJECTION_MESSAGE = """Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita.

Só posso responder perguntas relacionadas às obras de Allan Kardec e aos ensinamentos espíritas.

Por favor, faça uma pergunta sobre Espiritismo, como:
- O que é reencarnação?
- Como funciona a mediunidade?
- O que Allan Kardec diz sobre a vida após a morte?
- Qual o papel da caridade no Espiritismo?
"""