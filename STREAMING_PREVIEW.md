# Streaming Preview Implementation

## Overview

I've implemented a **streaming response system** that shows the preview answer FIRST, then displays the final validated answer. This creates a much better user experience where users see an immediate response while the system searches the books in the background.

---

## What Changed

### Backend Changes ([api_server.py](backend/api_server.py))

#### 1. New Streaming Endpoint: `/query/stream` (Lines 388-518)

This endpoint uses **Server-Sent Events (SSE)** to stream responses in real-time:

**Event Flow:**
```
1. event: preview
   → Sends quick answer from fast model (llama3.2:3b)
   → User sees this IMMEDIATELY (~1-2 seconds)

2. event: sources
   → Sends list of sources found in books
   → Shows user "📚 X fontes encontradas"

3. event: answer
   → Sends final validated answer from quality model (qwen2.5:7b)
   → Includes validation notes

4. event: done
   → Processing complete
```

**Key Features:**
- Preview is generated and sent immediately
- While preview displays, book search runs in parallel
- Final answer validates preview with book sources
- Users don't wait for everything to complete before seeing something

#### 2. Updated Preview Prompt (Lines 249-272)

Added instruction #5:
```
5. Se você NÃO tiver certeza ou conhecimento suficiente, responda:
   "Preciso consultar os livros da Codificação para responder com precisão."
```

**Why this matters:**
- If the model doesn't know something, it admits it
- Encourages users to trust the validated answer more
- Makes the preview more honest and transparent

#### 3. Context-Aware Instructions

Both preview and validation prompts now include:
- "Responda APENAS a pergunta atual"
- "Use o histórico APENAS se houver referência direta"
- "Se a pergunta for nova e independente, IGNORE o histórico"

This prevents the model from re-answering previous questions.

---

### Frontend Changes ([app.py](frontend/app.py))

#### 1. New Streaming Function: `query_api_stream()` (Lines 201-245)

Handles SSE parsing from the backend:
- Connects to `/query/stream` endpoint
- Parses event types and data
- Yields events as they arrive
- Compatible with `for` loops

#### 2. Streaming Display Logic (Lines 604-736)

**When Preview is Enabled:**
```python
# Show preview immediately
preview_placeholder.container()
  → "💭 Resposta inicial: [preview]"
  → "Aguarde... consultando os livros"

# Show sources found
sources_placeholder.container()
  → "📚 X fontes encontradas nos livros"

# Replace with final answer
answer_placeholder.container()
  → "💭 Resposta inicial: [preview]"
  → "✅ Resposta fundamentada: [final answer]"
  → "🔍 Processo de validação: [notes]"
```

**When Preview is Disabled:**
- Falls back to non-streaming `/query` endpoint
- Shows spinner while waiting
- Displays final answer only

---

## User Experience Flow

### Before (Non-Streaming)
```
User asks question
   ↓
[Spinner: "🔍 Consultando os livros espíritas..."]
   ↓ (wait 5-6 seconds)
   ↓
Shows preview + final answer together
```

### After (Streaming)
```
User asks question
   ↓
💭 Preview appears (~1-2s)
"Aguarde... consultando os livros"
   ↓
📚 "5 fontes encontradas nos livros"
   ↓
✅ Final answer replaces preview (~3-4s more)
Shows validation notes
```

**Benefits:**
1. **Faster perceived response** - Users see something immediately
2. **Progressive disclosure** - Information appears as it's ready
3. **Transparency** - Users see the process happening
4. **Better trust** - Preview admits when it doesn't know something

---

## API Endpoints

### Streaming Endpoint (New)
```http
POST /query/stream
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

**Response (SSE format):**
```
event: preview
data: {"answer": "O perispírito é...", "task_id": "task_123"}

event: sources
data: {"sources": [...], "count": 5}

event: answer
data: {"answer": "Validated answer...", "validation_notes": "...", "processing_time": 4.2}

