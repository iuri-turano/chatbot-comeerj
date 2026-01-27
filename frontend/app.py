import streamlit as st
import requests
import json
from chat_history import (
    save_conversation,
    load_conversation,
    get_recent_conversations,
    generate_chat_id,
    export_conversation_to_text,
    delete_conversation
)
import os
import time

# Page configuration
st.set_page_config(
    page_title="Assistente Espírita",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import theme system
from themes import THEMES, get_theme_css

# Initialize theme in session state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# Inject theme CSS (replaces old hardcoded CSS)
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# Old CSS below is now replaced by theme system (commented out)
# CSS is now managed by themes.py and injected above

# API Configuration
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def check_api_status():
    """Check if API is online"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.json()
    except Exception as e:
        return None

def save_feedback_via_api(question: str, answer: str, sources: list, rating: str, comment: str, user_name: str):
    """Save feedback via API instead of locally"""
    try:
        response = requests.post(
            f"{API_URL}/feedback",
            json={
                "question": question,
                "answer": answer,
                "sources": sources,
                "keywords": [],
                "rating": rating,
                "comment": comment,
                "user_name": user_name
            },
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        raise Exception(f"Erro ao salvar feedback: {str(e)}")

def query_api_stream(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None, enable_preview: bool = True):
    """Send query to streaming API - yields preview, sources, and final answer"""
    try:
        # Prepare conversation history (exclude sources for API call)
        api_history = []
        if conversation_history:
            for msg in conversation_history:
                api_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = requests.post(
            f"{API_URL}/query/stream",
            json={
                "question": question,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k,
                "enable_preview": enable_preview,
                "conversation_history": api_history
            },
            timeout=600,
            stream=True  # Enable streaming
        )
        response.raise_for_status()

        # Parse Server-Sent Events
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')

                # Parse SSE format
                if line_str.startswith('event:'):
                    event_type = line_str[6:].strip()
                elif line_str.startswith('data:'):
                    data = json.loads(line_str[5:].strip())
                    yield {'event': event_type, 'data': data}

    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: A resposta demorou muito. Tente novamente ou reduza o número de trechos.")
    except requests.exceptions.ConnectionError:
        raise Exception("🔌 Erro de conexão: Verifique se o backend está rodando.")
    except Exception as e:
        raise Exception(f"❌ Erro: {str(e)}")

def query_api(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None, enable_preview: bool = True):
    """Send query to API with conversation history (non-streaming fallback)"""
    try:
        # Prepare conversation history (exclude sources for API call)
        api_history = []
        if conversation_history:
            for msg in conversation_history:
                api_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = requests.post(
            f"{API_URL}/query",
            json={
                "question": question,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k,
                "enable_preview": enable_preview,
                "conversation_history": api_history
            },
            timeout=600  # 10 minutes timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: A resposta demorou muito. Tente novamente ou reduza o número de trechos.")
    except requests.exceptions.ConnectionError:
        raise Exception("🔌 Erro de conexão: Verifique se o backend está rodando.")
    except Exception as e:
        raise Exception(f"❌ Erro: {str(e)}")

def display_text_with_typing(text: str, placeholder, delay: float = 0.01):
    """Display text with typing animation effect"""
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(displayed_text + '<span class="typing-cursor"></span>', unsafe_allow_html=True)
        time.sleep(delay)
    # Final display without cursor
    placeholder.markdown(text, unsafe_allow_html=True)

def display_source(source: dict, index: int):
    """Display a source with nice formatting"""
    priority_classes = {
        "PRIORIDADE MÁXIMA": ("priority-max", "badge-max", "🥇"),
        "OBRA FUNDAMENTAL": ("priority-high", "badge-high", "🥈"),
        "COMPLEMENTAR": ("priority-medium", "badge-medium", "🥉"),
        "OUTRAS OBRAS": ("priority-low", "badge-low", "📄")
    }
    
    card_class, badge_class, icon = priority_classes.get(
        source['priority_label'], 
        ("priority-low", "badge-low", "📄")
    )
    
    st.markdown(f"""
    <div class="source-card {card_class}">
        <div>
            <span class="priority-badge {badge_class}">{icon} {source['priority_label']}</span>
            <strong>Fonte {index}</strong>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem; opacity: 0.9;">
            {source['content'][:500]}{"..." if len(source['content']) > 500 else ""}
        </div>
        <div style="margin-top: 0.5rem; font-style: italic; font-size: 0.85rem; opacity: 0.8;">
            {source['display_name']} | Pág: {source['page']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_message_with_preview(message: dict, idx: int):
    """Display message with search plan if available"""

    # If has search plan, show it
    if message.get("search_plan"):
        st.markdown("**🔍 Plano de busca:**")
        st.markdown(message["search_plan"])
        st.markdown("---")

    # Show answer
    st.markdown("**💬 Resposta:**")
    st.markdown(message["content"])
    
    # Show sources
    if "sources" in message and message["sources"]:
        with st.expander(f"📖 {len(message['sources'])} Fontes Consultadas"):
            for i, source in enumerate(message["sources"], 1):
                display_source(source, i)
    
    # Feedback section
    if "feedback_given" not in message:
        st.markdown("---")
        st.markdown("**📝 Esta resposta foi útil?**")
        
        feedback_key = f"feedback_{idx}"
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👍 Boa", key=f"good_{idx}", use_container_width=True):
                st.session_state[feedback_key] = "good"
        
        with col2:
            if st.button("😐 Regular", key=f"neutral_{idx}", use_container_width=True):
                st.session_state[feedback_key] = "neutral"
        
        with col3:
            if st.button("👎 Ruim", key=f"bad_{idx}", use_container_width=True):
                st.session_state[feedback_key] = "bad"
        
        if feedback_key in st.session_state:
            rating = st.session_state[feedback_key]
            
            comment = st.text_area(
                "Comentário (opcional):",
                placeholder="Compartilhe sua opinião...",
                key=f"comment_{idx}",
                height=80
            )
            
            if st.button("✅ Enviar Feedback", key=f"submit_{idx}"):
                user_msg_idx = idx - 1
                question = st.session_state.messages[user_msg_idx]["content"] if user_msg_idx >= 0 else ""
                
                try:
                    # Save via API instead of locally
                    save_feedback_via_api(
                        question=question,
                        answer=message["content"],
                        sources=[s['content'][:200] for s in message.get("sources", [])],
                        rating=rating,
                        comment=comment,
                        user_name=st.session_state.user_name
                    )
                    
                    st.session_state.messages[idx]["feedback_given"] = True
                    st.success("✅ Feedback salvo no servidor!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")
                    st.caption("Verifique se o backend está rodando")

def main():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = generate_chat_id()
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Anônimo"
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("📚 Assistente Espírita")
        st.caption("Pergunte sobre a Doutrina Espírita baseada nas obras da Codificação")
    
    # Check API status
    api_status = check_api_status()
    
    # Sidebar
    with st.sidebar:
        st.header("🌐 Status do Backend")
        
        if api_status:
            st.success("✅ Backend Online")
            
            # GPU/CPU info from health endpoint
            if api_status.get('cuda_available'):
                st.info(f"🎮 {api_status.get('gpu', 'GPU')}")
            else:
                st.warning("💻 CPU Mode")
            
            # Try to get detailed status (models info)
            try:
                status_response = requests.get(f"{API_URL}/status", timeout=3)
                if status_response.status_code == 200:
                    detailed_status = status_response.json()
                    
                    # Show models if loaded
                    models = detailed_status.get('models_loaded', {})
                    if models.get('both_ready'):
                        st.caption(f"🤖 Modelos: {models.get('fast', '')} + {models.get('quality', '')}")
            except:
                pass
        else:
            st.error("❌ Backend Offline")
            st.code(f"API URL: {API_URL}")
        
        st.markdown("---")

        # Theme toggle
        st.header("🎨 Tema")
        col_dark, col_light = st.columns(2)

        with col_dark:
            if st.button("🌙 Escuro", use_container_width=True,
                        disabled=st.session_state.theme == "dark"):
                st.session_state.theme = "dark"
                st.rerun()

        with col_light:
            if st.button("☀️ Claro", use_container_width=True,
                        disabled=st.session_state.theme == "light"):
                st.session_state.theme = "light"
                st.rerun()

        st.markdown("---")

        # User identification
        st.header("👤 Identificação")
        user_name = st.text_input(
            "Seu nome:",
            value=st.session_state.user_name,
            placeholder="Ex: João Silva"
        )
        if user_name:
            st.session_state.user_name = user_name
        
        st.markdown("---")
        
        # Model settings
        st.header("⚙️ Configurações")
        
        temperature = st.slider(
            "Criatividade:",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.05,
            help="Controla criatividade. 0.3 = mais fiel aos textos"
        )
        
        top_k = st.slider(
            "Nº de trechos:",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Quantos trechos dos livros usar"
        )
        
        with st.expander("⚙️ Avançado"):
            fetch_k = st.slider(
                "Busca inicial:",
                min_value=top_k,
                max_value=30,
                value=15,
                step=5
            )
            
            enable_preview = st.checkbox(
                "Modo Preview",
                value=True,
                help="Mostra resposta rápida antes de validar com livros"
            )
        
        st.markdown("---")
        
        # Conversation management
        st.header("💬 Conversas")
        
        col_new, col_save = st.columns(2)
        
        with col_new:
            if st.button("🆕 Nova Conversa", use_container_width=True):
                if len(st.session_state.messages) > 0:
                    # Save current conversation
                    save_conversation(
                        st.session_state.current_chat_id,
                        st.session_state.messages,
                        st.session_state.user_name
                    )
                # Start new chat
                st.session_state.messages = []
                st.session_state.current_chat_id = generate_chat_id()
                st.rerun()
        
        with col_save:
            if st.button("💾 Salvar", use_container_width=True, disabled=len(st.session_state.messages) == 0):
                save_conversation(
                    st.session_state.current_chat_id,
                    st.session_state.messages,
                    st.session_state.user_name
                )
                st.success("✅ Salva!")
                time.sleep(1)
                st.rerun()
        
        # Recent conversations
        recent_convs = get_recent_conversations(10)
        
        if recent_convs:
            st.subheader("📜 Conversas Recentes")
            
            for conv in recent_convs:
                with st.container():
                    col_title, col_action = st.columns([4, 1])
                    
                    with col_title:
                        if st.button(
                            f"💬 {conv['title'][:30]}...",
                            key=f"load_{conv['chat_id']}",
                            use_container_width=True
                        ):
                            # Load conversation
                            loaded = load_conversation(conv['chat_id'])
                            if loaded:
                                st.session_state.messages = loaded['messages']
                                st.session_state.current_chat_id = conv['chat_id']
                                st.rerun()
                    
                    with col_action:
                        if st.button("🗑️", key=f"del_{conv['chat_id']}"):
                            delete_conversation(conv['chat_id'])
                            st.rerun()
                    
                    st.caption(f"{conv['message_count']} msgs • {conv['created_at'][:10]}")
        
        st.markdown("---")
        
        # Help
        st.header("💡 Dicas")
        st.markdown("""
        **Para melhores resultados:**
        
        ✅ Perguntas claras e específicas  
        ✅ Verifique as fontes citadas  
        ✅ Compare com os livros originais
        
        **Sobre o Modo Preview:**
        
        💭 Resposta imediata (1-2s)  
        📚 Validação com livros (3-4s)  
        🔍 Mostra o que foi corrigido
        
        **Exemplos:**
        • O que é o perispírito?
        • Sobre o suicídio segundo o Espiritismo
        • Diferença entre médium e sensitivo
        """)
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        # Select avatar
        if message["role"] == "user":
            avatar = "🧑"
        else:
            # Try to use Chico Xavier avatar, fallback to emoji
            avatar_path = "assets/avatars/chico_xavier.png"
            if os.path.exists(avatar_path):
                avatar = avatar_path
            else:
                avatar = "🤖"  # Fallback emoji

        with st.chat_message(message["role"], avatar=avatar):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                display_message_with_preview(message, idx)
    
    # Chat input
    if prompt := st.chat_input("Digite sua pergunta sobre Espiritismo..."):
        if not api_status:
            st.error("❌ Sistema offline. Não é possível processar perguntas.")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        
        # Get assistant response
        # Select avatar
        avatar_path = "assets/avatars/chico_xavier.png"
        assistant_avatar = avatar_path if os.path.exists(avatar_path) else "🤖"

        with st.chat_message("assistant", avatar=assistant_avatar):
            try:
                if enable_preview:
                    # STREAMING MODE - Show search plan first, then final answer
                    search_plan_placeholder = st.empty()
                    sources_placeholder = st.empty()
                    answer_placeholder = st.empty()

                    search_plan = None
                    sources = []
                    final_answer = None

                    # Stream events
                    for event in query_api_stream(
                        prompt,
                        None,
                        temperature,
                        top_k,
                        fetch_k,
                        st.session_state.messages[:-1],
                        enable_preview
                    ):
                        event_type = event['event']
                        data = event['data']

                        if event_type == 'search_plan':
                            # Show search plan with typing animation
                            search_plan = data['plan']
                            with search_plan_placeholder.container():
                                st.markdown("**🔍 Plano de busca:**")

                                # Create placeholder for typing animation
                                typing_placeholder = st.empty()
                                display_text_with_typing(search_plan, typing_placeholder, delay=0.003)

                                st.caption("_Buscando nos livros..._")

                        elif event_type == 'sources':
                            # Update with sources found
                            sources = data['sources']
                            with sources_placeholder.container():
                                st.info(f"📚 {data['count']} fontes encontradas nos livros")

                        elif event_type == 'answer':
                            # Show final answer
                            final_answer = data['answer']
                            out_of_scope = data.get('out_of_scope', False)

                            # Clear placeholders
                            search_plan_placeholder.empty()
                            sources_placeholder.empty()

                            with answer_placeholder.container():
                                # Show search plan (if not off-topic)
                                if not out_of_scope and search_plan:
                                    st.markdown("**🔍 Plano de busca:**")
                                    st.markdown(search_plan)
                                    st.markdown("---")

                                # Typing animation for final answer
                                st.markdown("**💬 Resposta:**")
                                final_typing_placeholder = st.empty()
                                display_text_with_typing(final_answer, final_typing_placeholder, delay=0.003)

                            # Show sources (if not off-topic)
                            if sources and not out_of_scope:
                                with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                                    for i, source in enumerate(sources, 1):
                                        display_source(source, i)

                        elif event_type == 'done':
                            # Processing complete
                            pass

                    # Save message
                    message_data = {
                        "role": "assistant",
                        "content": final_answer,
                        "sources": sources,
                        "search_plan": search_plan
                    }
                    st.session_state.messages.append(message_data)

                else:
                    # NON-STREAMING MODE (fallback)
                    with st.spinner("🔍 Consultando os livros espíritas..."):
                        result = query_api(
                            prompt,
                            None,
                            temperature,
                            top_k,
                            fetch_k,
                            st.session_state.messages[:-1],
                            enable_preview
                        )

                        answer = result['answer']
                        sources = result['sources']

                        st.markdown(answer)

                        # Show sources
                        if sources:
                            with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                                for i, source in enumerate(sources, 1):
                                    display_source(source, i)

                        # Save message
                        message_data = {
                            "role": "assistant",
                            "content": answer,
                            "sources": sources,
                            "has_preview": False
                        }
                        st.session_state.messages.append(message_data)

                # Auto-save
                save_conversation(
                    st.session_state.current_chat_id,
                    st.session_state.messages,
                    st.session_state.user_name
                )

                st.rerun()

            except Exception as e:
                st.error(str(e))

if __name__ == "__main__":
    main()