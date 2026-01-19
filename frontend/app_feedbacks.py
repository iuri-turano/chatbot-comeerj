import streamlit as st
import json
import os
from datetime import datetime
from collections import defaultdict
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="Painel de Feedbacks - Assistente Espírita",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    .feedback-card {
        background-color: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
    }
    
    .feedback-card.good {
        border-left-color: #4ecdc4;
    }
    
    .feedback-card.neutral {
        border-left-color: #f7b731;
    }
    
    .feedback-card.bad {
        border-left-color: #ee5a6f;
    }
    
    .rating-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .badge-good {
        background: #4ecdc4;
        color: white;
    }
    
    .badge-neutral {
        background: #f7b731;
        color: white;
    }
    
    .badge-bad {
        background: #ee5a6f;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
try:
    API_URL = st.secrets["API_URL"]
except:
    API_URL = os.getenv("API_URL", "http://localhost:8000")

def load_all_feedbacks():
    """Load all feedbacks from API"""
    try:
        response = requests.get(f"{API_URL}/feedback/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('feedbacks', [])
        return []
    except Exception as e:
        st.error(f"Erro ao carregar feedbacks da API: {e}")
        return []

def get_stats(feedbacks):
    """Calculate statistics from feedbacks"""
    if not feedbacks:
        return {
            'total': 0,
            'good': 0,
            'neutral': 0,
            'bad': 0,
            'with_comments': 0,
            'avg_rating': 0
        }
    
    stats = defaultdict(int)
    stats['total'] = len(feedbacks)
    
    for fb in feedbacks:
        rating = fb.get('rating', 'neutral')
        stats[rating] += 1
        if fb.get('comment') and fb.get('comment').strip():
            stats['with_comments'] += 1
    
    # Calculate average rating (good=1, neutral=0.5, bad=0)
    rating_values = {
        'good': 1.0,
        'neutral': 0.5,
        'bad': 0.0
    }
    
    total_value = sum(rating_values.get(fb.get('rating', 'neutral'), 0.5) for fb in feedbacks)
    stats['avg_rating'] = (total_value / len(feedbacks)) * 100 if feedbacks else 0
    
    return stats

def display_feedback_card(feedback, index):
    """Display a single feedback card"""
    rating = feedback.get('rating', 'neutral')
    question = feedback.get('question', 'Sem pergunta')
    answer = feedback.get('answer', 'Sem resposta')
    comment = feedback.get('comment', '')
    user_name = feedback.get('user_name', 'Anônimo')
    timestamp = feedback.get('timestamp', '')
    
    # Rating badges
    rating_emojis = {
        'good': ('👍', 'badge-good', 'Boa'),
        'neutral': ('😐', 'badge-neutral', 'Regular'),
        'bad': ('👎', 'badge-bad', 'Ruim')
    }
    
    emoji, badge_class, label = rating_emojis.get(rating, ('❓', 'badge-neutral', 'N/A'))
    
    st.markdown(f"""
    <div class="feedback-card {rating}">
        <div>
            <span class="rating-badge {badge_class}">{emoji} {label}</span>
            <strong>Feedback #{index + 1}</strong>
            <span style="float: right; font-size: 0.85rem; opacity: 0.8;">
                👤 {user_name} • 📅 {timestamp[:16]}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander(f"Ver detalhes - Feedback #{index + 1}"):
        st.markdown("**❓ Pergunta:**")
        st.info(question[:500] + ("..." if len(question) > 500 else ""))
        
        st.markdown("**💬 Resposta:**")
        st.success(answer[:500] + ("..." if len(answer) > 500 else ""))
        
        if comment:
            st.markdown("**✍️ Comentário do usuário:**")
            st.warning(comment)
        
        # Sources if available
        sources = feedback.get('sources', [])
        if sources:
            st.markdown(f"**📚 Fontes ({len(sources)}):**")
            for i, source in enumerate(sources, 1):
                st.caption(f"{i}. {source[:150]}...")

def main():
    st.title("📊 Painel de Feedbacks")
    st.caption("Análise de feedbacks do Assistente Espírita")
    
    # Check API connection
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🌐 Conexão com Backend")
    with col2:
        if st.button("🔄 Atualizar", use_container_width=True):
            st.rerun()
    
    try:
        health_response = requests.get(f"{API_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success(f"✅ Conectado: {API_URL}")
        else:
            st.error("❌ Backend respondeu com erro")
    except:
        st.error(f"❌ Não foi possível conectar ao backend: {API_URL}")
        st.info("Verifique se o backend está rodando e se a URL do ngrok está correta em secrets.toml")
        return
    
    st.markdown("---")
    
    # Load feedbacks
    feedbacks = load_all_feedbacks()
    
    if not feedbacks:
        st.warning("📭 Nenhum feedback encontrado ainda.")
        st.info(f"🌐 Conectado à API: {API_URL}")
        st.markdown("---")
        st.markdown("### 💡 Como funciona?")
        st.markdown("""
        1. Use o Assistente Espírita (frontend deployado)
        2. Após cada resposta, você verá botões de feedback
        3. Escolha: 👍 Boa, 😐 Regular, ou 👎 Ruim
        4. Opcionalmente, adicione um comentário
        5. Os feedbacks são salvos no backend (via ngrok)
        6. Volte aqui para ver as estatísticas!
        
        **Nota:** Os feedbacks ficam salvos no seu computador local (backend).
        """)
        return
    
    # Calculate stats
    stats = get_stats(feedbacks)
    
    # Display metrics
    st.markdown("### 📈 Estatísticas Gerais")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total</div>
            <div class="metric-value">{stats['total']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4ecdc4 0%, #44a3a3 100%);">
            <div class="metric-label">👍 Boas</div>
            <div class="metric-value">{stats['good']}</div>
            <div class="metric-label">{(stats['good']/stats['total']*100):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f7b731 0%, #d99e2d 100%);">
            <div class="metric-label">😐 Regulares</div>
            <div class="metric-value">{stats['neutral']}</div>
            <div class="metric-label">{(stats['neutral']/stats['total']*100):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #ee5a6f 0%, #d44759 100%);">
            <div class="metric-label">👎 Ruins</div>
            <div class="metric-value">{stats['bad']}</div>
            <div class="metric-label">{(stats['bad']/stats['total']*100):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Satisfação</div>
            <div class="metric-value">{stats['avg_rating']:.0f}%</div>
            <div class="metric-label">✍️ {stats['with_comments']} com comentários</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Filters
    st.markdown("### 🔍 Filtros")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_rating = st.multiselect(
            "Avaliação:",
            options=['good', 'neutral', 'bad'],
            format_func=lambda x: {'good': '👍 Boa', 'neutral': '😐 Regular', 'bad': '👎 Ruim'}[x],
            default=['good', 'neutral', 'bad']
        )
    
    with col2:
        filter_comments = st.checkbox("Apenas com comentários", value=False)
    
    with col3:
        sort_order = st.selectbox(
            "Ordenar por:",
            options=['newest', 'oldest'],
            format_func=lambda x: {'newest': '📅 Mais recentes', 'oldest': '📅 Mais antigos'}[x]
        )
    
    # Apply filters
    filtered_feedbacks = feedbacks.copy()
    
    # Filter by rating
    if filter_rating:
        filtered_feedbacks = [fb for fb in filtered_feedbacks if fb.get('rating') in filter_rating]
    
    # Filter by comments
    if filter_comments:
        filtered_feedbacks = [fb for fb in filtered_feedbacks if fb.get('comment') and fb.get('comment').strip()]
    
    # Sort
    if sort_order == 'newest':
        filtered_feedbacks = list(reversed(filtered_feedbacks))
    
    st.markdown(f"### 📋 Feedbacks ({len(filtered_feedbacks)})")
    
    if not filtered_feedbacks:
        st.info("Nenhum feedback encontrado com os filtros aplicados.")
        return
    
    # Pagination
    items_per_page = 10
    total_pages = (len(filtered_feedbacks) - 1) // items_per_page + 1
    
    if total_pages > 1:
        page = st.selectbox(
            "Página:",
            options=range(1, total_pages + 1),
            format_func=lambda x: f"Página {x} de {total_pages}"
        )
    else:
        page = 1
    
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(filtered_feedbacks))
    
    # Display feedbacks
    for i in range(start_idx, end_idx):
        display_feedback_card(filtered_feedbacks[i], i)
    
    # Export options
    st.markdown("---")
    st.markdown("### 📥 Exportar Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export to CSV
        if st.button("📊 Exportar para CSV", use_container_width=True):
            df = pd.DataFrame(feedbacks)
            csv = df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Baixar CSV",
                data=csv,
                file_name=f"feedbacks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col2:
        # Export to JSON
        if st.button("📄 Exportar para JSON", use_container_width=True):
            json_data = json.dumps(feedbacks, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="⬇️ Baixar JSON",
                data=json_data,
                file_name=f"feedbacks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Advanced analytics
    with st.expander("📊 Análises Avançadas"):
        st.markdown("#### Distribuição de Avaliações")
        
        chart_data = pd.DataFrame({
            'Avaliação': ['👍 Boa', '😐 Regular', '👎 Ruim'],
            'Quantidade': [stats['good'], stats['neutral'], stats['bad']]
        })
        
        st.bar_chart(chart_data.set_index('Avaliação'))
        
        # Timeline
        if len(feedbacks) > 1:
            st.markdown("#### Feedbacks ao Longo do Tempo")
            
            timeline_data = defaultdict(lambda: {'good': 0, 'neutral': 0, 'bad': 0})
            
            for fb in feedbacks:
                date = fb.get('timestamp', '')[:10]  # YYYY-MM-DD
                rating = fb.get('rating', 'neutral')
                timeline_data[date][rating] += 1
            
            df_timeline = pd.DataFrame.from_dict(timeline_data, orient='index')
            df_timeline = df_timeline.sort_index()
            
            st.line_chart(df_timeline)

if __name__ == "__main__":
    main()