event: done
data: {"task_id": "task_123", "total_time": 4.2}
```

### Non-Streaming Endpoint (Existing)
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

**Response (JSON):**
```json
{
  "task_id": "task_123",
  "answer": "Final answer...",
  "sources": [...],
  "processing_time": 4.2,
  "has_preview": true,
  "preview_answer": "Preview answer...",
  "validation_notes": "..."
}
```

---

## Preview Honesty Feature

The preview model now has instruction to admit when it doesn't know:

**Example 1 - Model knows the answer:**
```
Question: "O que é o perispírito?"
Preview: "O perispírito é o envoltório semimaterial que liga o espírito ao corpo físico..."
```

**Example 2 - Model doesn't know:**
```
Question: "Quantas vezes a palavra 'caridade' aparece no Livro dos Espíritos?"
Preview: "Preciso consultar os livros da Codificação para responder com precisão."
Final: [Actual answer from searching the books]
```

This makes users understand the difference between:
- **General knowledge answer** (preview)
- **Research-based answer** (validated)

---

## Technical Implementation Details

### Server-Sent Events (SSE)

SSE is a standard protocol for server-to-client streaming:

**Format:**
```
event: event_name
data: JSON payload

```

**Advantages:**
- Simpler than WebSockets
- Built-in reconnection
- Works over HTTP
- Firewall-friendly

**Browser Support:**
- All modern browsers
- Automatic buffering
- EventSource API

### Streamlit Placeholders

Uses `st.empty()` containers that can be updated:

```python
placeholder = st.empty()

# First update
with placeholder.container():
    st.markdown("Loading...")

# Second update (replaces first)
with placeholder.container():
    st.markdown("Done!")

# Clear it
placeholder.empty()
```

---

## Testing the Feature

### 1. Start Backend
```bash
cd backend
python api_server.py
```

### 2. Start Frontend
```bash
cd frontend
streamlit run app.py
```

### 3. Test Scenarios

**Scenario A - Independent Questions:**
```
Q1: "O que é mediunidade?"
→ Preview shows immediately
→ Final answer validates with sources

Q2: "O que é perispírito?"
→ Preview should NOT mention mediunidade
→ Treats as completely new question
```

**Scenario B - Follow-up Questions:**
```
Q1: "O que é mediunidade?"
→ Normal preview + validation

Q2: "Pode explicar melhor?"
→ Preview uses context to understand "melhor" refers to mediunidade
→ Expands on previous answer
```

**Scenario C - Model Doesn't Know:**
```
Q: "Quantas vezes 'esperança' aparece no Evangelho?"
→ Preview: "Preciso consultar os livros..."
→ Final: [Would need word counting feature to answer]
```

---

## Configuration

### Enable/Disable Preview Mode

In the Streamlit sidebar:
```python
enable_preview = st.checkbox("Ativar Preview", value=True)
```

- **Checked** → Uses streaming endpoint
- **Unchecked** → Uses regular endpoint (faster but no preview)

### Fallback Behavior

If streaming fails, the app automatically falls back to non-streaming mode.

---

## Performance Metrics

### Streaming Mode (Preview Enabled)
- **Time to first response:** ~1-2 seconds (preview)
- **Time to final response:** ~5-6 seconds (validation)
- **User sees something:** Immediately after preview
- **Total wait for final answer:** ~5-6 seconds

### Non-Streaming Mode (Preview Disabled)
- **Time to first response:** ~4-5 seconds
- **User sees something:** Only when complete
- **Total wait:** ~4-5 seconds

**Key Insight:** Streaming adds ~1 second total but reduces *perceived* wait time by 3-4 seconds.

---

## Future Enhancements

### 1. Progress Indicators
```
event: progress
data: {"stage": "searching", "percent": 50}
```

### 2. Partial Answer Streaming
Stream the final answer word-by-word as it's generated (like ChatGPT).

### 3. Source Previews
Show sources as they're found, before validation completes.

### 4. Confidence Scores
Include confidence in preview:
```
Preview: "Com confiança média, acredito que..."
```

### 5. Caching Integration
Cache preview answers separately from final answers.

---

## Troubleshooting

### Preview Not Showing
- Check if `enable_preview` is True
- Verify `/query/stream` endpoint is accessible
- Check browser console for SSE errors

### Streaming Connection Fails
- Falls back to `/query` automatically
- Check backend logs for errors
- Verify CORS settings

### Preview Repeats History
- Check conversation_context in prompt
- Verify model is following instructions
- Try adjusting temperature (lower = more deterministic)

---

## Summary

This implementation creates a **2-phase response system**:

1. **Phase 1 (Preview):** Fast, general knowledge answer (~1-2s)
   - Uses llama3.2:3b
   - Shows immediately
   - Admits when it doesn't know

2. **Phase 2 (Validation):** Research-backed answer (~3-4s)
   - Searches books in parallel
   - Uses qwen2.5:7b
   - Validates preview with sources
   - Shows what changed

**Result:** Users get instant feedback while maintaining accuracy through validation.

---

*Last Updated: 2026-01-20*
