# CLAUDE.md - Spiritist RAG Chatbot Project

## Project Overview

This is an **MVP Spiritist RAG (Retrieval-Augmented Generation) Chatbot** designed to help users study the Spiritist Codification by Allan Kardec. The system reads, correlates, and provides reflections on questions about the foundational books of Spiritism.

**Key Purpose:**
- Answer questions about Spiritist doctrine using accurate citations from the codification
- Correlate information across multiple books
- Provide thoughtful reflections based on the teachings
- Enable word counting and metrics across the entire codification

**Deployment Architecture:**
- **Backend:** FastAPI server running locally with GPU acceleration, exposed via ngrok
- **Frontends:** Two Streamlit apps hosted on Streamlit Cloud
  - Main chatbot interface
  - Feedback analytics dashboard

---

## Project Structure

```
chatbot-comeerj/
├── backend/                    # FastAPI backend (local GPU server)
│   ├── api_server.py          # Main API endpoints (health, query, feedback)
│   ├── config.py              # Book priorities and configuration
│   ├── priority_retriever.py  # RAG prioritization logic
│   ├── process_books.py       # PDF/DOCX indexing pipeline
│   ├── feedback_system.py     # Backend feedback storage
│   ├── check_gpu.py           # GPU diagnostics
│   ├── requirements.txt       # Backend dependencies
│   ├── books/                 # 18 Spiritist books (PDFs)
│   ├── database/              # ChromaDB vector store (253MB)
│   ├── feedback/              # User feedback (JSONL format)
│   └── start_backend.bat      # Windows startup script
│
└── frontend/                   # Streamlit web interfaces
    ├── app.py                 # Main chat interface
    ├── app_feedbacks.py       # Feedback analytics dashboard
    ├── chat_history.py        # Conversation persistence
    ├── feedback_system.py     # Frontend feedback module
    ├── requirements.txt       # Frontend dependencies
    ├── chat_history/          # Stored conversations (JSON)
    └── feedback/              # Cached feedback data
```

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.115.6
- **LLM Server:** Ollama
  - Quality Model: `qwen2.5:7b` (for validated answers)
  - Fast Model: `llama3.2:3b` (for quick previews)
- **Vector Database:** ChromaDB 0.5.23 (253MB)
- **Embeddings:** sentence-transformers/paraphrase-multilingual-mpnet-base-v2
- **ML Framework:** PyTorch 2.1.2 with CUDA GPU support
- **Document Processing:** LangChain Community, PyPDF

### Frontend
- **Framework:** Streamlit 1.40.2
- **HTTP Client:** requests 2.32.3
- **Deployment:** Streamlit Cloud

### Infrastructure
- **Tunnel:** ngrok (exposes local backend to cloud)
- **GPU:** NVIDIA CUDA support for acceleration
- **Storage:** Local ChromaDB + JSON conversation history

---

## Core Features

### 1. Hybrid Two-Model Architecture
- **Fast Preview:** Llama3.2:3b generates quick initial response (~1-2s)
- **Quality Answer:** Qwen2.5:7b validates with RAG context (~3-4s)
- **Benefits:** Faster user feedback + accurate source-backed answers

### 2. Intelligent Source Prioritization
**Three-tier priority system:**
- **Priority 100:** O Livro dos Espíritos (foundational work)
- **Priority 70:** O Evangelho segundo o Espiritismo, Livro dos Médiuns, A Gênese, O Céu e o Inferno, O Que é o Espiritismo
- **Priority 40:** Revista Espírita (1858-1869, 12 years)

**Retrieval Algorithm:**
1. Vector similarity search (fetch_k=20 results)
2. Deduplication of similar chunks
3. Reranking: `Score = (priority × 2) + position_score`
4. Select top-k most relevant sources

