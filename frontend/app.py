import streamlit as st
import requests
from feedback_system import save_feedback, get_feedback_stats
import os

# Page configuration
st.set_page_config(
    page_title="Assistente Espírita",
    page_icon="📚",
    layout="wide"
)

# API Configuration - Try secrets first, then env, then default
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def check_api_status():
    """Check if API is online"""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.json()
    except Exception as e:
        return None

def query_api(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int):
    """Send query to API"""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={
                "question": question,
                "model_name": model_name,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k
            },
            timeout=120  # 2 minutes timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: A resposta demorou muito. Tente novamente.")
    except requests.exceptions.ConnectionError:
        raise Exception("🔌 Erro de conexão: Verifique se o backend está rodando.")
    except Exception as e:
        raise Exception(f"❌ Erro: {str(e)}")

def main():
    st.title("📚 Assistente Espírita")
    st.markdown("Faça perguntas sobre Espiritismo baseadas nas obras da Codificação")
    
    # Check API status
    api_status = check_api_status()
    
    # Sidebar
    with st.sidebar:
        st.header("🌐 Status do Backend")
        
        if api_status:
            st.success("✅ Backend Online")
            if api_status.get('cuda_available'):
                st.info(f"🎮 {api_status.get('gpu', 'GPU')}")
            else:
                st.warning("💻 CPU Mode")
            
            if not api_status.get('vectorstore_loaded'):
                st.error("⚠️ Banco de dados não carregado")
        else:
            st.error("❌ Backend Offline")
            st.code(f"API URL: {API_URL}")
            st.info("💡 Verifique se o backend está rodando")
        
        st.markdown("---")
        
        st.header("👤 Identificação")
        user_name = st.text_input(
            "Seu nome (opcional):",
            value="",
            placeholder="Ex: João Silva",
            help="Seu nome será usado para identificar seus feedbacks e ajudar a melhorar o assistente"
        )
        
        if not user_name:
            user_name = "Anônimo"
        
        st.markdown("---")
        
        st.header("⚙️ Configurações do Modelo")
        
        st.markdown("**Modelo:** *qwen2.5:7b*")
        st.caption("Modelo otimizado para português e respostas fiéis aos textos")
        
        temperature = st.slider(
            "Temperatura:",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="**Temperatura** controla a criatividade das respostas:\n\n"
                 "• **Baixa (0.1-0.3)**: Respostas mais objetivas e fiéis ao texto\n"
                 "• **Média (0.3-0.5)**: Equilíbrio entre fidelidade e reflexão\n"
                 "• **Alta (0.5-1.0)**: Respostas mais elaboradas e reflexivas\n\n"
                 "**Recomendado**: 0.3 para máxima fidelidade aos livros"
        )
        
        top_k = st.slider(
            "Nº de trechos:",
            min_value=3,
            max_value=15,
            value=8,
            step=1,
            help="**Número de trechos** define quantos excertos dos livros serão usados para responder:\n\n"
                 "• **Menos trechos (3-5)**: Respostas mais diretas e focadas\n"
                 "• **Mais trechos (8-12)**: Respostas com mais correlações e contexto\n\n"
                 "**Recomendado**: 8 trechos para bom equilíbrio"
        )
        
        with st.expander("⚙️ Configurações Avançadas"):
            fetch_k = st.slider(
                "Busca inicial:",
                min_value=top_k,
                max_value=50,
                value=20,
                step=5,
                help="**Busca inicial** determina quantos trechos são buscados antes da priorização:\n\n"
                     "• Quanto maior, mais chance de encontrar trechos de O Livro dos Espíritos\n"
                     "• Depois da busca, os trechos são reordenados por prioridade\n"
                     "• Os melhores são selecionados (quantidade definida em 'Nº de trechos')\n\n"
                     "**Recomendado**: 20 para boa cobertura"
            )
        
        st.markdown("---")
        
        st.header("📖 Hierarquia de Fontes")
        st.markdown("""
        O sistema prioriza as fontes nesta ordem:
        
        **🥇 Prioridade Máxima:**  
        • O Livro dos Espíritos
        
        **🥈 Obras Fundamentais:**  
        • O Evangelho Segundo o Espiritismo  
        • O Livro dos Médiuns  
        • A Gênese  
        • O Céu e o Inferno  
        • O que é o Espiritismo
        
        **🥉 Complementar:**  
        • Revistas Espíritas (1858-1869)
        """)
        
        st.markdown("---")
        
        st.header("💡 Como Usar")
        st.markdown("""
        **Para melhores resultados:**
        
        ✅ Faça perguntas claras e específicas  
        ✅ Verifique sempre as fontes citadas  
        ✅ Compare com os livros originais  
        ✅ Deixe feedback sobre as respostas
        
        **Exemplos de perguntas:**
        • O que é o perispírito?
        • O que o Espiritismo diz sobre o suicídio?
        • Qual a diferença entre médium e sensitivo?
        """)
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            if "sources" in message and message["sources"]:
                with st.expander("📖 Fontes Consultadas"):
                    for i, source in enumerate(message["sources"], 1):
                        icons = {
                            "PRIORIDADE MÁXIMA": "🥇",
                            "OBRA FUNDAMENTAL": "🥈",
                            "COMPLEMENTAR": "🥉",
                            "OUTRAS OBRAS": "📄"
                        }
                        
                        icon = icons.get(source['priority_label'], "📄")
                        
                        st.markdown(f"**{icon} Fonte {i}:** {source['priority_label']}")
                        st.text(source['content'][:500] + "...")
                        st.markdown(f"*{source['display_name']} | Pág: {source['page']}*")
                        st.markdown("---")
            
            # Feedback
            if message["role"] == "assistant" and "feedback_given" not in message:
                st.markdown("---")
                st.markdown("**📝 Esta resposta foi útil?**")
                st.caption("Seu feedback nos ajuda a melhorar o assistente")
                
                feedback_key = f"feedback_{idx}"
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👍 Boa", key=f"good_{idx}", use_container_width=True, 
                                help="Resposta correta, bem citada e coerente"):
                        st.session_state[feedback_key] = "good"
                
                with col2:
                    if st.button("😐 Regular", key=f"neutral_{idx}", use_container_width=True,
                                help="Resposta aceitável mas pode melhorar"):
                        st.session_state[feedback_key] = "neutral"
                
                with col3:
                    if st.button("👎 Ruim", key=f"bad_{idx}", use_container_width=True,
                                help="Resposta incorreta, mal citada ou confusa"):
                        st.session_state[feedback_key] = "bad"
                
                if feedback_key in st.session_state:
                    rating = st.session_state[feedback_key]
                    
                    comment = st.text_area(
                        "Comentário (opcional, mas muito valioso!):",
                        placeholder="Exemplos:\n• 'Faltou citar O Livro dos Espíritos'\n• 'Excelente correlação entre as obras'\n• 'Erros de português no segundo parágrafo'\n• 'Não respondeu exatamente o que foi perguntado'",
                        key=f"comment_{idx}",
                        height=100,
                        help="Comentários detalhados nos ajudam a identificar problemas específicos e melhorar o sistema"
                    )
                    
                    if st.button("✅ Enviar Feedback", key=f"submit_{idx}"):
                        user_msg_idx = idx - 1
                        question = st.session_state.messages[user_msg_idx]["content"] if user_msg_idx >= 0 else ""
                        
                        save_feedback(
                            question=question,
                            answer=message["content"],
                            sources=[s['content'][:200] for s in message.get("sources", [])],
                            keywords=[],
                            rating=rating,
                            comment=comment,
                            user_name=user_name
                        )
                        
                        st.session_state.messages[idx]["feedback_given"] = True
                        st.success("✅ Obrigado pelo feedback!")
                        st.rerun()
    
    # User input
    if prompt := st.chat_input("Digite sua pergunta sobre Espiritismo..."):
        if not api_status:
            st.error("❌ Backend offline. Não é possível processar perguntas.")
            st.info("💡 Verifique se o servidor backend está rodando em segundo plano")
            return
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🔍 Consultando os livros espíritas..."):
                try:
                    result = query_api(prompt, "qwen2.5:7b", temperature, top_k, fetch_k)
                    
                    answer = result['answer']
                    sources = result['sources']
                    
                    st.markdown(answer)
                    
                    if sources:
                        with st.expander("📖 Fontes Consultadas (ordenadas por prioridade)"):
                            for i, source in enumerate(sources, 1):
                                icons = {
                                    "PRIORIDADE MÁXIMA": "🥇",
                                    "OBRA FUNDAMENTAL": "🥈",
                                    "COMPLEMENTAR": "🥉",
                                    "OUTRAS OBRAS": "📄"
                                }
                                
                                icon = icons.get(source['priority_label'], "📄")
                                
                                st.markdown(f"**{icon} Fonte {i}:** {source['priority_label']}")
                                st.text(source['content'][:500] + "...")
                                st.markdown(f"*{source['display_name']} | Pág: {source['page']}*")
                                st.markdown("---")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(str(e))

if __name__ == "__main__":
    main()