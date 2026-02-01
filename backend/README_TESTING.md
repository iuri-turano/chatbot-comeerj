# Testing Context Validation

## How to Run Tests

### Prerequisites
1. Activate the virtual environment
2. Ensure all dependencies are installed

### Running the Test

**Windows:**
```bash
cd backend
venv\Scripts\activate
python test_context_validation.py
```

**Mac/Linux:**
```bash
cd backend
source venv/bin/activate
python test_context_validation.py
```

### Expected Results

The test validates 20 questions:
- 10 valid questions about Spiritism (should be accepted)
- 10 invalid questions off-topic (should be rejected)

**Success Criteria:**
- Accuracy >= 90%
- Valid questions precision >= 98%
- Invalid questions recall >= 95%

### Test Output Example

```
================================================================================
🧪 TESTANDO VALIDAÇÃO DE CONTEXTO
================================================================================

📊 Carregando modelo de embeddings...
✅ Embeddings carregados!

🔧 Criando validador de contexto...
🔍 Calculando embeddings dos tópicos espíritas...
✅ 20 tópicos espíritas indexados

================================================================================
✅ TESTANDO PERGUNTAS VÁLIDAS (devem passar)
================================================================================

✅ PASSOU [0.652] O que é o perispírito?
✅ PASSOU [0.689] Explique sobre reencarnação segundo Allan Kardec
✅ PASSOU [0.701] Como funciona a mediunidade?
...

📊 Resultado: 10/10 perguntas válidas aceitas (100.0%)

================================================================================
❌ TESTANDO PERGUNTAS INVÁLIDAS (devem ser rejeitadas)
================================================================================

✅ PASSOU [0.123] Qual a receita de bolo de chocolate?
✅ PASSOU [0.089] Quem ganhou a Copa do Mundo 2022?
...

📊 Resultado: 10/10 perguntas inválidas rejeitadas (100.0%)

================================================================================
📊 RESULTADO GERAL
================================================================================

✅ Perguntas válidas aceitas: 10/10 (100.0%)
❌ Perguntas inválidas rejeitadas: 10/10 (100.0%)

🎯 ACURÁCIA TOTAL: 20/20 (100.0%)

📈 MÉTRICAS:
   - Precision (válidas aceitas): 100.0%
   - Recall (inválidas rejeitadas): 100.0%
   - Threshold usado: 0.35

✅ TESTE PASSOU! Acurácia >= 90%
```

### Adjusting the Threshold

If tests fail, you can adjust the validation threshold in `config.py`:

```python
# More permissive (accepts more questions)
CONTEXT_VALIDATION_THRESHOLD = 0.30

# More restrictive (rejects more questions)
CONTEXT_VALIDATION_THRESHOLD = 0.40
```

**Recommended:** 0.35 (balanced)

### Manual Testing via API

You can also test via the API once the backend is running:

```bash
# Valid question (should get answer)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "O que é reencarnação?",
    "model_name": "qwen2.5:7b",
    "temperature": 0.3,
    "top_k": 3,
    "fetch_k": 15
  }'

# Invalid question (should get rejection message)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Qual a receita de bolo de chocolate?",
    "model_name": "qwen2.5:7b",
    "temperature": 0.3,
    "top_k": 3,
    "fetch_k": 15
  }'
```

Expected response for invalid question:
```json
{
  "task_id": "rejected",
  "answer": "Desculpe, sou um assistente especializado em Espiritismo e Doutrina Espírita...",
  "sources": [],
  "processing_time": 0.0
}
```
