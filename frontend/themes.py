"""Theme definitions for light and dark modes"""

THEMES = {
    "dark": {
        "name": "Dark",
        "primary_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "secondary_gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "user_msg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "assistant_msg_gradient": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "bg_color": "#0e1117",
        "text_color": "#ffffff",
        "overlay": "rgba(255, 255, 255, 0.05)",
        "border_color": "#667eea",
        "search_plan_bg": "rgba(102, 126, 234, 0.2)",
        "icon": "🌙"
    },
    "light": {
        "name": "Light",
        "primary_gradient": "linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%)",
        "secondary_gradient": "linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%)",
        "user_msg_gradient": "linear-gradient(135deg, #2196f3 0%, #1976d2 100%)",
        "assistant_msg_gradient": "linear-gradient(135deg, #ff9800 0%, #f57c00 100%)",
        "bg_color": "#fafafa",
        "text_color": "#212121",
        "overlay": "rgba(0, 0, 0, 0.05)",
        "border_color": "#2196f3",
        "search_plan_bg": "rgba(33, 150, 243, 0.1)",
        "icon": "☀️"
    }
}

def get_theme_css(theme_name: str) -> str:
    """Generate CSS for given theme"""
    theme = THEMES.get(theme_name, THEMES["dark"])

    return f"""
    <style>
        :root {{
            --primary-gradient: {theme["primary_gradient"]};
            --secondary-gradient: {theme["secondary_gradient"]};
            --user-msg-gradient: {theme["user_msg_gradient"]};
            --assistant-msg-gradient: {theme["assistant_msg_gradient"]};
            --bg-color: {theme["bg_color"]};
            --text-color: {theme["text_color"]};
            --overlay: {theme["overlay"]};
            --border-color: {theme["border_color"]};
            --search-plan-bg: {theme["search_plan_bg"]};
        }}

        /* Main container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
        }}

        /* Chat message styling */
        .stChatMessage {{
            padding: 1rem !important;
            border-radius: 10px !important;
            margin-bottom: 1rem !important;
        }}

        /* User message bubble */
        .stChatMessage[data-testid="user-message"] {{
            background: var(--user-msg-gradient) !important;
            color: white !important;
        }}

        /* Assistant message bubble */
        .stChatMessage[data-testid="assistant-message"] {{
            background: var(--assistant-msg-gradient) !important;
            color: white !important;
        }}

        /* Preview/search plan answer box */
        .preview-box {{
            background: var(--search-plan-bg);
            border-left: 4px solid var(--border-color);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
        }}

        /* Source cards */
        .source-card {{
            background-color: var(--overlay);
            border-left: 4px solid var(--border-color);
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
        }}

        .source-card.priority-max {{
            border-left-color: #ffd700;
        }}

        .source-card.priority-high {{
            border-left-color: #ff6b6b;
        }}

        .source-card.priority-medium {{
            border-left-color: #4ecdc4;
        }}

        /* Priority badges */
        .priority-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }}

        .badge-max {{
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            color: #333;
        }}

        .badge-high {{
            background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%);
            color: white;
        }}

        .badge-medium {{
            background: linear-gradient(135deg, #4ecdc4 0%, #44a3a3 100%);
            color: white;
        }}

        .badge-low {{
            background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
            color: white;
        }}

        /* Typing animation */
        .typing-cursor {{
            display: inline-block;
            width: 2px;
            height: 1em;
            background-color: currentColor;
            margin-left: 2px;
            animation: blink 1s step-end infinite;
        }}

        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0; }}
        }}

        .typing-text {{
            display: inline;
        }}

        /* Feedback buttons */
        .stButton button {{
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.3s ease !important;
        }}

        .stButton button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        }}

        /* Expander styling */
        .streamlit-expanderHeader {{
            font-weight: 600 !important;
            color: var(--border-color) !important;
        }}

        /* Chat input */
        .stChatInputContainer {{
            border-top: 2px solid var(--border-color);
            padding-top: 1rem;
        }}

        /* Conversation history item */
        .conv-item {{
            padding: 0.75rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            background-color: var(--overlay);
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .conv-item:hover {{
            background-color: var(--overlay);
            transform: translateX(5px);
        }}

        /* Validation notes */
        .validation-notes {{
            background: rgba(78, 205, 196, 0.1);
            border-left: 3px solid #4ecdc4;
            padding: 0.75rem;
            border-radius: 6px;
            margin-top: 0.5rem;
            font-size: 0.9rem;
        }}
    </style>
    """
