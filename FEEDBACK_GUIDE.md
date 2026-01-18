# 📚 Guia para Testadores - Assistente Espírita

Bem-vindo! Você foi convidado para testar o Assistente Espírita, um sistema inteligente que responde perguntas sobre Espiritismo baseado nas obras da Codificação.

## 🎯 Objetivo do Teste

Ajudar a melhorar o assistente identificando:
- ✅ Respostas corretas e bem fundamentadas
- ❌ Erros de português ou conceituais
- ⚠️ Problemas na citação de fontes
- 💡 Oportunidades de melhoria

## 🚀 Como Acessar

### Link do Assistente
**https://chatbot-comeerj.streamlit.app/**

**Disponível**: Segunda a Sexta, 10h às 23h (enquanto o backend estiver rodando)

## 📖 Como Usar

### 1. **Acessar o Site**
- Clique no link fornecido
- Aguarde carregar (pode demorar ~10 segundos na primeira vez)

### 2. **Verificar Status**
Na barra lateral esquerda, veja:
- ✅ **Backend Online** = Tudo funcionando!
- ❌ **Backend Offline** = Aguarde ou avise o administrador

### 3. **Identificar-se (Opcional)**
- Digite seu nome na barra lateral
- Isso ajuda a identificar seu feedback

### 4. **Fazer Perguntas**
Digite sua pergunta na caixa de texto na parte inferior da tela.

**Exemplos de boas perguntas:**
```
✅ O que é o perispírito?
✅ O que o Espiritismo diz sobre o suicídio?
✅ Qual a diferença entre médium e sensitivo?
✅ Como funciona a reencarnação segundo Allan Kardec?
✅ O que são os Espíritos errantes?
```

**Evite perguntas muito vagas:**
```
❌ Me fale sobre Espiritismo
❌ O que Allan Kardec disse?
❌ Explique tudo sobre mediunidade
```

### 5. **Ler a Resposta**
O assistente vai:
- Buscar informações nos livros espíritas
- Priorizar O Livro dos Espíritos
- Citar as fontes utilizadas

### 6. **Verificar as Fontes**
Clique em **"📖 Fontes Consultadas"** para ver:
- 🥇 = O Livro dos Espíritos (prioridade máxima)
- 🥈 = Obras fundamentais (Evangelho, Médiuns, etc)
- 🥉 = Revista Espírita
- Página do livro onde foi encontrado

## ⭐ Como Avaliar (MUITO IMPORTANTE!)

Após cada resposta, você verá três botões:

### 👍 **BOA RESPOSTA**
Use quando:
- ✅ Português correto e fluente
- ✅ Citou os livros espíritas corretamente
- ✅ Resposta coerente e completa
- ✅ Fez boas correlações entre conceitos
- ✅ Priorizou O Livro dos Espíritos quando relevante

### 😐 **REGULAR**
Use quando:
- ⚠️ Resposta correta mas incompleta
- ⚠️ Português aceitável mas pode melhorar
- ⚠️ Faltou citar algumas fontes
- ⚠️ Poderia ter mais detalhes

### 👎 **RUIM**
Use quando:
- ❌ Erros de português (concordância, conjugação)
- ❌ Não citou as fontes corretamente
- ❌ Resposta confusa ou incoerente
- ❌ Priorizou obra errada (ex: usou Revista quando tinha no LE)
- ❌ Inventou informações não presentes nos livros

## 💬 Deixar Comentários (ESSENCIAL!)

**Por favor, SEMPRE deixe um comentário explicando sua avaliação!**

### Exemplos de BONS comentários:

**Para respostas boas:**
```
✅ "Excelente! Citou O Livro dos Espíritos questão 150 e fez boa correlação com O Evangelho"
✅ "Perfeito. Resposta objetiva e bem fundamentada"
✅ "Ótimo português e citações precisas"
```

**Para respostas regulares:**
```
⚠️ "Resposta correta mas faltou citar o capítulo do livro"
⚠️ "Poderia ter usado mais trechos de O Livro dos Espíritos"
⚠️ "Português bom mas frase muito longa no segundo parágrafo"
```

**Para respostas ruins:**
```
❌ "Erro de concordância: escreveu 'os espírito' em vez de 'os espíritos'"
❌ "Usou principalmente a Revista Espírita quando a resposta está no LE questão 93"
❌ "Não citou nenhuma fonte específica, só disse 'segundo o Espiritismo'"
❌ "Resposta não condiz com o que está no livro. Questão 150 fala sobre X e não Y"
```

## 🎯 O Que Procurar Especificamente

### 1. **Priorização Correta**
O sistema deve priorizar nesta ordem:
1. 🥇 O Livro dos Espíritos
2. 🥈 Obras fundamentais
3. 🥉 Revista Espírita

**Avalie se:**
- Quando a resposta está no LE, ele foi usado?
- Ou o sistema usou outras fontes desnecessariamente?

