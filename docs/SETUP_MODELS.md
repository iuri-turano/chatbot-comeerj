# Model Setup Guide - OS-Specific Configuration

## 🎯 Automatic Model Selection

The system automatically selects the optimal model with **Chain-of-Thought reasoning**:

| OS | Hardware | Model | Features |
|----|----------|-------|----------|
| **macOS** | M4 16GB | `llama3.2:3b` | CoT reasoning, fits in 16GB RAM |
| **Windows** | RTX 3070 8GB + 32GB RAM | `llama3.1:8b` | CoT reasoning, GPU accelerated |

## 🧠 Chain-of-Thought Reasoning

All models now use enhanced reasoning that:
- Analyzes the question before answering
- Evaluates source priority and relevance
- Synthesizes information from multiple passages
- Verifies alignment with spiritist doctrine

This produces more thoughtful, well-structured answers.

## 📥 Installation Commands

### macOS (M4 16GB)
```bash
ollama pull llama3.2:3b
ollama pull llama3.2:1b  # Optional lightweight
```

### Windows (RTX 3070 8GB + 32GB RAM)
```bash
ollama pull llama3.1:8b
ollama pull llama3.2:3b  # Optional lighter alternative
```

## 🚀 Quick Start

Just run the startup script - it will detect your OS automatically:

**macOS**: `./start_all.sh`
**Windows**: `start_all.bat`

---

For detailed information, see the full documentation in the main README.
