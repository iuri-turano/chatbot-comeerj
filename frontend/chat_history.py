import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

CHATS_DIR = "chat_history"
CHATS_FILE = os.path.join(CHATS_DIR, "conversations.json")

def ensure_chats_dir():
    """Create chat history directory if it doesn't exist"""
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)

def generate_chat_id() -> str:
    """Generate a unique chat ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_conversation(
    chat_id: str,
    messages: List[Dict],
    user_name: str = "Anônimo",
    title: Optional[str] = None
) -> str:
    """
    Save a conversation to JSON file
    
    Args:
        chat_id: Unique identifier for the chat
        messages: List of message dictionaries with 'role', 'content', and optional 'sources'
        user_name: Name of the user
        title: Optional title (auto-generated from first question if not provided)
    
    Returns:
        The chat_id used
    """
    ensure_chats_dir()
    
    # Auto-generate title from first user message if not provided
    if title is None and messages:
        first_user_msg = next((msg for msg in messages if msg.get('role') == 'user'), None)
        if first_user_msg:
            # Use first 50 chars of first question as title
            title = first_user_msg['content'][:50]
            if len(first_user_msg['content']) > 50:
                title += "..."
        else:
            title = "Conversa sem título"
    
    conversation = {
        "chat_id": chat_id,
        "user_name": user_name,
        "title": title,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages
    }
    
    # Load existing conversations
    conversations = load_all_conversations()
    
    # Update or add new conversation
    existing_idx = next((i for i, conv in enumerate(conversations) if conv['chat_id'] == chat_id), None)
    
    if existing_idx is not None:
        # Update existing conversation
        conversations[existing_idx] = conversation
    else:
        # Add new conversation
        conversations.append(conversation)
    
    # Save to file
    with open(CHATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(conversations, f, ensure_ascii=False, indent=2)
    
    return chat_id

def load_all_conversations() -> List[Dict]:
    """Load all conversations from file"""
    ensure_chats_dir()
    
    if not os.path.exists(CHATS_FILE):
        return []
    
    try:
        with open(CHATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def load_conversation(chat_id: str) -> Optional[Dict]:
    """Load a specific conversation by ID"""
    conversations = load_all_conversations()
    return next((conv for conv in conversations if conv['chat_id'] == chat_id), None)

def delete_conversation(chat_id: str) -> bool:
    """Delete a conversation by ID"""
    conversations = load_all_conversations()
    filtered = [conv for conv in conversations if conv['chat_id'] != chat_id]
    
    if len(filtered) == len(conversations):
        return False  # Chat not found
    
    with open(CHATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)
    
    return True

def get_recent_conversations(limit: int = 10) -> List[Dict]:
    """Get most recent conversations (summary only, no messages)"""
    conversations = load_all_conversations()
    
    # Sort by updated_at (most recent first)
    sorted_convs = sorted(
        conversations, 
        key=lambda x: x.get('updated_at', x.get('created_at', '')), 
        reverse=True
    )
    
    # Return summary without full messages
    summaries = []
    for conv in sorted_convs[:limit]:
        summaries.append({
            "chat_id": conv['chat_id'],
            "title": conv['title'],
            "user_name": conv.get('user_name', 'Anônimo'),
            "created_at": conv['created_at'],
            "updated_at": conv.get('updated_at', conv['created_at']),
            "message_count": conv.get('message_count', len(conv.get('messages', [])))
        })
    
    return summaries

def search_conversations(query: str) -> List[Dict]:
    """Search conversations by title or content"""
    conversations = load_all_conversations()
    query_lower = query.lower()
    
    matching = []
    for conv in conversations:
        # Search in title
        if query_lower in conv.get('title', '').lower():
            matching.append(conv)
            continue
        
        # Search in messages
        for msg in conv.get('messages', []):
            if query_lower in msg.get('content', '').lower():
                matching.append(conv)
                break
    
    # Sort by relevance (most recent first)
    return sorted(matching, key=lambda x: x.get('updated_at', ''), reverse=True)

def export_conversation_to_text(chat_id: str) -> Optional[str]:
    """Export a conversation to formatted text"""
    conv = load_conversation(chat_id)
    if not conv:
        return None
    
    lines = []
    lines.append("=" * 70)
    lines.append(f"CONVERSA: {conv['title']}")
    lines.append(f"Data: {conv['created_at'][:10]}")
    lines.append(f"Usuário: {conv.get('user_name', 'Anônimo')}")
    lines.append("=" * 70)
    lines.append("")
    
    for i, msg in enumerate(conv.get('messages', []), 1):
        role = "VOCÊ" if msg['role'] == 'user' else "ASSISTENTE"
        lines.append(f"{role}:")
        lines.append(msg['content'])
        
        # Add sources if present
        if 'sources' in msg and msg['sources']:
            lines.append("")
            lines.append("Fontes consultadas:")
            for j, source in enumerate(msg['sources'], 1):
                lines.append(f"  {j}. {source.get('display_name', 'Desconhecido')} (pág. {source.get('page', 'N/A')})")
        
        lines.append("")
        lines.append("-" * 70)
        lines.append("")
    
    return "\n".join(lines)

def get_conversation_stats() -> Dict:
    """Get statistics about all conversations"""
    conversations = load_all_conversations()
    
    if not conversations:
        return {
            "total_conversations": 0,
            "total_messages": 0,
            "unique_users": 0,
            "avg_messages_per_conversation": 0
        }
    
    total_messages = sum(conv.get('message_count', len(conv.get('messages', []))) for conv in conversations)
    unique_users = len(set(conv.get('user_name', 'Anônimo') for conv in conversations))
    
    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "unique_users": unique_users,
        "avg_messages_per_conversation": total_messages / len(conversations) if conversations else 0
    }