### 3. RAG Pipeline (Preview Mode)
```
User Query
    ↓
[Phase 1] Fast Preview (knowledge-based, no sources)
    ↓
[Phase 2] Vector Search (parallel with preview)
    ├─ Similarity search
    ├─ Deduplication
    └─ Priority reranking
    ↓
[Phase 3] Quality Validation (with RAG context)
    ├─ Validate preview against sources
    ├─ Correct errors
    └─ Add missing information
    ↓
Final Response:
├─ Preview Answer
├─ Final Answer
├─ Validation Notes (what was maintained/corrected/added)
└─ Sources (with page numbers and priorities)
```

### 4. Performance Optimizations
- **Response Cache:** 500 entries, MD5-hashed queries
- **Rate Limiting:** 15 requests/minute per IP
- **Batch Processing:** 5000 chunks per batch for embeddings
- **ThreadPool Executor:** Async operations for parallel processing
- **Max Concurrent Requests:** 4

### 5. Conversation Management
- Auto-save conversations to JSON
- Context-aware: maintains last 5 messages
- Recent conversations list (10 items)
- Delete individual conversations
- Conversation ID tracking

### 6. Feedback System
**User Feedback:**
- Inline ratings: 👍 Good / 😐 Regular / 👎 Bad
- Optional comments for detailed feedback
- Stored centrally at backend (JSONL format)

**Analytics Dashboard:**
- Total feedback count
- Rating distribution (good/neutral/bad)
- Satisfaction score calculation
- Timeline charts for trends
- Filtering by rating and comment status
- Export to CSV/JSON

### 7. Rich Source Visualization
- Book emoji icons (📘 📗 📙)
- Priority badges (Prioridade: 100, 70, 40)
- Page numbers for citations
- Display names for better readability

---

## Books in Database

### Tier 1 - Foundational (Priority 100)
- **O Livro dos Espíritos** (The Book of Spirits)

