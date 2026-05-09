#!/usr/bin/env python3
"""AGI用語解き — 今日の一言叶: 毎日1つのAGI用語を解説して配信"""

import json
import random
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

TERMS_FILE = Path(__file__).parent / "terms.json"
STATE_FILE = Path(__file__).parent / "state.json"

def load_terms():
    with open(TERMS_FILE) as f:
        return json.load(f)

def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"posted_indices": [], "last_post_date": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def pick_term(terms, state):
    posted = set(state.get("posted_indices", []))
    available = [i for i in range(len(terms)) if i not in posted]
    if not available:
        # All terms posted, reset
        available = list(range(len(terms)))
        state["posted_indices"] = []
    idx = random.choice(available)
    return idx, terms[idx]

def generate_explanation(term_entry):
    term = term_entry["term"]
    reading = term_entry["reading"]
    category = term_entry["category"]
    desc = term_entry["description"]
    
    category_emoji = {
        "core": "🧠", "model": "🤖", "architecture": "🏗️",
        "training": "🎓", "technique": "🔧", "phenomenon": "✨",
        "theory": "📐", "concept": "💡", "safety": "🛡️",
        "capability": "⚡", "research": "🔬", "protocol": "📡"
    }
    emoji = category_emoji.get(category, "📌")
    
    # X用テキスト (280文字以内を意識、ただし長めでも可)
    x_text = f"""🎋 今日の一言叶 #{term.split('(')[0].strip().replace(' ', '_')}

{emoji} {term}
📖 {reading}

{desc}

#ONIZUKA_AGI #AGI"""

    # Discord用テキスト (詳細版)
    discord_text = f"""🎋 **今日の一言叶**

{emoji} **{term}**
📖 {reading}

{desc}

— 今日のAGI用語解説でした"""

    return x_text, discord_text

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    
    terms = load_terms()
    state = load_state()
    
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    
    if state.get("last_post_date") == today:
        print(f"Already posted today ({today})")
        return
    
    if cmd == "generate":
        idx, term = pick_term(terms, state)
        x_text, discord_text = generate_explanation(term)
        
        result = {
            "index": idx,
            "term": term["term"],
            "x_text": x_text,
            "discord_text": discord_text,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
    elif cmd == "mark-posted":
        idx = int(sys.argv[2])
        state["posted_indices"].append(idx)
        state["last_post_date"] = today
        save_state(state)
        print(f"Marked term #{idx} as posted for {today}")
        
    elif cmd == "status":
        posted = len(state.get("posted_indices", []))
        total = len(terms)
        print(f"Terms: {total} | Posted: {posted} | Remaining: {total - posted}")
        print(f"Last post: {state.get('last_post_date', 'Never')}")
        
    elif cmd == "terms":
        for i, t in enumerate(terms):
            marker = "✓" if i in state.get("posted_indices", []) else " "
            print(f"  [{marker}] {i:2d}. {t['term']} ({t['reading']})")

if __name__ == "__main__":
    main()
