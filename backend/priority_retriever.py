from langchain.schema import Document
from typing import List, Tuple
from config import get_book_priority

def remove_duplicate_chunks(documents: List[Document], similarity_threshold: float = 0.85) -> List[Document]:
    """
    Remove duplicate or very similar chunks.
    Uses simple text similarity to detect duplicates.
    """
    unique_docs = []
    seen_contents = []
    
    for doc in documents:
        content = doc.page_content.strip()
        
        # Check if this content is too similar to any we've already seen
        is_duplicate = False
        for seen_content in seen_contents:
            # Simple similarity: check if one is a substring of the other
            # or if they share most of their content
            if content in seen_content or seen_content in content:
                is_duplicate = True
                break
            
            # Calculate simple similarity (ratio of common characters)
            if len(content) > 100 and len(seen_content) > 100:
                # If first 100 chars are identical, it's likely duplicate
                if content[:100] == seen_content[:100]:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_docs.append(doc)
            seen_contents.append(content)
    
    return unique_docs

# def remove_duplicate_chunks(documents: List[Document], similarity_threshold: float = 0.85) -> List[Document]:
#     """
#     Remove duplicate or very similar chunks more aggressively.
#     """
#     unique_docs = []
#     seen_fingerprints = set()
    
#     for doc in documents:
#         content = doc.page_content.strip()
        
#         # Create a fingerprint (first 200 chars + last 100 chars)
#         if len(content) > 300:
#             fingerprint = content[:200] + content[-100:]
#         else:
#             fingerprint = content
        
#         # Normalize fingerprint (remove extra spaces, lowercase)
#         fingerprint = " ".join(fingerprint.split()).lower()
        
#         if fingerprint not in seen_fingerprints:
#             unique_docs.append(doc)
#             seen_fingerprints.add(fingerprint)
    
#     return unique_docs

def rerank_by_priority(documents: List[Document], top_k: int = 8) -> List[Document]:
    """
    Rerank documents giving priority to fundamental spiritist works.
    
    Priority order:
    1. O Livro dos Espíritos (weight: 100)
    2. Other 5 fundamental books (weight: 70)
    3. Revista Espírita (weight: 40)
    4. Other works (weight: 10)
    """
    
    # First, remove duplicates
    documents = remove_duplicate_chunks(documents)
    
    # Score each document
    scored_docs = []
    for i, doc in enumerate(documents):
        source = doc.metadata.get('source', '')
        
        # Get priority based on book
        priority_score = get_book_priority(source)
        
        # Position score (earlier results from vector search are more relevant)
        # Start with high score that decreases with position
        position_score = 100 - (i * 2)  # First doc: 100, second: 98, etc.
        
        # Combined score: priority is very important, but position also matters
        # Formula: (priority * 2) + position
        # This means priority can overcome position, but position still matters
        total_score = (priority_score * 2) + position_score
        
        scored_docs.append((total_score, doc, source))
    
    # Sort by total score (descending)
    scored_docs.sort(reverse=True, key=lambda x: x[0])
    
    # Debug info
    print("\n📚 RERANKING DOS DOCUMENTOS (após deduplicação):")
    for score, doc, source in scored_docs[:top_k]:
        book_name = source.split('/')[-1] if '/' in source else source.split('\\')[-1]
        priority = get_book_priority(source)
        page = doc.metadata.get('page', 'N/A')
        print(f"  Score: {score:3.0f} | Prioridade: {priority:3d} | Pág: {page} | {book_name[:40]}")
    print()
    
    # Return top K documents after reranking
    return [doc for _, doc, _ in scored_docs[:top_k]]

def prioritized_search(vectorstore, question: str, k: int = 8, fetch_k: int = 20) -> List[Document]:
    """
    Search with priority-based reranking and deduplication.
    
    1. Fetch more documents than needed (fetch_k)
    2. Remove duplicates
    3. Rerank them by book priority
    4. Return top k
    """
    
    # Fetch more documents initially for filtering
    initial_docs = vectorstore.similarity_search(question, k=fetch_k)
    
    # Rerank by priority (includes deduplication)
    prioritized_docs = rerank_by_priority(initial_docs, top_k=k)
    
    return prioritized_docs