### Tier 2 - Fundamental Works (Priority 70)
- **O Evangelho segundo o Espiritismo** (The Gospel According to Spiritism)
- **Livro dos Médiuns** (The Mediums' Book)
- **A Gênese** (Genesis)
- **O Céu e o Inferno** (Heaven and Hell)
- **O Que é o Espiritismo** (What is Spiritism)

### Tier 3 - Revista Espírita (Priority 40)
- Years: 1858, 1859, 1860, 1861, 1862, 1863, 1864, 1865, 1866, 1867, 1868, 1869 (12 volumes)

**Total:** 18 books indexed in vector database

---

## API Endpoints

### Backend (http://localhost:8000)

#### Health Check
```http
GET /health
```
Returns: status, CUDA availability, GPU name, timestamp

#### Status
```http
GET /status
```
Returns: uptime, models_loaded, cache stats, GPU info

#### Query
```http
POST /query
Content-Type: application/json

{
  "question": "O que é o perispírito?",
  "temperature": 0.2,
  "top_k": 5,
  "fetch_k": 20,
  "conversation_history": [...],
  "enable_preview": true
}
```
Returns: answer, sources, preview_answer, validation_notes, processing_time

#### Save Feedback
```http
POST /feedback
Content-Type: application/json

{
  "question": "...",
  "answer": "...",
  "rating": "good",
  "comment": "Very helpful!",
  "sources": [...]
}
```

#### Feedback Statistics
```http
GET /feedback/stats
```
Returns: total, rating counts, last 100 feedbacks

---

## Current Metrics & Analytics

### Response-Level Metrics
- Processing time (seconds)
- Source count per answer
- Cache hit/miss tracking
- Task ID for response tracking

### Backend Metrics (/status)
- Uptime (seconds)
- GPU/CUDA availability
- Models loaded status
- Cache statistics (size, hits, misses, hit rate %)

### Feedback Statistics
- Total feedback count
- Rating distribution (good/neutral/bad)
- Satisfaction score (good=1.0, neutral=0.5, bad=0.0)
- Comments ratio

### Conversation Analytics
- Total conversations count
- Total messages count
- Unique users count
- Average messages per conversation
- Message counts per conversation

---

## Roadmap & Goals

### Current State (MVP)
✅ RAG-based question answering
✅ Multi-book correlation through vector search
✅ Smart prioritization of foundational works
✅ Dual-model preview + validation architecture
✅ Feedback system with analytics dashboard
✅ Conversation history and context
✅ Source citations with page numbers

### Future Goals

#### 1. Enhanced Correlation & Reflections
- [ ] Cross-reference detection across books
- [ ] Thematic analysis (identify related topics)
- [ ] Generate reflections that synthesize multiple sources
- [ ] "Deep dive" mode for comprehensive topic exploration
- [ ] Related passages suggestions

#### 2. Word Counting & Metrics
**High Priority:** Enable queries like "How many times does 'art' appear in the codification?"

Features to implement:
- [ ] Word frequency counter across all books
- [ ] Phrase/concept frequency analysis
- [ ] Concordance tool (show all contexts where word appears)
- [ ] Comparative metrics between books
- [ ] Timeline of term usage (by book publication year)
- [ ] Export word statistics to CSV/charts

**Technical Approach:**
- Build inverted index during document processing
- Store term positions in metadata
- Create dedicated `/metrics` API endpoint
- Add "Analytics" tab to frontend

#### 3. Advanced Search Features
- [ ] Exact quote search
- [ ] Filter by specific books
- [ ] Date range filtering (by book publication year)
- [ ] Advanced boolean queries (AND, OR, NOT)
- [ ] Semantic similarity search (find similar passages)

#### 4. User Experience Improvements
- [ ] Bookmarking favorite responses
- [ ] Share conversations (public links)
- [ ] Dark mode
- [ ] Mobile-responsive design
- [ ] Voice input/output
- [ ] PDF export of conversations

#### 5. Backend Enhancements
- [ ] Multi-user authentication
- [ ] User-specific conversation history
- [ ] Admin dashboard for monitoring
- [ ] Automatic book updates (when new editions available)
- [ ] A/B testing for model configurations
- [ ] Prometheus metrics integration

#### 6. Scalability
- [ ] Cloud GPU deployment (modal.com, runpod.io)
- [ ] Horizontal scaling for API servers
- [ ] Distributed vector database (Qdrant, Weaviate)
- [ ] CDN for static assets
- [ ] Load balancing

---

## Development Workflow

### Setting Up Backend

1. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

2. **Index books (if database/ doesn't exist):**
```bash
python process_books.py
```

3. **Start Ollama and pull models:**
```bash
ollama serve
ollama pull qwen2.5:7b
ollama pull llama3.2:3b
```

4. **Run backend server:**
```bash
python api_server.py
# or use start_backend.bat on Windows
```

5. **Expose via ngrok:**
```bash
ngrok http 8000
```

### Setting Up Frontend

1. **Install dependencies:**
```bash
cd frontend
pip install -r requirements.txt
```

2. **Configure API URL:**
Create `.streamlit/secrets.toml`:
```toml
API_URL = "https://your-ngrok-url.ngrok-free.app"
```

3. **Run locally:**
```bash
streamlit run app.py
# Feedback dashboard:
streamlit run app_feedbacks.py
```

4. **Deploy to Streamlit Cloud:**
- Push to GitHub
- Connect repository to Streamlit Cloud
- Add `API_URL` to secrets in Streamlit Cloud dashboard

### GPU Diagnostics

```bash
python check_gpu.py
```
Shows: CUDA availability, GPU name, memory, PyTorch info

---

## Configuration

### Backend (config.py)

**Book Priorities:**
```python
BOOK_PRIORITIES = {
    "livro-dos-espiritos": 100,
    "evangelho": 70,
    "livro-dos-mediuns": 70,
    "genese": 70,
    "ceu-e-inferno": 70,
    "o-que-e-o-espiritismo": 70,
    "revista_espirita": 40
}
```

**Display Names:**
Maps technical filenames to user-friendly names with emoji icons.

### Frontend Parameters

**User-adjustable settings:**
- **Temperature:** 0.0-1.0 (controls creativity; 0.2 recommended for accuracy)
- **Top-K:** 1-10 (number of source chunks to use)
- **Fetch-K:** 20-50 (initial search breadth, advanced)
- **Enable Preview:** Toggle dual-model preview mode

---

## Data Storage Formats

### Conversations (JSON)
```json
{
  "conversation_id": "uuid",
  "user_id": "username",
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp",
  "messages": [
    {
      "role": "user|assistant",
      "content": "...",
      "timestamp": "...",
      "sources": [...],
      "preview_answer": "...",
      "validation_notes": "..."
    }
  ]
}
```

### Feedback (JSONL)
```jsonl
{"timestamp": "...", "question": "...", "answer": "...", "rating": "good", "comment": "...", "sources": [...]}
```

### Vector Store (ChromaDB)
- **Chunk Size:** 1000 characters
- **Overlap:** 200 characters
- **Metadata:** source filename, page number, priority
- **Embedding Dim:** 768 (multilingual-mpnet)

---

## Performance Benchmarks

### Response Times (with cache miss)
- **Preview Answer:** ~1-2 seconds
- **Final Answer:** ~3-4 seconds
- **Total (preview mode):** ~5-6 seconds
- **Cache Hit:** <100ms

### Database Stats
- **Total Chunks:** ~15,000-20,000 (estimated)
- **Database Size:** 253 MB
- **Indexing Time:** ~10-15 minutes (one-time)

### Model Sizes
- **Qwen2.5:7b:** ~4.7 GB
- **Llama3.2:3b:** ~2 GB
- **Embedding Model:** ~420 MB

---

## Testing Period

**Duration:** 19/01/2026 - 14/02/2026
**Operating Hours:** Monday-Friday, 10h-23h (while backend is active)
**User Testing:** Collaborative feedback collection via inline ratings

---

## Key Files & Modules

### Backend Core
- **[api_server.py](backend/api_server.py):** Main FastAPI server with endpoints
- **[priority_retriever.py](backend/priority_retriever.py):** RAG logic with prioritization
- **[config.py](backend/config.py):** Book priorities and display names
- **[process_books.py](backend/process_books.py):** PDF/DOCX indexing pipeline
- **[feedback_system.py](backend/feedback_system.py):** JSONL feedback storage

### Frontend Core
- **[app.py](frontend/app.py):** Main Streamlit chat interface (22KB)
- **[app_feedbacks.py](frontend/app_feedbacks.py):** Feedback analytics dashboard (13KB)
- **[chat_history.py](frontend/chat_history.py):** Conversation persistence (7KB)
- **[feedback_system.py](frontend/feedback_system.py):** Frontend feedback module

### Configuration Files
- **[requirements.txt](backend/requirements.txt):** Backend Python dependencies
- **[requirements.txt](frontend/requirements.txt):** Frontend Python dependencies
- **[.streamlit/secrets.toml](frontend/.streamlit/secrets.toml):** API URL and secrets
- **[.devcontainer/devcontainer.json](.devcontainer/devcontainer.json):** VS Code dev container config

---

## Notable Design Decisions

### Why Two Models?
- **Fast Preview:** Gives immediate feedback to users (better UX)
- **Quality Validation:** Ensures accuracy with RAG sources
- **Transparency:** Users see validation notes (what changed and why)

### Why Priority System?
- **O Livro dos Espíritos** is the foundational text in Spiritism
- Ensures most authoritative sources appear first
- Helps handle cases where multiple books discuss the same topic

### Why ChromaDB?
- Lightweight and fast
- No external server required
- Good for MVP/local deployment
- Easy migration path to cloud alternatives (Qdrant, Weaviate)

### Why JSONL for Feedback?
- Append-only (no lock conflicts)
- Easy to parse and stream
- Human-readable for debugging
- Simple backup and migration

---

## Common Tasks

### Add a New Book
1. Place PDF in `backend/books/`
2. Add priority to `config.py:BOOK_PRIORITIES`
3. Add display name to `config.py:BOOK_DISPLAY_NAMES`
4. Delete `backend/database/` folder
5. Run `python backend/process_books.py`

### Clear Cache
```python
# In api_server.py, restart server or:
response_cache.clear()
```

### Reset Conversations
Delete: `frontend/chat_history/conversations.json`

### Export All Feedback
```bash
# Backend stores at: backend/feedback/feedback.jsonl
# Can be opened with any text editor or imported to pandas
```

### Check GPU Status
```bash
python backend/check_gpu.py
```

---

## Troubleshooting

### Backend won't start
- Check if Ollama is running: `ollama list`
- Verify models are pulled: `ollama pull qwen2.5:7b`
- Check GPU: `python check_gpu.py`
- Check port 8000 isn't in use

### Frontend can't connect
- Verify ngrok tunnel is active
- Check `API_URL` in secrets.toml
- Test backend health: `curl http://localhost:8000/health`

### Slow responses
- Check cache hit rate in `/status`
- Reduce `fetch_k` parameter
- Lower `temperature`
- Verify GPU is being used (check logs)

### Out of memory (GPU)
- Restart Ollama
- Reduce batch sizes in `process_books.py`
- Use CPU fallback (slower but works)

---

## Security Considerations

### Current State (MVP)
⚠️ **No authentication** - anyone with URL can access
⚠️ **No rate limiting** on frontend (only backend: 15 req/min)
⚠️ **No input sanitization** - relies on LLM to handle
⚠️ **Ngrok tunnel** - public URL to local machine

### Recommended for Production
- [ ] Add user authentication (OAuth, JWT)
- [ ] Input validation and sanitization
- [ ] Rate limiting per user
- [ ] HTTPS everywhere
- [ ] API key rotation
- [ ] Cloud deployment (remove ngrok dependency)
- [ ] Monitoring and alerting
- [ ] Backup strategy for database and feedback

---

## Performance Tuning

### For Faster Responses
- Increase cache size (currently 500)
- Use smaller models (sacrifice quality)
- Reduce `top_k` (fewer sources)
- Disable preview mode (only final answer)
- Pre-warm cache with common questions

### For Better Quality
- Increase `fetch_k` (broader search)
- Increase `top_k` (more sources)
- Lower `temperature` (more deterministic)
- Use larger quality model (e.g., qwen2.5:14b)
- Fine-tune embedding model on Spiritist texts

### For Lower Resource Usage
- Use CPU-only mode
- Smaller embedding model
- Reduce chunk overlap
- Decrease batch sizes
- Use quantized models (Q4, Q5)

---

## Contributing

### Code Style
- Python: Follow PEP 8
- Type hints where applicable
- Docstrings for functions
- Comments for complex logic

### Git Workflow
- Main branch: `main`
- Feature branches: `feature/feature-name`
- Commit messages: Descriptive and concise

### Testing
- Test locally before committing
- Verify both frontend apps work
- Check backend health endpoint
- Test with various queries

---

## Contact & Support

**Testing Period:** 19/01/2026 - 14/02/2026
**Feedback:** Use in-app feedback system (👍😐👎)
**Issues:** Report via feedback dashboard or directly to maintainer

---

## License & Acknowledgments

### Books
All books are works of **Allan Kardec**, foundational texts of Spiritism (public domain).

### Technologies
- Anthropic (Claude Code)
- Meta (Llama models)
- Alibaba (Qwen models)
- LangChain, ChromaDB, Streamlit, FastAPI communities

---

## Version History

**Current Version:** MVP v1.0 (January 2026)
- Dual-model architecture (preview + validation)
- 18 books indexed
- Priority-based RAG retrieval
- Feedback system with analytics
- Streamlit Cloud deployment

---

*Last Updated: 2026-01-20*
