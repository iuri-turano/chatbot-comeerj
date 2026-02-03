import streamlit as st
import requests
from chat_history import (
    generate_chat_id,
)
import os
import time
import json

# Page configuration
st.set_page_config(
    page_title="Assistente Espírita",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# THEME SYSTEM
# ============================================================================

def get_theme_css(theme: str) -> str:
    """Generate CSS based on current theme (dark or light)"""

    if theme == "dark":
        return """
        <style>
            /* ===== DARK THEME — "Livro Antigo com Energia Moderna" ===== */

            /* Main background with subtle golden grid pattern */
            .stApp {
                background-color: #121212 !important;
                background-image:
                    radial-gradient(circle at 25% 25%, rgba(255, 215, 0, 0.03) 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, rgba(255, 193, 7, 0.03) 0%, transparent 50%),
                    linear-gradient(rgba(255, 215, 0, 0.02) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255, 215, 0, 0.02) 1px, transparent 1px) !important;
                background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px !important;
            }

            /* Sidebar with gradient */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0a0a0a 0%, #121212 50%, #0a0a0a 100%) !important;
                border-right: 1px solid rgba(255, 215, 0, 0.1);
            }

            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            .stChatMessage {
                padding: 1rem !important;
                border-radius: 10px !important;
                margin-bottom: 1rem !important;
            }

            /* User message — vibrant yellow gradient */
            .stChatMessage[data-testid="user-message"] {
                background: linear-gradient(135deg, #FFD700 0%, #FF8F00 100%) !important;
                color: #1a1a1a !important;
            }

            .stChatMessage[data-testid="user-message"] p,
            .stChatMessage[data-testid="user-message"] span,
            .stChatMessage[data-testid="user-message"] div {
                color: #1a1a1a !important;
            }

            /* Assistant message — dark blue-tinted gradient */
            .stChatMessage[data-testid="assistant-message"] {
                background: linear-gradient(135deg, #1E1E2E 0%, #2A2A3E 100%) !important;
                color: #FFFFFF !important;
                border: 1px solid rgba(255, 215, 0, 0.2);
            }

            /* Source cards with shadow */
            .source-card {
                background-color: rgba(255, 215, 0, 0.08);
                border-left: 4px solid #FFD700;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                color: #E0E0E0;
                box-shadow: 0 2px 8px rgba(255, 215, 0, 0.1),
                            inset 0 1px 0 rgba(255, 215, 0, 0.05);
            }

            .source-card.priority-max { border-left-color: #FFD700; }
            .source-card.priority-high { border-left-color: #FF6D00; }
            .source-card.priority-medium { border-left-color: #00BFA5; }
            .source-card.priority-low { border-left-color: #78909C; }

            /* Priority badges — vibrant with shadow */
            .priority-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-right: 0.5rem;
            }

            .badge-max {
                background: #FFD700 !important;
                color: #1a1a1a !important;
                box-shadow: 0 1px 4px rgba(255, 215, 0, 0.3);
                font-weight: 700 !important;
            }

            .badge-high {
                background: #FF6D00 !important;
                color: white !important;
                box-shadow: 0 1px 4px rgba(255, 109, 0, 0.3);
            }

            .badge-medium {
                background: #00BFA5 !important;
                color: white !important;
                box-shadow: 0 1px 4px rgba(0, 191, 165, 0.3);
            }

            .badge-low {
                background: linear-gradient(135deg, #78909C 0%, #90A4AE 100%);
                color: white;
            }

            /* Quotation card */
            .quotation-card {
                background-color: rgba(255, 215, 0, 0.08);
                border-left: 3px solid #FFC107;
                padding: 1rem;
                margin: 0.75rem 0;
                border-radius: 6px;
                color: #E0E0E0;
                font-size: 0.92rem;
                line-height: 1.6;
                box-shadow: 0 2px 6px rgba(255, 215, 0, 0.08);
            }

            .quotation-card .quote-header {
                font-weight: 600;
                color: #FFD700;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
            }

            .quotation-card .quote-text {
                color: #BDBDBD;
                font-style: italic;
            }

            /* Buttons with golden border and hover glow */
            .stButton button {
                border-radius: 8px !important;
                font-weight: 500 !important;
                border: 1px solid rgba(255, 215, 0, 0.3) !important;
                transition: all 0.3s ease !important;
            }

            .stButton button:hover {
                transform: translateY(-2px) !important;
                border-color: #FFD700 !important;
                box-shadow: 0 0 12px rgba(255, 215, 0, 0.2) !important;
            }

            .streamlit-expanderHeader {
                font-weight: 600 !important;
                color: #FFD700 !important;
            }

            .stChatInputContainer {
                border-top: 2px solid #FFD700;
                padding-top: 1rem;
            }

            .conv-item {
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                background-color: rgba(255, 215, 0, 0.05);
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .conv-item:hover {
                background-color: rgba(255, 215, 0, 0.1);
                transform: translateX(5px);
            }

            .streaming-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #FFD700;
                animation: pulse 1.5s ease-in-out infinite;
                margin-right: 8px;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }

            @keyframes blink {
                0%, 49% { opacity: 1; }
                50%, 100% { opacity: 0; }
            }

            .stMarkdown p {
                animation: fadeIn 0.2s ease-in;
            }

            @keyframes fadeIn {
                from { opacity: 0.8; }
                to { opacity: 1; }
            }

            .progress-container {
                background: rgba(255, 215, 0, 0.05);
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                border: 1px solid rgba(255, 215, 0, 0.3);
            }

            .progress-stage {
                display: flex;
                align-items: center;
                margin: 0.25rem 0;
                font-size: 0.8rem;
                color: rgba(255, 215, 0, 0.35);
                font-weight: 400;
                transition: all 0.3s ease;
            }

            .progress-stage.active {
                font-size: 1.05rem;
                font-weight: 700;
                color: #FFC107;
                margin: 0.5rem 0;
            }

            .progress-stage.completed {
                font-size: 0.8rem;
                color: rgba(255, 255, 255, 0.3);
                font-weight: 400;
                opacity: 0.5;
            }

            .progress-icon { margin-right: 0.75rem; font-size: 1rem; }
            .progress-stage.active .progress-icon { font-size: 1.3rem; }

            @keyframes progressAnimation {
                0% { width: 0%; }
                100% { width: 100%; }
            }

            .animated-progress {
                animation: progressAnimation 0.5s ease-out;
            }

            .auth-section {
                background: rgba(255, 215, 0, 0.05);
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid rgba(255, 215, 0, 0.15);
            }
        </style>
        """
    else:
        # LIGHT THEME — warm beige with real contrast
        return """
        <style>
            /* ===== LIGHT THEME — Warm Beige with Contrast ===== */

            /* Main background — warm beige with subtle dot pattern */
            .stApp {
                background-color: #F5F0E8 !important;
                background-image:
                    radial-gradient(circle, rgba(0, 0, 0, 0.06) 1px, transparent 1px),
                    radial-gradient(circle at 50% 50%, rgba(249, 168, 37, 0.05) 0%, transparent 70%) !important;
                background-size: 20px 20px, 100% 100% !important;
            }

            /* Sidebar with gradient beige */
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #EDE7D9 0%, #F5F0E8 50%, #EDE7D9 100%) !important;
                border-right: 1px solid #D4C4A8;
            }

            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }

            .stChatMessage {
                padding: 1rem !important;
                border-radius: 10px !important;
                margin-bottom: 1rem !important;
            }

            /* User message — strong amber gradient */
            .stChatMessage[data-testid="user-message"] {
                background: linear-gradient(135deg, #F9A825 0%, #FF8F00 100%) !important;
                color: #2C1810 !important;
            }

            .stChatMessage[data-testid="user-message"] p,
            .stChatMessage[data-testid="user-message"] span,
            .stChatMessage[data-testid="user-message"] div {
                color: #2C1810 !important;
            }

            /* Assistant message — white card with border and shadow */
            .stChatMessage[data-testid="assistant-message"] {
                background: #FFFFFF !important;
                color: #2C1810 !important;
                border: 1px solid #E0D5C5 !important;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
            }

            .stChatMessage[data-testid="assistant-message"] p,
            .stChatMessage[data-testid="assistant-message"] span,
            .stChatMessage[data-testid="assistant-message"] div {
                color: #2C1810 !important;
            }

            /* Source cards — white with brown border and shadow */
            .source-card {
                background-color: #FFFFFF;
                border-left: 4px solid #F9A825;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                color: #2C1810;
                border: 1px solid #D4C4A8;
                border-left: 4px solid #F9A825;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08),
                            0 1px 2px rgba(0, 0, 0, 0.04);
            }

            .source-card.priority-max { border-left-color: #F9A825; }
            .source-card.priority-high { border-left-color: #FF6D00; }
            .source-card.priority-medium { border-left-color: #00BFA5; }
            .source-card.priority-low { border-left-color: #78909C; }

            /* Priority badges — vibrant solid colors */
            .priority-badge {
                display: inline-block;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
                margin-right: 0.5rem;
            }

            .badge-max {
                background: #FFD700 !important;
                color: #1a1a1a !important;
                box-shadow: 0 1px 4px rgba(255, 215, 0, 0.3);
                font-weight: 700 !important;
            }

            .badge-high {
                background: #FF6D00 !important;
                color: white !important;
                box-shadow: 0 1px 4px rgba(255, 109, 0, 0.3);
            }

            .badge-medium {
                background: #00BFA5 !important;
                color: white !important;
                box-shadow: 0 1px 4px rgba(0, 191, 165, 0.3);
            }

            .badge-low {
                background: linear-gradient(135deg, #78909C 0%, #90A4AE 100%);
                color: white;
            }

            /* Quotation card — white with warm border */
            .quotation-card {
                background-color: #FFFFFF;
                border-left: 3px solid #F9A825;
                border: 1px solid #D4C4A8;
                border-left: 3px solid #F9A825;
                padding: 1rem;
                margin: 0.75rem 0;
                border-radius: 6px;
                color: #2C1810;
                font-size: 0.92rem;
                line-height: 1.6;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
            }

            .quotation-card .quote-header {
                font-weight: 600;
                color: #BF360C;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
            }

            .quotation-card .quote-text {
                color: #4E342E;
                font-style: italic;
            }

            /* Buttons with warm border and hover */
            .stButton button {
                border-radius: 8px !important;
                font-weight: 500 !important;
                border: 1px solid #D4C4A8 !important;
                background: #FFFFFF !important;
                transition: all 0.3s ease !important;
            }

            .stButton button:hover {
                transform: translateY(-2px) !important;
                border-color: #F9A825 !important;
                box-shadow: 0 2px 8px rgba(249, 168, 37, 0.2) !important;
            }

            .streamlit-expanderHeader {
                font-weight: 600 !important;
                color: #BF360C !important;
            }

            .stChatInputContainer {
                border-top: 2px solid #F9A825;
                padding-top: 1rem;
            }

            .conv-item {
                padding: 0.75rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                background-color: #FFFFFF;
                border: 1px solid #E0D5C5;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .conv-item:hover {
                background-color: #FFF8E1;
                border-color: #F9A825;
                transform: translateX(5px);
            }

            .streaming-indicator {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background-color: #F9A825;
                animation: pulse 1.5s ease-in-out infinite;
                margin-right: 8px;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.3; }
            }

            @keyframes blink {
                0%, 49% { opacity: 1; }
                50%, 100% { opacity: 0; }
            }

            .stMarkdown p {
                animation: fadeIn 0.2s ease-in;
            }

            @keyframes fadeIn {
                from { opacity: 0.8; }
                to { opacity: 1; }
            }

            .progress-container {
                background: #FFFFFF;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                border: 1px solid #D4C4A8;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
            }

            .progress-stage {
                display: flex;
                align-items: center;
                margin: 0.25rem 0;
                font-size: 0.8rem;
                color: rgba(44, 24, 16, 0.35);
                font-weight: 400;
                transition: all 0.3s ease;
            }

            .progress-stage.active {
                font-size: 1.05rem;
                font-weight: 700;
                color: #E65100;
                margin: 0.5rem 0;
            }

            .progress-stage.completed {
                font-size: 0.8rem;
                color: rgba(44, 24, 16, 0.3);
                font-weight: 400;
                opacity: 0.5;
            }

            .progress-icon { margin-right: 0.75rem; font-size: 1rem; }
            .progress-stage.active .progress-icon { font-size: 1.3rem; }

            @keyframes progressAnimation {
                0% { width: 0%; }
                100% { width: 100%; }
            }

            .animated-progress {
                animation: progressAnimation 0.5s ease-out;
            }

            .auth-section {
                background: #FFFFFF;
                border-radius: 8px;
                padding: 1rem;
                border: 1px solid #D4C4A8;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
        </style>
        """


# API Configuration
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = os.getenv("API_URL", "http://localhost:8000")


# ============================================================================
# AUTH HELPERS
# ============================================================================

def _auth_headers() -> dict:
    """Build request headers with auth token if available"""
    headers = {"Content-Type": "application/json"}
    token = st.session_state.get("auth_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def auth_register(email: str, password: str, display_name: str) -> dict:
    """Register a new user"""
    try:
        resp = requests.post(
            f"{API_URL}/auth/register",
            json={"email": email, "password": password, "display_name": display_name},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def auth_login(email: str, password: str) -> dict:
    """Login with email and password"""
    try:
        resp = requests.post(
            f"{API_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


def auth_logout():
    """Logout current user"""
    try:
        requests.post(
            f"{API_URL}/auth/logout",
            headers=_auth_headers(),
            timeout=10
        )
    except:
        pass
    st.session_state.auth_token = None
    st.session_state.logged_user = None


def auth_check_session():
    """Verify current session is still valid"""
    token = st.session_state.get("auth_token")
    if not token:
        return None
    try:
        resp = requests.get(
            f"{API_URL}/auth/me",
            headers=_auth_headers(),
            timeout=5
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get("user")
        else:
            st.session_state.auth_token = None
            st.session_state.logged_user = None
            return None
    except:
        return None


# ============================================================================
# BACKEND CONVERSATION HELPERS (for logged-in users)
# ============================================================================

def backend_save_conversation(chat_id: str, messages: list, title: str = "Conversa sem título"):
    """Save conversation to backend for logged-in user"""
    try:
        requests.post(
            f"{API_URL}/conversations/{chat_id}",
            headers=_auth_headers(),
            json={"title": title, "messages": messages},
            timeout=10
        )
    except:
        pass


def backend_get_conversations(limit: int = 20) -> list:
    """Get conversations from backend for logged-in user"""
    try:
        resp = requests.get(
            f"{API_URL}/conversations?limit={limit}",
            headers=_auth_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("conversations", [])
    except:
        pass
    return []


def backend_load_conversation(chat_id: str) -> dict:
    """Load a conversation from backend"""
    try:
        resp = requests.get(
            f"{API_URL}/conversations/{chat_id}",
            headers=_auth_headers(),
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return None


def backend_delete_conversation(chat_id: str):
    """Delete a conversation from backend"""
    try:
        requests.delete(
            f"{API_URL}/conversations/{chat_id}",
            headers=_auth_headers(),
            timeout=10
        )
    except:
        pass


# ============================================================================
# API FUNCTIONS
# ============================================================================

def check_api_status():
    """Check if API is online"""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.json()
    except:
        return None


def query_api(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None):
    """Send query to API with conversation history"""
    try:
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
            headers=_auth_headers(),
            timeout=600
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception("Timeout: A resposta demorou muito. Tente novamente ou reduza o numero de trechos.")
    except requests.exceptions.ConnectionError:
        raise Exception("Erro de conexao: Verifique se o backend esta rodando.")
    except Exception as e:
        raise Exception(f"Erro: {str(e)}")


def stream_api_response(question: str, model_name: str, temperature: float, top_k: int, fetch_k: int, conversation_history: list = None):
    """Stream response from API with status updates"""
    try:
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
            headers=_auth_headers(),
            stream=True,
            timeout=600
        )
        response.raise_for_status()

        full_text = ""
        sources = None
        char_buffer = ""
        buffer_size = 2

        for line in response.iter_lines(decode_unicode=True):
            if line:
                if line.startswith('data: '):
                    data = json.loads(line[6:])

                    if data['type'] == 'task_id':
                        pass

                    elif data['type'] == 'status':
                        current_status = {
                            'stage': data.get('stage'),
                            'progress': data.get('progress'),
                            'description': data.get('description')
                        }
                        yield None, None, current_status

                    elif data['type'] == 'token':
                        char_buffer += data['content']
                        full_text += data['content']

                        if len(char_buffer) >= buffer_size or data['content'] in [' ', '.', ',', '!', '?', '\n']:
                            yield char_buffer, None, None
                            char_buffer = ""

                    elif data['type'] == 'sources':
                        if char_buffer:
                            yield char_buffer, None, None
                            char_buffer = ""
                        sources = data['sources']

                    elif data['type'] == 'done':
                        if char_buffer:
                            yield char_buffer, None, None
                        yield None, sources, None
                        break

                    elif data['type'] == 'error':
                        raise Exception(data['content'])

    except requests.exceptions.Timeout:
        raise Exception("Timeout: A resposta demorou muito.")
    except Exception as e:
        raise Exception(f"Erro: {str(e)}")


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

def display_source(source: dict, index: int):
    """Display a source with nice formatting"""
    priority_classes = {
        "PRIORIDADE MAXIMA": ("priority-max", "badge-max", "🥇"),
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
            {source['display_name']} | Pag: {source['page']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_quotations(sources: list):
    """Display full quotations in styled cards"""
    has_full = any(s.get('full_content') for s in sources)
    if not has_full:
        return

    with st.expander(f"📜 Ver Citacoes Completas ({len(sources)})"):
        for i, source in enumerate(sources, 1):
            full_text = source.get('full_content', source.get('content', ''))

            priority_classes = {
                "PRIORIDADE MAXIMA": ("badge-max", "🥇"),
                "OBRA FUNDAMENTAL": ("badge-high", "🥈"),
                "COMPLEMENTAR": ("badge-medium", "🥉"),
                "OUTRAS OBRAS": ("badge-low", "📄")
            }
            badge_class, icon = priority_classes.get(
                source.get('priority_label', ''),
                ("badge-low", "📄")
            )

            st.markdown(f"""
            <div class="quotation-card">
                <div class="quote-header">
                    <span class="priority-badge {badge_class}">{icon} {source.get('priority_label', '')}</span>
                    {source.get('display_name', 'Desconhecido')} | Pag. {source.get('page', '?')}
                </div>
                <div class="quote-text">{full_text}</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# PERSISTENCE HELPERS
# ============================================================================

def is_logged_in() -> bool:
    return st.session_state.get("auth_token") is not None and st.session_state.get("logged_user") is not None


def do_save_conversation():
    """Save conversation ONLY for logged-in users."""
    if not is_logged_in():
        return  # Anonymous users: session-only, no persistence

    title = "Conversa sem titulo"
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            title = msg["content"][:50]
            break
    backend_save_conversation(
        st.session_state.current_chat_id,
        st.session_state.messages,
        title
    )


def do_get_recent_conversations(limit: int = 10):
    """Get recent conversations (logged-in users only)."""
    if is_logged_in():
        return backend_get_conversations(limit)
    return []


def do_load_conversation(chat_id: str):
    """Load conversation (logged-in users only)."""
    if is_logged_in():
        return backend_load_conversation(chat_id)
    return None


def do_delete_conversation(chat_id: str):
    """Delete conversation (logged-in users only)."""
    if is_logged_in():
        backend_delete_conversation(chat_id)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = generate_chat_id()
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Anonimo"
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None
    if "logged_user" not in st.session_state:
        st.session_state.logged_user = None
    if "llm_cached" not in st.session_state:
        st.session_state.llm_cached = False

    # Apply theme CSS
    st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

    # Header
    st.title("📚 Assistente Espirita")
    st.caption("Pergunte sobre a Doutrina Espirita baseada nas obras da Codificacao")

    # Check API status
    api_status = check_api_status()

    # ========================================================================
    # SIDEBAR
    # ========================================================================
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

        # ====================================================================
        # THEME TOGGLE
        # ====================================================================
        is_dark = st.toggle(
            "🌙 Tema Escuro",
            value=(st.session_state.theme == "dark"),
            key="theme_toggle"
        )
        new_theme = "dark" if is_dark else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

        st.markdown("---")

        # ====================================================================
        # AUTH SECTION
        # ====================================================================
        st.header("👤 Conta")

        if is_logged_in():
            user = st.session_state.logged_user
            st.success(f"Ola, **{user.get('display_name', 'Usuario')}**!")
            st.caption(f"📧 {user.get('email', '')}")
            if st.button("🚪 Sair", use_container_width=True):
                auth_logout()
                st.rerun()
        else:
            tab_login, tab_register = st.tabs(["Entrar", "Criar Conta"])

            with tab_login:
                login_email = st.text_input("Email:", key="login_email", placeholder="seu@email.com")
                login_password = st.text_input("Senha:", type="password", key="login_password")
                if st.button("Entrar", key="btn_login", use_container_width=True):
                    if login_email and login_password:
                        result = auth_login(login_email, login_password)
                        if result.get("success"):
                            st.session_state.auth_token = result["token"]
                            st.session_state.logged_user = result["user"]
                            st.session_state.user_name = result["user"].get("display_name", "Usuario")
                            st.rerun()
                        else:
                            st.error(result.get("error", "Erro ao entrar."))
                    else:
                        st.warning("Preencha email e senha.")

            with tab_register:
                reg_name = st.text_input("Nome:", key="reg_name", placeholder="Seu nome")
                reg_email = st.text_input("Email:", key="reg_email", placeholder="seu@email.com")
                reg_password = st.text_input("Senha:", type="password", key="reg_password")
                reg_password2 = st.text_input("Confirmar senha:", type="password", key="reg_password2")
                if st.button("Criar Conta", key="btn_register", use_container_width=True):
                    if not reg_email or not reg_password:
                        st.warning("Preencha email e senha.")
                    elif reg_password != reg_password2:
                        st.error("As senhas nao coincidem.")
                    else:
                        result = auth_register(reg_email, reg_password, reg_name or "Anonimo")
                        if result.get("success"):
                            st.session_state.auth_token = result["token"]
                            st.session_state.logged_user = result["user"]
                            st.session_state.user_name = result["user"].get("display_name", "Usuario")
                            st.success("Conta criada com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(result.get("error", "Erro ao criar conta."))

            st.caption("💡 Usando como Anonimo — conversas nao serao salvas entre sessoes.")

        st.markdown("---")

        # ====================================================================
        # MODEL SETTINGS
        # ====================================================================
        st.header("⚙️ Configuracoes")

        import platform
        system = platform.system().lower()

        if system == "darwin":
            available_models = ["llama3.2:3b", "llama3.2:1b"]
            default_help = "llama3.2:3b otimizado para Mac M4 16GB"
        elif system == "windows":
            available_models = ["llama3.1:8b", "llama3.2:3b", "llama3.2:1b"]
            default_help = "llama3.1:8b otimizado para RTX 3070 8GB"
        else:
            available_models = ["llama3.2:3b", "llama3.1:8b", "llama3.2:1b"]
            default_help = "Selecione o modelo adequado ao seu hardware"

        model_name = st.selectbox("Modelo:", available_models, help=default_help)

        temperature = st.slider(
            "Temperatura:", min_value=0.0, max_value=1.0, value=0.3, step=0.05,
            help="Controla criatividade. 0.3 = mais fiel aos textos"
        )

        top_k = st.slider(
            "No de trechos:", min_value=1, max_value=10, value=3, step=1,
            help="Quantos trechos dos livros usar (padrao: 3)"
        )

        with st.expander("⚙️ Avancado"):
            fetch_k = st.slider(
                "Busca inicial:", min_value=top_k, max_value=30, value=15, step=5
            )
            enable_streaming = st.checkbox(
                "Resposta progressiva", value=True,
                help="Mostra a resposta conforme e gerada"
            )

        st.markdown("---")

        # ====================================================================
        # CONVERSATION MANAGEMENT
        # ====================================================================
        st.header("💬 Conversas")

        if st.button("🆕 Nova Conversa", use_container_width=True):
            if len(st.session_state.messages) > 0 and is_logged_in():
                do_save_conversation()
            st.session_state.messages = []
            st.session_state.current_chat_id = generate_chat_id()
            st.rerun()

        # Recent conversations
        if is_logged_in():
            recent_convs = do_get_recent_conversations(10)

            if recent_convs:
                st.subheader("📜 Conversas Recentes")

                for conv in recent_convs:
                    with st.container():
                        col_title, col_action = st.columns([4, 1])

                        with col_title:
                            title = conv.get('title', 'Sem titulo')
                            if st.button(
                                f"💬 {title[:30]}...",
                                key=f"load_{conv.get('chat_id', '')}",
                                use_container_width=True
                            ):
                                loaded = do_load_conversation(conv.get('chat_id', ''))
                                if loaded:
                                    st.session_state.messages = loaded.get('messages', [])
                                    st.session_state.current_chat_id = conv.get('chat_id', '')
                                    st.rerun()

                        with col_action:
                            if st.button("🗑️", key=f"del_{conv.get('chat_id', '')}"):
                                do_delete_conversation(conv.get('chat_id', ''))
                                st.rerun()

                        msg_count = conv.get('message_count', 0)
                        created = conv.get('created_at', '')[:10]
                        st.caption(f"{msg_count} msgs • {created}")
            else:
                st.caption("Nenhuma conversa salva ainda.")
        else:
            st.info("🔒 Faca login para salvar suas conversas entre sessoes.")

        st.markdown("---")

        # Help
        st.header("💡 Dicas")
        st.markdown("""
        **Para melhores resultados:**

        ✅ Perguntas claras e especificas
        ✅ Verifique as fontes citadas
        ✅ Compare com os livros originais

        **Exemplos:**
        • O que e o perispirito?
        • Sobre o suicidio segundo o Espiritismo
        • Diferenca entre medium e sensitivo
        """)

    # ========================================================================
    # CHAT DISPLAY
    # ========================================================================
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"], avatar="🧑" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

            # Show sources
            if "sources" in message and message["sources"]:
                with st.expander(f"📖 {len(message['sources'])} Fontes Consultadas"):
                    for i, source in enumerate(message["sources"], 1):
                        display_source(source, i)

                # Full quotations accordion
                display_quotations(message["sources"])

            # Feedback section
            if message["role"] == "assistant" and "feedback_given" not in message:
                st.markdown("---")
                st.markdown("**📝 Esta resposta foi util?**")

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

                    # Optional name for anonymous users
                    anonymous_name = "Anônimo"
                    if not is_logged_in():
                        anonymous_name = st.text_input(
                            "Seu nome (opcional):",
                            value="",
                            placeholder="Como podemos te chamar?",
                            key=f"anon_name_{idx}"
                        ) or "Anônimo"

                    comment = st.text_area(
                        "Comentario (opcional):",
                        placeholder="Compartilhe sua opiniao...",
                        key=f"comment_{idx}",
                        height=80
                    )

                    if st.button("✅ Enviar Feedback", key=f"submit_{idx}"):
                        user_msg_idx = idx - 1
                        question = st.session_state.messages[user_msg_idx]["content"] if user_msg_idx >= 0 else ""

                        # Send feedback to backend API
                        try:
                            requests.post(
                                f"{API_URL}/feedback",
                                headers=_auth_headers(),
                                json={
                                    "question": question,
                                    "answer": message["content"],
                                    "sources": [s.get('content', '')[:200] for s in message.get("sources", []) or []],
                                    "rating": rating,
                                    "comment": comment,
                                    "anonymous_name": anonymous_name
                                },
                                timeout=10
                            )
                        except Exception:
                            pass  # Silently fail — don't block UX

                        st.session_state.messages[idx]["feedback_given"] = True
                        st.success("✅ Obrigado!")
                        time.sleep(1)
                        st.rerun()

    # ========================================================================
    # CHAT INPUT
    # ========================================================================
    if prompt := st.chat_input("Digite sua pergunta sobre Espiritismo..."):
        if not api_status:
            st.error("❌ Backend offline. Nao e possivel processar perguntas.")
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant", avatar="🤖"):
            if enable_streaming:
                progress_placeholder = st.empty()
                progress_bar = st.progress(0)
                response_placeholder = st.empty()

                full_response = ""
                sources = None
                current_stage = None
                current_bar_value = 0.0
                progress_cleared = False

                # Show initial progress immediately before backend responds
                # On subsequent questions, LLM is cached so skip that stage
                is_first_query = not st.session_state.llm_cached

                if is_first_query:
                    stages_info = [
                        ('creating_llm', '⚙️', 'Criando modelo LLM', 10),
                        ('searching_books', '🔍', 'Buscando nos livros espíritas', 30),
                        ('building_context', '📚', 'Construindo contexto', 50),
                        ('generating_answer', '🤖', 'Gerando resposta', 70),
                    ]
                    initial_active = 'creating_llm'
                    initial_emoji = '⚙️'
                    initial_desc = 'Criando modelo LLM'
                    initial_target = 0.10
                else:
                    stages_info = [
                        ('searching_books', '🔍', 'Buscando nos livros espíritas', 30),
                        ('building_context', '📚', 'Construindo contexto', 50),
                        ('generating_answer', '🤖', 'Gerando resposta', 70),
                    ]
                    initial_active = 'searching_books'
                    initial_emoji = '🔍'
                    initial_desc = 'Buscando nos livros espíritas'
                    initial_target = 0.30

                initial_html = '<div class="progress-container">'
                initial_html += '<div style="margin-bottom:0.75rem;font-weight:600;">🔍 Consultando os livros...</div>'
                initial_html += f'''
                <div class="progress-stage active stage-{initial_active}">
                    <span class="progress-icon">{initial_emoji}</span>
                    {initial_desc}
                </div>'''
                for stage_key, stage_emoji, stage_desc, stage_pct in stages_info[1:] if is_first_query else stages_info[1:]:
                    initial_html += f'''
                <div class="progress-stage">
                    <span class="progress-icon">⏳</span>
                    {stage_desc}
                </div>'''
                initial_html += '</div>'
                progress_placeholder.markdown(initial_html, unsafe_allow_html=True)

                # Animate bar to initial target
                target = initial_target
                step = max(target / 15, 0.01)
                while current_bar_value < target:
                    current_bar_value = min(current_bar_value + step, target)
                    progress_bar.progress(current_bar_value)
                    time.sleep(0.03)

                try:
                    for chunk, chunk_sources, status_update in stream_api_response(
                        prompt, model_name, temperature, top_k, fetch_k,
                        st.session_state.messages[:-1]
                    ):
                        if status_update:
                            current_stage = status_update
                            progress = status_update['progress']

                            # Animate progress bar smoothly
                            target = progress / 100
                            step = max((target - current_bar_value) / 15, 0.01)
                            while current_bar_value < target:
                                current_bar_value = min(current_bar_value + step, target)
                                progress_bar.progress(current_bar_value)
                                time.sleep(0.03)

                            current_stage_name = status_update['stage']
                            progress_html = '<div class="progress-container">'
                            progress_html += '<div style="margin-bottom:0.75rem;font-weight:600;">🔍 Consultando os livros...</div>'

                            for stage_key, stage_emoji, stage_desc, stage_pct in stages_info:
                                if stage_pct < progress:
                                    css_class = "progress-stage completed"
                                    icon = "✅"
                                elif stage_key == current_stage_name:
                                    css_class = f"progress-stage active stage-{stage_key}"
                                    icon = stage_emoji
                                else:
                                    css_class = "progress-stage"
                                    icon = "⏳"

                                progress_html += f'''
                                <div class="{css_class}">
                                    <span class="progress-icon">{icon}</span>
                                    {stage_desc}
                                </div>'''

                            progress_html += '</div>'
                            progress_placeholder.markdown(progress_html, unsafe_allow_html=True)

                        elif chunk:
                            # Clear progress after some text has appeared
                            if not progress_cleared and len(full_response) > 80:
                                progress_placeholder.empty()
                                progress_bar.empty()
                                progress_cleared = True

                            full_response += chunk
                            response_placeholder.markdown(full_response + " ▌")
                            time.sleep(0.01)

                        elif chunk_sources:
                            sources = chunk_sources

                    progress_placeholder.empty()
                    progress_bar.empty()

                    response_placeholder.markdown(full_response)

                    # Show sources
                    if sources:
                        with st.expander(f"📖 {len(sources)} Fontes Consultadas"):
                            for i, source in enumerate(sources, 1):
                                display_source(source, i)

                        # Full quotations
                        display_quotations(sources)

                    # Mark LLM as cached for subsequent queries
                    st.session_state.llm_cached = True

                    # Add to messages
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": full_response,
                        "sources": sources
                    })

                    # Auto-save
                    do_save_conversation()

                    st.rerun()

                except Exception as e:
                    st.error(str(e))
            else:
                # Non-streaming response
                with st.spinner("🔍 Consultando os livros espiritas..."):
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

                            # Full quotations
                            display_quotations(sources)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })

                        # Auto-save
                        do_save_conversation()

                        st.rerun()

                    except Exception as e:
                        st.error(str(e))


if __name__ == "__main__":
    main()
