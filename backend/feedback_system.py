import json
import os
from datetime import datetime
from typing import Dict, List

FEEDBACK_DIR = "feedback"
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "responses_feedback.jsonl")

def ensure_feedback_dir():
    """Create feedback directory if it doesn't exist"""
    if not os.path.exists(FEEDBACK_DIR):
        os.makedirs(FEEDBACK_DIR)

def save_feedback(
    question: str,
    answer: str,
    sources: List[str],
    keywords: List[str],
    rating: str,
    comment: str = "",
    user_name: str = "Anonymous"
):
    """Save user feedback to file"""
    ensure_feedback_dir()
    
    feedback_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_name,
        "question": question,
        "answer": answer,
        "keywords": keywords,
        "sources": [s[:200] for s in sources],  # Truncate for storage
        "rating": rating,  # "good", "bad", "neutral"
        "comment": comment
    }
    
    # Append to JSONL file (one JSON per line)
    with open(FEEDBACK_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')

def load_all_feedback() -> List[Dict]:
    """Load all feedback entries"""
    ensure_feedback_dir()
    
    if not os.path.exists(FEEDBACK_FILE):
        return []
    
    feedback_list = []
    with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                feedback_list.append(json.loads(line))
    
    return feedback_list

def get_feedback_stats() -> Dict:
    """Get statistics about feedback"""
    feedback = load_all_feedback()
    
    if not feedback:
        return {
            "total": 0,
            "good": 0,
            "bad": 0,
            "neutral": 0
        }
    
    stats = {
        "total": len(feedback),
        "good": sum(1 for f in feedback if f["rating"] == "good"),
        "bad": sum(1 for f in feedback if f["rating"] == "bad"),
        "neutral": sum(1 for f in feedback if f["rating"] == "neutral")
    }
    
    return stats