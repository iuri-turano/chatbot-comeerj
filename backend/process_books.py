import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from config import BOOKS_DIR, DB_DIR, CHUNK_SIZE, CHUNK_OVERLAP, EMBEDDING_MODEL
import torch

def load_documents():
    """Load all PDF and DOCX files from books directory"""
    documents = []
    
    if not os.path.exists(BOOKS_DIR):
        os.makedirs(BOOKS_DIR)
        print(f"Created {BOOKS_DIR} directory. Please add your books there.")
        return documents
    
    print(f"Loading documents from {BOOKS_DIR}...")
    
    for filename in os.listdir(BOOKS_DIR):
        file_path = os.path.join(BOOKS_DIR, filename)
        
        try:
            if filename.lower().endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"✓ Loaded: {filename}")
                
            elif filename.lower().endswith('.docx'):
                loader = Docx2txtLoader(file_path)
                documents.extend(loader.load())
                print(f"✓ Loaded: {filename}")
                
        except Exception as e:
            print(f"✗ Error loading {filename}: {str(e)}")
    
    print(f"\nTotal documents loaded: {len(documents)}")
    return documents

def split_documents(documents):
    """Split documents into chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Documents split into {len(chunks)} chunks")
    return chunks

def create_vectorstore(chunks):
    """Create and persist vector database in batches"""
    print("\nCreating embeddings (this may take a few minutes)...")
    
    # Use GPU if available
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': device}
    )
    
    # ChromaDB batch size limit
    BATCH_SIZE = 5000
    total_chunks = len(chunks)
    
    print(f"\nProcessing {total_chunks} chunks in batches of {BATCH_SIZE}...")
    
    vectorstore = None
    
    # Process in batches
    for i in range(0, total_chunks, BATCH_SIZE):
        batch_end = min(i + BATCH_SIZE, total_chunks)
        batch = chunks[i:batch_end]
        
        print(f"Processing batch {i//BATCH_SIZE + 1}/{(total_chunks + BATCH_SIZE - 1)//BATCH_SIZE} ({i+1}-{batch_end}/{total_chunks})")
        
        if vectorstore is None:
            # Create new vectorstore with first batch
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=DB_DIR
            )
        else:
            # Add to existing vectorstore
            vectorstore.add_documents(batch)
        
        print(f"  ✓ Batch processed ({batch_end}/{total_chunks} chunks indexed)")
    
    print(f"\n✓ Vector database created and saved to {DB_DIR}")
    print(f"✓ Total chunks indexed: {total_chunks}")
    
    return vectorstore

def main():
    print("=== Assistente Espírita - Processamento de Livros ===\n")
    
    # Load documents
    documents = load_documents()
    
    if not documents:
        print("\nNenhum documento encontrado. Adicione arquivos PDF ou DOCX na pasta 'books'.")
        return
    
    # Split into chunks
    chunks = split_documents(documents)
    
    # Create vector database
    vectorstore = create_vectorstore(chunks)
    
    print("\n=== Processamento Completo ===")
    print("Você pode executar a aplicação com: streamlit run app.py")

if __name__ == "__main__":
    main()