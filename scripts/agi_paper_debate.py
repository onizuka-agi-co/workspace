#!/usr/bin/env python3
"""
AGI論文マルチエージェント議論システム

最新のAGI論文を取得し、複数のエージェントが異なる視点から議論。
議論から知見を抽出してX/Discordに投稿する自動コンテンツ生成パイプラインとの連携。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add workspace to path
WORKSPACE_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))

sys.path.insert(0, str(WORKSPACE_ROOT / "skills" / "hf-papers" / "scripts"))

# Import existing modules
try:
    from multi_source_fetcher import MultiSourceFetcher
    from content_queue import ContentQueue
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    MultiSourceFetcher = None
    ContentQueue = None

# Agent personas
AGENTS = {
    "optimist": {
        "name": "楽観派 🔆",
        "perspective": "技術の進歩と可能性にフォーカス。AGI実現への明るい未来を描く。",
        "style": "ポジティブで前向きな視点"
    },
    "critic": {
        "name": "批判派 🔍",
        "perspective": "課題・改善点・リスクを指摘。慎重なアプローチを主張。",
        "style": "批判的で慎重な視点"
    },
    "practitioner": {
        "name": "実用派 ⚙️",
        "perspective": "実装可能性と実用性を重視。現実的な応用を考える。",
        "style": "実践的で現実的な視点"
    }
}


def call_llm(prompt: str, system_prompt: str = "") -> str:
    """Call LLM API (z.ai/GLM) to generate response."""
    try:
        import requests

        # Use z.ai Anthropic-compatible API
        api_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
        api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", os.environ.get("ZAI_API_KEY", ""))

        # Anthropic-compatible API format
        response = requests.post(
            f"{api_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-3-5-sonnet-20241022",  # Maps to GLM-5
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("content", [{}])[0].get("text", "[No response]")
        else:
            print(f"LLM API error: {response.status_code} - {response.text[:200]}")
            return f"[LLM Error: {response.status_code}]"

    except Exception as e:
        print(f"LLM call failed: {e}")
        return f"[LLM Error: {e}]"


def generate_agent_opinion(
    paper: dict[str, Any],
    agent_key: str,
    previous_opinions: list[dict[str, str]] | None = None
) -> dict[str, str]:
    """Generate an agent's opinion on a paper."""
    agent = AGENTS[agent_key]

    # Build context from previous opinions
    context = ""
    if previous_opinions:
        for op in previous_opinions:
            context += f"\n**{op['agent_name']}**: {op['opinion'][:200]}...\n"

    system_prompt = f"""あなたは「{agent['name']}」という役割のAIエージェントです。
視点: {agent['perspective']}
スタイル: {agent['style']}

論文について、あなたの視点から簡潔に意見を述べてください。
日本語で、200文字以内で回答してください。"""

    prompt = f"""論文タイトル: {paper.get('title', 'Unknown')}
概要: {paper.get('summary', paper.get('abstract', 'No summary available'))[:500]}

{context}

この論文について、あなたの視点から意見を述べてください。"""

    opinion = call_llm(prompt, system_prompt)

    return {
        "agent_key": agent_key,
        "agent_name": agent["name"],
        "opinion": opinion
    }


def generate_debate_summary(paper: dict[str, Any], opinions: list[dict[str, str]]) -> str:
    """Generate a summary of the debate."""
    system_prompt = """あなたはAGI研究の専門家です。
複数のエージェントの議論を要約し、重要な知見を抽出してください。
日本語で、300文字以内で回答してください。"""

    opinions_text = "\n".join([
        f"**{op['agent_name']}**: {op['opinion']}"
        for op in opinions
    ])

    prompt = f"""論文タイトル: {paper.get('title', 'Unknown')}

議論:
{opinions_text}

この議論から重要な知見を抽出し、要約してください。"""

    return call_llm(prompt, system_prompt)