### 2. **Citações Precisas**
**Avalie se:**
- O assistente citou o livro, capítulo ou questão?
- Exemplo bom: "Segundo O Livro dos Espíritos, questão 150..."
- Exemplo ruim: "De acordo com Allan Kardec..." (sem citar obra)

### 3. **Qualidade do Português**
**Procure:**
- ✅ Frases claras e bem estruturadas
- ❌ Erros de concordância
- ❌ Conjugação verbal errada
- ❌ Frases confusas ou truncadas

### 4. **Fidelidade ao Texto**
**Avalie se:**
- A resposta corresponde ao que está nos livros?
- Ou o assistente "inventou" coisas?
- Clique em "Ver Fontes" e compare com a resposta

### 5. **Correlações**
**O assistente deve:**
- Conectar conceitos de diferentes obras quando relevante
- Exemplo: explicar perispírito citando LE + Gênese + Médiuns

## 📊 Configurações (Avançado)

Na barra lateral, você pode ajustar:

### **Temperatura** (0.0 - 1.0)
- **Baixa (0.1-0.3)**: Respostas mais objetivas e fiéis
- **Alta (0.5-1.0)**: Respostas mais elaboradas
- **Teste**: Faça a mesma pergunta com diferentes temperaturas!

### **Nº de trechos** (3-15)
- **Poucos (3-5)**: Respostas mais diretas
- **Muitos (10-15)**: Mais contexto e correlações
- **Teste**: Veja como muda a resposta!

## 🐛 Problemas Comuns

### "Backend Offline"
- O servidor backend não está rodando
- Aguarde alguns minutos ou avise o administrador
- Normal nos finais de semana ou após 23h

### Resposta muito lenta
- Normal para perguntas complexas (até 30 segundos)
- Se demorar mais de 1 minuto, recarregue a página

### Erro de conexão
- Verifique sua internet
- Recarregue a página (F5)

## ✅ Checklist de Teste

Para cada sessão de teste, tente:

- [ ] Fazer pelo menos **5 perguntas diferentes**
- [ ] Avaliar **todas as respostas** (👍😐👎)
- [ ] Deixar **comentários detalhados** em cada avaliação
- [ ] Testar perguntas sobre **diferentes temas**:
  - [ ] Natureza dos Espíritos
  - [ ] Reencarnação
  - [ ] Mediunidade
  - [ ] Lei de causa e efeito
  - [ ] Vida após a morte
- [ ] Verificar se as **fontes estão corretas**
- [ ] Testar **diferentes temperaturas** (opcional)
- [ ] Anotar qualquer **comportamento estranho**

## 📝 Exemplos de Perguntas Para Testar

### Básicas (para começar):
```
1. O que é Espiritismo?
2. Quem foi Allan Kardec?
3. O que é o perispírito?
4. Quantos tipos de médiuns existem?
```

### Intermediárias:
```
1. Como funciona a reencarnação?
2. Por que os Espíritos se comunicam?
3. O que são Espíritos errantes?
4. Qual o papel do livre-arbítrio?
```

### Avançadas (para testar correlações):
```
1. Qual a relação entre perispírito e mediunidade?
2. Como a lei de causa e efeito se relaciona com a reencarnação?
3. O que Allan Kardec diz sobre suicídio e suas consequências no mundo espiritual?
4. Explique a diferença entre médium de efeitos físicos e médium psicógrafo
```

### Para testar priorização:
```
1. O que é a alma? (deve priorizar LE)
2. Existe Deus? (deve priorizar LE)
3. O que acontece após a morte? (deve priorizar LE + Céu e Inferno)
```

## 🎁 Sua Contribuição É Valiosa!

Cada avaliação e comentário que você deixa ajuda a:
- ✅ Identificar problemas no sistema
- ✅ Melhorar a qualidade das respostas
- ✅ Ajustar a priorização de fontes
- ✅ Corrigir erros de português
- ✅ Beneficiar futuros usuários

## 📧 Dúvidas ou Problemas?

Se encontrar algo que não consegue resolver:
1. Anote o que aconteceu
2. Tire um print (se possível)
3. Mande para o administrador

## 🙏 Agradecimento

Obrigado por dedicar seu tempo para testar e melhorar o Assistente Espírita!

Seu feedback é essencial para criar uma ferramenta útil para o estudo da Doutrina Espírita.

---

**Período de Teste**: 19/01/2026 até 14/02/2026
**Horário**: Segunda a Sexta, 10h às 23h  

---

## 📋 Resumo Rápido

1. ✅ Acesse o link
2. ✅ Digite seu nome (opcional)
3. ✅ Faça perguntas sobre Espiritismo
4. ✅ Leia as respostas
5. ✅ Verifique as fontes
6. ✅ Avalie: 👍 😐 ou 👎
7. ✅ **DEIXE COMENTÁRIOS DETALHADOS!**
8. ✅ Repita!

**Quanto mais feedback, melhor o sistema fica! 🚀**