import streamlit as st
import requests
from feedback_system import save_feedback, get_feedback_stats
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

# Custom CSS for chat bubbles, avatars, and better UI
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem !important;
        border-radius: 10px !important;
        margin-bottom: 1rem !important;
    }
    
    /* User message bubble */
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Assistant message bubble */
    .stChatMessage[data-testid="assistant-message"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        color: white !important;
    }
    
    /* Source cards */
    .source-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    
    .source-card.priority-max {
        border-left-color: #ffd700;
    }
    
    .source-card.priority-high {
        border-left-color: #ff6b6b;
    }
    
    .source-card.priority-medium {
        border-left-color: #4ecdc4;
    }
    
    /* Priority badges */
    .priority-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .badge-max {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #333;
    }
    
    .badge-high {
        background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
        color: white;
    }
    
    .badge-medium {
        background: linear-gradient(135deg, #4ecdc4 0%, #44a3a3 100%);
        color: white;
    }
    
    .badge-low {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
        color: white;
    }
    
    /* Feedback buttons */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600 !important;
        color: #667eea !important;
    }
    
    /* Chat input */
    .stChatInputContainer {
        border-top: 2px solid #667eea;
        padding-top: 1rem;
    }
    
    /* Conversation history item */
    .conv-item {
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        background-color: rgba(255, 255, 255, 0.05);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .conv-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
        transform: translateX(5px);
    }
    
    /* Streaming indicator */
    .streaming-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #4ecdc4;
        animation: pulse 1.5s ease-in-out infinite;
        margin-right: 8px;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    /* Blinking cursor effect for streaming */
    @keyframes blink {
        0%, 49% { opacity: 1; }
        50%, 100% { opacity: 0; }
    }

    /* Smooth text appearance */
    .stMarkdown p {
        animation: fadeIn 0.2s ease-in;
    }

    @keyframes fadeIn {
        from { opacity: 0.8; }
        to { opacity: 1; }
    }

    /* Progress indicator styling */
    .progress-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }

    .progress-stage {
        display: flex;
        align-items: center;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #667eea;
        font-weight: 500;
    }

    .progress-stage.active {
        color: #4ecdc4;
        font-weight: 600;
    }

    .progress-stage.completed {
        color: #95a5a6;
        opacity: 0.7;
    }

    .progress-icon {
        margin-right: 0.75rem;
        font-size: 1.2rem;
    }

    .progress-percentage {
        margin-left: auto;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Stage-specific colors */
    .stage-creating_llm { color: #3498db; }
    .stage-searching_books { color: #e74c3c; }
    .stage-building_context { color: #f39c12; }
    .stage-generating_answer { color: #2ecc71; }
    .stage-formatting_response { color: #9b59b6; }

    /* Animated progress bar */
    @keyframes progressAnimation {
        0% { width: 0%; }
        100% { width: 100%; }
    }

    .animated-progress {
        animation: progressAnimation 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
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

def query_api(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None):
    """Send query to API with conversation history"""
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
                "model_name": model_name,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k,
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

def stream_api_response(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None):
    """Stream response from API with status updates and character-by-character support"""
    try:
        # Prepare conversation history
        api_history = []
        if conversation_history:
            for msg in conversation_history:
                api_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        response = requests.post(
            f"{API_URL}/query_stream",
            json={
                "question": question,
                "model_name": model_name,
                "temperature": temperature,
                "top_k": top_k,
                "fetch_k": fetch_k,
                "conversation_history": api_history
            },
            stream=True,
            timeout=600  # 10 minutes timeout
        )
        response.raise_for_status()

        full_text = ""
        sources = None
        char_buffer = ""
        buffer_size = 2  # Batch 2 characters at a time for smoother display

        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith('data: '):
                    import json
                    data = json.loads(line[6:])

                    if data['type'] == 'task_id':
                        # Initial task ID
                        pass

                    elif data['type'] == 'status':
                        # Status update event
                        current_status = {
                            'stage': data.get('stage'),
                            'progress': data.get('progress'),
                            'description': data.get('description')
                        }
                        yield None, None, current_status  # Yield status

                    elif data['type'] == 'token':
                        char_buffer += data['content']
                        full_text += data['content']

                        # Yield buffer when it reaches buffer_size or immediately for spaces/punctuation
                        if len(char_buffer) >= buffer_size or data['content'] in [' ', '.', ',', '!', '?', '\n']:
                            yield char_buffer, None, None  # Yield text chunk
                            char_buffer = ""

                    elif data['type'] == 'sources':
                        # Flush any remaining characters in buffer
                        if char_buffer:
                            yield char_buffer, None, None
                            char_buffer = ""
                        sources = data['sources']

                    elif data['type'] == 'done':
                        # Flush any remaining characters
                        if char_buffer:
                            yield char_buffer, None, None
                        # Final yield with sources
                        yield None, sources, None
                        break

                    elif data['type'] == 'error':
                        raise Exception(data['content'])

    except requests.exceptions.Timeout:
        raise Exception("⏱️ Timeout: A resposta demorou muito.")
    except Exception as e:
        raise Exception(f"❌ Erro: {str(e)}")

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
            if api_status.get('cuda_available'):
                st.info(f"🎮 {api_status.get('gpu', 'GPU')}")
            else:
                st.warning("💻 CPU Mode")
        else:
            st.error("❌ Backend Offline")
            st.code(f"API URL: {API_URL}")
        
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
        
        # OS-specific model selection
        import platform
        system = platform.system().lower()

        if system == "darwin":  # macOS
            available_models = ["llama3.2:3b", "llama3.2:1b"]
            default_help = "llama3.2:3b otimizado para Mac M4 16GB com raciocínio aprimorado"
        elif system == "windows":
            available_models = ["llama3.1:8b", "llama3.2:3b", "llama3.2:1b"]
            default_help = "llama3.1:8b otimizado para RTX 3070 8GB com raciocínio aprimorado"
        else:  # Linux or other
            available_models = ["llama3.2:3b", "llama3.1:8b", "llama3.2:1b"]
            default_help = "Selecione o modelo adequado ao seu hardware"

        model_name = st.selectbox(
            "Modelo:",
            available_models,
            help=default_help
        )
        
        temperature = st.slider(
            "Temperatura:",
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
            help="Quantos trechos dos livros usar (padrão: 3)"
        )
        
        with st.expander("⚙️ Avançado"):
            fetch_k = st.slider(
                "Busca inicial:",
                min_value=top_k,
                max_value=30,
                value=15,
                step=5
            )
            
            enable_streaming = st.checkbox(
                "Resposta progressiva",
                value=True,
                help="Mostra a resposta conforme é gerada"
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
        
        **Exemplos:**
        • O que é o perispírito?
        • Sobre o suicídio segundo o Espiritismo
        • Diferença entre médium e sensitivo
        """)
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])
            
            # Show sources
            if "sources" in message and message["sources"]:
                with st.expander(f"📖 {len(message['sources'])} Fontes Consultadas"):
                    for i, source in enumerate(message["sources"], 1):
                        display_source(source, i)
            
            # Feedback section
            if message["role"] == "assistant" and "feedback_given" not in message:
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
                        
                        save_feedback(
                            question=question,
                            answer=message["content"],
                            sources=[s['content'][:200] for s in message.get("sources", [])],
                            keywords=[],
                            rating=rating,
                            comment=comment,
                            user_name=st.session_state.user_name
                        )
                        
                        st.session_state.messages[idx]["feedback_given"] = True
                        st.success("✅ Obrigado!")
                        time.sleep(1)
                        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Digite sua pergunta sobre Espiritismo..."):
        if not api_status:
            st.error("❌ Backend offline. Não é possível processar perguntas.")
            return
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant", avatar="🤖"):
            if enable_streaming:
                # Streaming response with real-time display and progress indicators
                progress_placeholder = st.empty()
                progress_bar = st.progress(0)
                response_placeholder = st.empty()

                full_response = ""
                sources = None
                current_stage = None

                try:
                    for chunk, chunk_sources, status_update in stream_api_response(
                        prompt, model_name, temperature, top_k, fetch_k,
                        st.session_state.messages[:-1]  # Exclude current question
                    ):
                        # Handle status updates
                        if status_update:
                            current_stage = status_update
                            progress = status_update['progress']
                            description = status_update['description']

                            # Update progress bar
                            progress_bar.progress(progress / 100)

                            # Update status text with emoji based on stage
                            stage_emoji = {
                                'creating_llm': '⚙️',
                                'searching_books': '🔍',
                                'building_context': '📚',
                                'generating_answer': '🤖',
                                'formatting_response': '✨',
                                'complete': '✅'
                            }
                            emoji = stage_emoji.get(status_update['stage'], '🔄')

                            progress_placeholder.markdown(
                                f"**{emoji} {description}** ({progress}%)"
                            )

                        # Handle text chunks
                        elif chunk:
                            # Clear progress display when text starts (after generating_answer stage begins)
                            if current_stage and current_stage.get('stage') == 'generating_answer' and len(full_response) == 0:
                                progress_placeholder.empty()
                                progress_bar.empty()

                            full_response += chunk
                            # Display with blinking cursor for streaming effect
                            response_placeholder.markdown(full_response + " ▌")
                            # Small delay to allow Streamlit to render the update
                            time.sleep(0.01)

                        # Handle sources
                        elif chunk_sources:
                            sources = chunk_sources

                    # Clear any remaining progress indicators
                    progress_placeholder.empty()
                    progress_bar.empty()

                    # Remove cursor when done
                    response_placeholder.markdown(full_response)
                    
                    # Show sources
                    if sources:
                        with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                            for i, source in enumerate(sources, 1):
                                display_source(source, i)
                    
                    # Add to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources
                    })
                    
                    # Auto-save after each exchange
                    save_conversation(
                        st.session_state.current_chat_id,
                        st.session_state.messages,
                        st.session_state.user_name
                    )
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(str(e))
            else:
                # Non-streaming response
                with st.spinner("🔍 Consultando os livros espíritas..."):
                    try:
                        result = query_api(
                            prompt, model_name, temperature, top_k, fetch_k,
                            st.session_state.messages[:-1]
                        )
                        
                        answer = result['answer']
                        sources = result['sources']
                        
                        st.markdown(answer)
                        
                        if sources:
                            with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                                for i, source in enumerate(sources, 1):
                                    display_source(source, i)
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                        
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