def extract_insights(paper: dict[str, Any], summary: str) -> dict[str, Any]:
    """Extract structured insights from the debate."""
    system_prompt = """あなたはAGI研究の専門家です。
議論から重要な知見を構造化して抽出してください。
JSON形式で出力してください。"""

    prompt = f"""論文タイトル: {paper.get('title', 'Unknown')}
要約: {summary}

以下の形式で知見を抽出してください:
{{
  "key_techniques": ["技術1", "技術2"],
  "challenges": ["課題1", "課題2"],
  "applications": ["応用1", "応用2"],
  "future_directions": ["方向性1", "方向性2"]
}}"""

    response = call_llm(prompt, system_prompt)

    try:
        # Try to parse JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            return json.loads(json_match.group())
    except json.JSONDecodeError:
        pass

    return {
        "key_techniques": [],
        "challenges": [],
        "applications": [],
        "future_directions": [],
        "raw_response": response
    }


def format_for_posting(
    paper: dict[str, Any],
    opinions: list[dict[str, str]],
    summary: str,
    insights: dict[str, Any]
) -> str:
    """Format the debate for X/Discord posting."""
    lines = [
        f"📜 **{paper.get('title', 'AGI論文')}**",
        "",
        "🗣️ **マルチエージェント議論**"
    ]

    for op in opinions:
        lines.append(f"{op['agent_name']}: {op['opinion'][:150]}...")

    lines.extend([
        "",
        f"📝 **要約**: {summary[:200]}...",
        "",
        "#AGI #AI論文 #ONIZUKA_AGI"
    ])

    return "\n".join(lines)


def run_debate(
    paper: dict[str, Any],
    agents: list[str] | None = None,
    rounds: int = 1
) -> dict[str, Any]:
    """Run a multi-agent debate on a paper."""
    if agents is None:
        agents = list(AGENTS.keys())

    all_opinions = []

    for round_num in range(rounds):
        round_opinions = []
        for agent_key in agents:
            # Pass previous opinions for context (except first round)
            prev = all_opinions if round_num > 0 else None
            opinion = generate_agent_opinion(paper, agent_key, prev)
            round_opinions.append(opinion)
        all_opinions.extend(round_opinions)

    summary = generate_debate_summary(paper, all_opinions)
    insights = extract_insights(paper, summary)

    return {
        "paper": paper,
        "opinions": all_opinions,
        "summary": summary,
        "insights": insights,
        "timestamp": datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description="AGI論文マルチエージェント議論システム")
    parser.add_argument("--paper-id", help="Specific paper ID to debate")
    parser.add_argument("--agents", nargs="+", choices=list(AGENTS.keys()),
                        default=list(AGENTS.keys()), help="Agents to include")
    parser.add_argument("--rounds", type=int, default=1, help="Number of debate rounds")
    parser.add_argument("--queue", action="store_true", help="Add result to content queue")
    parser.add_argument("--post", action="store_true", help="Post to X/Discord immediately")
    parser.add_argument("--output", choices=["json", "text"], default="text",
                        help="Output format")
    parser.add_argument("--top", type=int, default=1, help="Number of top papers to process")

    args = parser.parse_args()

    # Fetch papers
    if MultiSourceFetcher:
        fetcher = MultiSourceFetcher()
        papers = fetcher.fetch_all(top_k=args.top)
    else:
        # Fallback: use sample paper
        papers = [{
            "id": "sample-001",
            "title": "Sample AGI Paper",
            "summary": "This is a sample paper for testing.",
            "source": "test"
        }]

    if not papers:
        print("No papers found")
        return

    results = []
    for paper in papers[:args.top]:
        print(f"\n📜 Processing: {paper.get('title', 'Unknown')[:60]}...")

        result = run_debate(paper, args.agents, args.rounds)
        results.append(result)

        # Display opinions
        for op in result["opinions"]:
            print(f"\n{op['agent_name']}:")
            print(f"  {op['opinion'][:200]}...")

        print(f"\n📝 要約:")
        print(f"  {result['summary'][:300]}...")

        # Add to queue if requested
        if args.queue and ContentQueue:
            queue = ContentQueue()
            content = format_for_posting(
                paper, result["opinions"], result["summary"], result["insights"]
            )
            queue.add_item(
                content=content,
                source="agi_paper_debate",
                metadata={"paper_id": paper.get("id"), "title": paper.get("title")}
            )
            print("\n✅ Added to content queue")

    # Output results
    if args.output == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'='*60}")
        print(f"Processed {len(results)} paper(s)")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
