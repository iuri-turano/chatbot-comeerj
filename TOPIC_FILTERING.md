# Topic Filtering - Rejecting Off-Topic Questions

## Overview

The system now **rejects questions that are not related to Spiritism**. This prevents the chatbot from answering questions about programming, general knowledge, or other topics outside its domain.

---

## How It Works

### 1. Preview Detection (Fast Model)

The preview prompt includes explicit instructions to reject off-topic questions:

```
IMPORTANTE: Você DEVE responder APENAS perguntas relacionadas a:
- Espiritismo e Doutrina Espírita
- Allan Kardec e a Codificação Espírita
- Temas espirituais, religião, filosofia relacionados ao Espiritismo
- Mediunidade, perispírito, reencarnação, evolução espiritual
- Moral, ética e ensinamentos dos Espíritos

Se a pergunta NÃO for relacionada a estes temas, responda EXATAMENTE:
"Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita.
Não posso responder perguntas sobre outros assuntos. Por favor, faça uma
pergunta relacionada ao Espiritismo."
```

### 2. Early Termination

When the preview contains the rejection message, the system:
- **Skips book search** (saves processing time)
- **Skips validation** (no need to validate rejection)
- **Returns immediately** with the rejection message

This happens in both endpoints:
- `/query/stream` - [Lines 451-460](backend/api_server.py#L451-L460)
- `/query` - [Lines 621-626](backend/api_server.py#L621-L626)

### 3. Validation Enforcement

If somehow an off-topic question passes the preview, the validation prompt has a backup check:

```
RESTRIÇÃO DE ESCOPO:
Se a resposta prévia indica que a pergunta está FORA DO ESCOPO do Espiritismo
(contém a mensagem "Desculpe, sou um assistente especializado..."), você DEVE:
1. Manter EXATAMENTE a mesma mensagem de rejeição
2. NÃO tentar responder a pergunta
3. NÃO adicionar notas de validação
4. Retornar apenas a mensagem de rejeição
```

---

## Examples

### ✅ Accepted Topics

**Spiritism Basics:**
```
Q: "O que é o perispírito?"
A: [Detailed answer about perispirit from the books]
```

**Mediumship:**
```
Q: "Como desenvolver a mediunidade?"
A: [Answer based on Livro dos Médiuns]
```

**Moral and Ethics:**
```
Q: "O que o Espiritismo ensina sobre caridade?"
A: [Answer from Evangelho segundo o Espiritismo]
```

**Allan Kardec:**
```
Q: "Quem foi Allan Kardec?"
A: [Biographical information and his role in Spiritism]
```

**Spiritual Evolution:**
```
Q: "Como funciona a reencarnação?"
A: [Detailed answer from Livro dos Espíritos]
```

### ❌ Rejected Topics

**Programming:**
```
Q: "Write a Python script to calculate is_odd and is_even"
Preview: "Desculpe, sou um assistente especializado em Espiritismo e
Doutrina Espírita. Não posso responder perguntas sobre outros assuntos.
Por favor, faça uma pergunta relacionada ao Espiritismo."

Final: [Same rejection message, no sources, no validation]
```

**General Knowledge:**
```
Q: "What is the capital of France?"
A: [Rejection message]
```

**Cooking:**
```
Q: "How do I make a cake?"
A: [Rejection message]
```

**Math:**
```
Q: "Solve the equation 2x + 5 = 15"
A: [Rejection message]
```

**Technology:**
```
Q: "How does artificial intelligence work?"
A: [Rejection message]
```

---

## Performance Benefits

### Before Topic Filtering
```
Off-topic question
  ↓
Generate preview (~1-2s)
  ↓
Search books (~1-2s) ← WASTED
  ↓
Validate with quality model (~3-4s) ← WASTED
  ↓
Return incorrect answer
```
**Total waste:** ~5-6 seconds + incorrect answer

### After Topic Filtering
```
Off-topic question
  ↓
Generate preview (~1-2s)
  ↓
Detect rejection message
  ↓
Return immediately
```
**Total time:** ~1-2 seconds + correct rejection

**Savings:**
- ⏱️ 70-80% faster response for off-topic questions
- 💰 No wasted LLM calls on validation
- 🔍 No unnecessary book searches
- ✅ Correct behavior (rejection instead of hallucination)

---

## Technical Implementation

### Detection Logic

The system checks for the rejection phrase in the preview:

```python
if "Desculpe, sou um assistente especializado" in preview_answer:
    # Question is off-topic, skip book search and validation
    final_answer = preview_answer
    validation_notes = None
    sources = []
```

This works because:
1. The rejection phrase is **unique and specific**
2. It's **unlikely to appear in valid answers**
3. It's **in Portuguese** (matching the system language)
4. It's **exact** (model is instructed to use this exact phrase)

### Streaming Endpoint Flow

```python
# FASE 1: Generate preview
preview_answer = await generate_preview(...)
yield preview_event

# Check for rejection
if "Desculpe, sou um assistente especializado" in preview_answer:
    yield answer_event  # Same as preview
    yield done_event
    return  # Early exit

# FASE 2: Search books (only if on-topic)
sources = await search_books_async(...)
yield sources_event

# FASE 3: Validate (only if on-topic)
validated_answer = await validate(...)
yield answer_event
yield done_event
```

### Regular Endpoint Flow

```python
# Execute preview and search in parallel
preview_answer, sources = await asyncio.gather(
    generate_preview(...),
    search_books_async(...)
)

# Check for rejection
if "Desculpe, sou um assistente especializado" in preview_answer:
    final_answer = preview_answer
    sources = []  # Clear sources
    validation_notes = None
else:
    # Continue with validation
    validated_answer = quality_llm.invoke(...)
    final_answer, validation_notes = extract_validation_notes(...)
```

---

## Edge Cases

### 1. Borderline Topics

Some topics might be borderline (e.g., "What is meditation?"):

**Strategy:** The model uses its judgment based on the instructions. Meditation in a spiritual/philosophical context might be accepted, while technical meditation apps would be rejected.

**User feedback:** If users report incorrect rejections, we can:
- Adjust the prompt to be more inclusive
- Add examples of borderline cases
- Fine-tune the model

### 2. Follow-up Questions

If the previous question was on-topic but the follow-up is off-topic:

```
Q1: "O que é mediunidade?"
A1: [Valid answer about mediumship]

Q2: "Can you write Python code for me?"
A2: [Rejection - treats as independent question]
```

The system correctly identifies Q2 as off-topic despite the conversation history.

### 3. Mixed Questions

Questions that mix Spiritism with off-topic content:

```
Q: "Compare mediunidade with Python programming"
```

**Expected behavior:** Rejection (Python programming is off-topic).

If this causes issues, we can adjust the prompt to:
- Answer only the Spiritism part
- Ignore the off-topic part

### 4. Language Switching

If a user asks in English:

```
Q: "What is the perispirit?"
```

**Expected behavior:** The model should understand and answer, as the question is about Spiritism (perispirit = perispírito).

The rejection phrase is in Portuguese, but the model should handle multilingual questions about Spiritism.

---

## Monitoring and Metrics

### Rejection Rate

Track how often questions are rejected:

```python
# In backend logs
if "Desculpe, sou um assistente especializado" in preview_answer:
    print(f"⚠️ Pergunta fora do escopo: {question[:50]}...")
```

**Expected rate:**
- Production users: ~5-10% (some users test boundaries)
- Abuse/spam: Higher rejection rate is good

### False Positives

Monitor user feedback for incorrectly rejected questions:
- User gives 👎 rating to rejection
- User comment: "This is about Spiritism!"

**Resolution:**
- Review the question
- Adjust prompt if pattern emerges
- Add examples to training data

### False Negatives

Monitor cases where off-topic questions are answered:
- Check validation notes
- Look for answers that don't cite books
- User reports irrelevant answers

**Resolution:**
- Strengthen rejection prompt
- Add more explicit examples
- Increase model temperature for preview (more consistent)

---

## Configuration

### Adjusting Strictness

To make the filter **more strict** (reject more):

```python
template = """...
IMPORTANTE: Você DEVE responder APENAS perguntas DIRETAMENTE relacionadas ao Espiritismo.
Qualquer pergunta que não seja EXPLICITAMENTE sobre a Doutrina Espírita deve ser rejeitada.
...
"""
```

To make the filter **more lenient** (accept more):

```python
template = """...
IMPORTANTE: Você pode responder perguntas sobre Espiritismo e temas RELACIONADOS, como:
- Filosofia espiritual
- Religiões comparadas (quando relevante para entender o Espiritismo)
- História das ideias espirituais
...
"""
```

### Custom Rejection Messages

You can customize the rejection message for different languages or tones:

**Formal:**
```
"Lamento, mas este assistente é especializado exclusivamente em Espiritismo
e Doutrina Espírita. Por gentileza, formule uma pergunta relacionada a estes temas."
```

**Friendly:**
```
"Opa! Sou especializado em Espiritismo 😊 Infelizmente não posso ajudar com
outras coisas. Tem alguma pergunta sobre a Doutrina Espírita?"
```

**Bilingual:**
```
"Desculpe / Sorry, I'm specialized in Spiritism. Please ask a question related
to Spiritism / Por favor, faça uma pergunta relacionada ao Espiritismo."
```

---

## Testing

### Unit Tests

Test rejection logic with sample questions:

```python
def test_programming_question_rejected():
    question = "Write a Python script to sort a list"
    preview = generate_preview(question)
    assert "Desculpe, sou um assistente especializado" in preview

def test_spiritism_question_accepted():
    question = "O que é o perispírito?"
    preview = generate_preview(question)
    assert "Desculpe, sou um assistente especializado" not in preview
```

### Integration Tests

Test end-to-end flow:

```python
def test_off_topic_skips_book_search():
    response = query_api("Write Python code")
    assert response['sources'] == []
    assert response['validation_notes'] is None
    assert "Desculpe" in response['answer']
```

### Manual Testing

Test with various off-topic questions:
- Programming (Python, JavaScript, etc.)
- Math (equations, calculus)
- Science (physics, chemistry)
- Current events (news, politics)
- Entertainment (movies, games)
- Cooking (recipes)
- Sports
- Shopping
- Travel

All should be rejected.

---

## Future Improvements

### 1. Category Classification

Instead of binary (accept/reject), classify into categories:

```python
categories = [
    "spiritism",          # Core topic
    "philosophy",         # Related
    "comparative_religion", # Related
    "programming",        # Off-topic
    "general_knowledge"   # Off-topic
]
```

### 2. Soft Rejection

For borderline cases, suggest related Spiritist topics:

```
Q: "What is meditation?"
A: "While I specialize in Spiritism, I can tell you about PRAYER and
SPIRITUAL ELEVATION in Spiritist practice, which shares similarities
with meditation. Would you like to know more?"
```

### 3. Topic Redirection

If the question is close to a Spiritist topic:

```
Q: "What happens when we die?"
A: "This is a fundamental question in Spiritism! According to the
Codification, when the physical body dies... [answer from books]"
```

### 4. Educational Rejection

Explain why the question was rejected and suggest alternatives:

```
Q: "Write Python code"
A: "I'm specialized in Spiritism and can't help with programming.
However, if you're interested in the spiritual aspects of technology
or the moral implications of AI, I'd be happy to discuss those from
a Spiritist perspective!"
```

---

## Summary

The topic filtering system:

✅ **Rejects off-topic questions** at the preview stage
✅ **Saves processing time** by skipping book search and validation
✅ **Provides clear feedback** to users about system scope
✅ **Maintains focus** on Spiritism and related topics
✅ **Prevents hallucinations** on topics outside the knowledge base
✅ **Improves user experience** by setting clear expectations

**Implementation files:**
- [backend/api_server.py](backend/api_server.py) - Preview and validation prompts
- Lines 255-263: Topic restrictions in preview prompt
- Lines 297-302: Scope enforcement in validation prompt
- Lines 451-460: Early termination in streaming endpoint
- Lines 621-626: Early termination in regular endpoint

---

*Last Updated: 2026-01-20*
