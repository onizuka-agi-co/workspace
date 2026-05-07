#!/usr/bin/env python3
"""
AGI Research Impact Dashboard

Static HTML dashboard analyzing AGI research trends, impact metrics,
author networks, and topic evolution from the knowledge graph data.

Usage:
    python impact_dashboard.py                  # Generate dashboard.html
    python impact_dashboard.py --serve          # Generate and serve on port 8050
    python impact_dashboard.py --output path.html  # Custom output path
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from html import escape

PROJECT_ROOT = Path(__file__).parent
CACHE_FILE = PROJECT_ROOT / "papers_cache.json"
GRAPH_FILE = PROJECT_ROOT / "knowledge_graph.json"


def load_data():
    """Load papers and graph data."""
    papers = []
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            data = json.load(f)
            papers = data.get("papers", [])

    graph = {}
    if GRAPH_FILE.exists():
        with open(GRAPH_FILE) as f:
            graph = json.load(f)

    return papers, graph


def compute_metrics(papers):
    """Compute impact metrics from papers."""
    # Citation stats
    citations = [p.get("citationCount", 0) or 0 for p in papers]
    total_citations = sum(citations)
    avg_citations = total_citations / len(papers) if papers else 0
    max_citations = max(citations) if citations else 0

    # Top papers
    top_papers = sorted(papers, key=lambda p: p.get("citationCount", 0) or 0, reverse=True)[:10]

    # Author productivity
    author_papers = defaultdict(int)
    author_citations = defaultdict(int)
    for p in papers:
        for a in p.get("authors", []):
            name = a if isinstance(a, str) else a.get("name", "")
            if name:
                author_papers[name] += 1
                author_citations[name] += p.get("citationCount", 0) or 0

    top_authors = sorted(author_papers.items(), key=lambda x: x[1], reverse=True)[:10]
    top_cited_authors = sorted(author_citations.items(), key=lambda x: x[1], reverse=True)[:10]

    # Topic distribution
    topic_counter = Counter()
    for p in papers:
        for t in p.get("tags", []):
            tag = t if isinstance(t, str) else t.get("name", "")
            if tag:
                topic_counter[tag] += 1

    top_topics = topic_counter.most_common(15)

    # Timeline
    monthly = defaultdict(int)
    monthly_citations = defaultdict(int)
    for p in papers:
        pub = p.get("publishedAt", "")
        if pub:
            month = pub[:7]  # YYYY-MM
            monthly[month] += 1
            monthly_citations[month] += p.get("citationCount", 0) or 0

    timeline = sorted(monthly.items())
    timeline_citations = sorted(monthly_citations.items())

    # Organizations
    org_counter = Counter()
    for p in papers:
        org = p.get("organization", "")
        if org:
            org_counter[org] += 1
        for a in p.get("authors", []):
            if isinstance(a, dict) and a.get("organization"):
                org_counter[a["organization"]] += 1

    top_orgs = org_counter.most_common(10)

    # GitHub repos
    github_papers = [p for p in papers if p.get("githubRepo")]

    return {
        "total_papers": len(papers),
        "total_citations": total_citations,
        "avg_citations": round(avg_citations, 1),
        "max_citations": max_citations,
        "top_papers": top_papers,
        "top_authors": top_authors,
        "top_cited_authors": top_cited_authors,
        "top_topics": top_topics,
        "timeline": timeline,
        "timeline_citations": timeline_citations,
        "top_orgs": top_orgs,
        "github_papers": len(github_papers),
        "generated_at": datetime.now(__import__("datetime").timezone.utc).isoformat(),
    }


def generate_html(metrics):
    """Generate static HTML dashboard."""
    # Color palette (ONIZUKA theme)
    c = {
        "bg": "#0d1117",
        "card": "#161b22",
        "border": "#30363d",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "red": "#C41E3A",
        "green": "#4CAF50",
        "blue": "#2196F3",
        "gold": "#FFD700",
        "purple": "#9C27B0",
    }

    top_papers_rows = ""
    for i, p in enumerate(metrics["top_papers"], 1):
        title = escape(p.get("title", "N/A"))[:80]
        citations = p.get("citationCount", 0) or 0
        authors = ", ".join(
            (a if isinstance(a, str) else a.get("name", ""))
            for a in p.get("authors", [])[:3]
        )
        date = p.get("publishedAt", "")[:10]
        url = p.get("url", "#")
        tag_badges = " ".join(
            f'<span class="tag">{escape(t if isinstance(t, str) else t.get("name", ""))}</span>'
            for t in p.get("tags", [])[:3]
        )
        top_papers_rows += f"""
        <tr>
            <td class="rank">{i}</td>
            <td><a href="{url}" target="_blank" class="paper-link">{title}</a><br>
                <span class="muted">{escape(authors)}{(' et al.' if len(p.get('authors',[])) > 3 else '')}</span><br>
                {tag_badges}
            </td>
            <td class="num">{citations:,}</td>
            <td class="muted">{date}</td>
        </tr>"""

    top_authors_rows = ""
    for name, count in metrics["top_authors"]:
        top_authors_rows += f"""
        <tr>
            <td>{escape(name)}</td>
            <td class="num">{count}</td>
        </tr>"""

    top_cited_authors_rows = ""
    for name, cites in metrics["top_cited_authors"]:
        top_cited_authors_rows += f"""
        <tr>
            <td>{escape(name)}</td>
            <td class="num">{cites:,}</td>
        </tr>"""

    topic_bars = ""
    max_topic = metrics["top_topics"][0][1] if metrics["top_topics"] else 1
    for topic, count in metrics["top_topics"]:
        pct = count / max_topic * 100
        topic_bars += f"""
        <div class="bar-row">
            <span class="bar-label">{escape(topic)}</span>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%"></div></div>
            <span class="bar-num">{count}</span>
        </div>"""

    timeline_rows = ""
    for month, count in metrics["timeline"]:
        timeline_rows += f'<tr><td>{month}</td><td class="num">{count}</td></tr>'

    org_rows = ""
    for org, count in metrics["top_orgs"]:
        org_rows += f'<tr><td>{escape(org)}</td><td class="num">{count}</td></tr>'

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGI Research Impact Dashboard | ONIZUKA AGI Co.</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif;
       background: {c["bg"]}; color: {c["text"]}; padding: 2rem; }}
h1 {{ color: {c["red"]}; font-size: 1.8rem; margin-bottom: 0.3rem; }}
.subtitle {{ color: {c["muted"]}; margin-bottom: 2rem; font-size: 0.9rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
         gap: 1rem; margin-bottom: 2rem; }}
.card {{ background: {c["card"]}; border: 1px solid {c["border"]};
         border-radius: 8px; padding: 1.2rem; }}
.card .label {{ color: {c["muted"]}; font-size: 0.75rem; text-transform: uppercase;
               letter-spacing: 0.05em; }}
.card .value {{ font-size: 2rem; font-weight: 700; margin-top: 0.3rem; }}
.card .value.red {{ color: {c["red"]}; }}
.card .value.green {{ color: {c["green"]}; }}
.card .value.blue {{ color: {c["blue"]}; }}
.card .value.gold {{ color: {c["gold"]}; }}
h2 {{ color: {c["text"]}; font-size: 1.2rem; margin: 1.5rem 0 0.8rem;
      border-left: 3px solid {c["red"]}; padding-left: 0.6rem; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 1rem; }}
th {{ text-align: left; color: {c["muted"]}; font-size: 0.75rem; text-transform: uppercase;
     padding: 0.5rem 0.6rem; border-bottom: 1px solid {c["border"]}; }}
td {{ padding: 0.5rem 0.6rem; border-bottom: 1px solid {c["border"]}; font-size: 0.9rem; }}
.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.rank {{ color: {c["gold"]}; font-weight: 700; text-align: center; width: 2rem; }}
.muted {{ color: {c["muted"]}; font-size: 0.8rem; }}
.paper-link {{ color: {c["blue"]}; text-decoration: none; }}
.paper-link:hover {{ text-decoration: underline; }}
.tag {{ background: {c["border"]}; color: {c["muted"]}; padding: 0.1rem 0.4rem;
        border-radius: 4px; font-size: 0.7rem; display: inline-block; margin: 0.1rem; }}
.bar-row {{ display: flex; align-items: center; margin: 0.3rem 0; }}
.bar-label {{ width: 120px; font-size: 0.8rem; text-align: right; padding-right: 0.6rem;
              overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.bar-track {{ flex: 1; background: {c["border"]}; border-radius: 3px; height: 18px; }}
.bar-fill {{ background: linear-gradient(90deg, {c["red"]}, {c["gold"]}); height: 100%;
             border-radius: 3px; }}
.bar-num {{ width: 30px; text-align: right; font-size: 0.8rem; margin-left: 0.4rem;
            color: {c["muted"]}; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
@media (max-width: 768px) {{ .cols {{ grid-template-columns: 1fr; }} }}
footer {{ color: {c["muted"]}; font-size: 0.75rem; margin-top: 2rem; text-align: center; }}
</style>
</head>
<body>

<h1>🎋 AGI Research Impact Dashboard</h1>
<p class="subtitle">ONIZUKA AGI Co. — Democratizing AGI Knowledge<br>
Generated: {metrics["generated_at"]}</p>

<div class="grid">
  <div class="card">
    <div class="label">Total Papers</div>
    <div class="value red">{metrics["total_papers"]}</div>
  </div>
  <div class="card">
    <div class="label">Total Citations</div>
    <div class="value blue">{metrics["total_citations"]:,}</div>
  </div>
  <div class="card">
    <div class="label">Avg Citations</div>
    <div class="value green">{metrics["avg_citations"]}</div>
  </div>
  <div class="card">
    <div class="label">Max Citations</div>
    <div class="value gold">{metrics["max_citations"]:,}</div>
  </div>
  <div class="card">
    <div class="label">With GitHub Repo</div>
    <div class="value blue">{metrics["github_papers"]}</div>
  </div>
</div>

<h2>🏆 Top Cited Papers</h2>
<div class="card" style="overflow-x:auto">
<table>
<tr><th>#</th><th>Title</th><th>Citations</th><th>Date</th></tr>
{top_papers_rows}
</table>
</div>

<div class="cols">
<div>
<h2>👤 Top Authors (Papers)</h2>
<div class="card">
<table>
<tr><th>Author</th><th>Papers</th></tr>
{top_authors_rows}
</table>
</div>

<h2>🔥 Top Authors (Citations)</h2>
<div class="card">
<table>
<tr><th>Author</th><th>Citations</th></tr>
{top_cited_authors_rows}
</table>
</div>
</div>

<div>
<h2>🏷️ Topic Distribution</h2>
<div class="card">
{topic_bars}
</div>

<h2>🏢 Top Organizations</h2>
<div class="card">
<table>
<tr><th>Organization</th><th>Papers</th></tr>
{org_rows}
</table>
</div>
</div>
</div>

<h2>📅 Publication Timeline</h2>
<div class="card">
<table>
<tr><th>Month</th><th>Papers</th></tr>
{timeline_rows}
</table>
</div>

<footer>
🎋 ONIZUKA AGI Co. — <a href="https://github.com/onizuka-agi-co" style="color:{c["blue"]}">GitHub</a>
</footer>

</body>
</html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="AGI Research Impact Dashboard")
    parser.add_argument("--output", default=str(PROJECT_ROOT / "dashboard.html"),
                        help="Output HTML file path")
    parser.add_argument("--serve", action="store_true",
                        help="Start HTTP server after generating")
    parser.add_argument("--port", type=int, default=8050, help="Server port")
    args = parser.parse_args()

    papers, graph = load_data()
    if not papers:
        print("Error: No papers found in cache. Run auto_update.py first.")
        sys.exit(1)

    print(f"Loaded {len(papers)} papers")
    metrics = compute_metrics(papers)
    html = generate_html(metrics)

    output = Path(args.output)
    output.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {output}")

    if args.serve:
        import http.server
        import socketserver
        os.chdir(output.parent)
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", args.port), handler) as httpd:
            print(f"Serving at http://localhost:{args.port}/{output.name}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped")


if __name__ == "__main__":
    main()
