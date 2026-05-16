#!/usr/bin/env python3
"""
🔗 AGI論文チェーンオブソート自動検知システム (Citation Sentinel)

Uses OpenAlex API (free, no key required) for citation data.

Usage:
  python3 citation_sentinel.py trending       # Show trending AGI papers
  python3 citation_sentinel.py check --doi <DOI>  # Check specific paper
  python3 citation_sentinel.py baseline       # Store citation baseline
  python3 citation_sentinel.py report         # Generate spike detection report
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse

# --- Config ---
DATA_DIR = Path(__file__).parent / "data"
BASELINE_FILE = DATA_DIR / "citation_baseline.json"
REPORT_FILE = DATA_DIR / "latest_report.json"

OPENALEX_BASE = "https://api.openalex.org"
MAILTO = "onizuka.renjiii+onizuka-agi@gmail.com"  # polite pool

AGI_CONCEPTS = [
    "artificial general intelligence AGI",
    "AGI alignment safety",
    "large language model reasoning capability",
    "foundation model scaling laws",
    "AI agent autonomy planning",
    "world model embodied AI",
]

def api_get(url, params=None):
    """Make a GET request to OpenAlex API."""
    if params is None:
        params = {}
    params["mailto"] = MAILTO
    qs = urllib.parse.urlencode(params)
    full_url = f"{url}?{qs}" if "?" not in url else f"{url}&{qs}"

    req = urllib.request.Request(full_url, headers={"User-Agent": "CitationSentinel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Request error: {e}", file=sys.stderr)
        return None

def search_works(query, limit=25, sort="cited_by_count:desc"):
    """Search works on OpenAlex."""
    data = api_get(f"{OPENALEX_BASE}/works", {
        "search": query,
        "per_page": limit,
        "sort": sort,
        "filter": "from_publication_date:2024-01-01",
    })
    if data and "results" in data:
        return data["results"]
    return []

def get_work(openalex_id):
    """Get a single work by OpenAlex ID or DOI."""
    data = api_get(f"{OPENALEX_BASE}/works/{openalex_id}")
    return data

def load_baseline():
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}

def save_baseline(baseline):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    baseline["_updated"] = datetime.now(timezone.utc).isoformat()
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2, ensure_ascii=False))

def save_report(report):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, indent=2, ensure_ascii=False))

def collect_papers():
    """Collect papers from multiple AGI-related searches."""
    seen = set()
    papers = []

    for query in AGI_CONCEPTS:
        results = search_works(query, limit=15)
        for p in results:
            oid = p.get("id", "")
            if oid and oid not in seen:
                seen.add(oid)
                papers.append({
                    "id": oid,
                    "title": p.get("title", ""),
                    "citationCount": p.get("cited_by_count", 0),
                    "year": p.get("publication_year"),
                    "doi": p.get("doi", ""),
                    "url": p.get("id", ""),
                    "openAccess": p.get("open_access", {}).get("oa_url", ""),
                })
        time.sleep(0.5)

    papers.sort(key=lambda x: x.get("citationCount", 0), reverse=True)
    return papers

def detect_spikes(papers, baseline):
    """Compare current citations against baseline to detect spikes."""
    spikes = []
    for p in papers:
        pid = p["id"]
        current = p.get("citationCount", 0)
        prev = baseline.get(pid, {}).get("citationCount", None)

        if prev is not None and prev > 0:
            delta = current - prev
            pct = (delta / prev) * 100
            if delta >= 5 or pct >= 10:
                spikes.append({
                    "id": pid,
                    "title": p.get("title", "Unknown"),
                    "citationCount": current,
                    "previousCount": prev,
                    "delta": delta,
                    "pctChange": round(pct, 1),
                    "year": p.get("year"),
                    "doi": p.get("doi", ""),
                })

    spikes.sort(key=lambda x: x["delta"], reverse=True)
    return spikes

def cmd_trending(args):
    """Show trending AGI papers."""
    print("🔍 Collecting AGI papers from OpenAlex...")
    papers = collect_papers()

    print(f"\n📊 Found {len(papers)} papers\n")
    print(f"{'Citations':>10} | {'Year':>4} | Title")
    print("-" * 80)
    for p in papers[:20]:
        title = (p.get("title") or "N/A")[:60]
        print(f"{p.get('citationCount',0):>10} | {p.get('year','?'):>4} | {title}")
    return papers

def cmd_check(args):
    """Check a specific paper by DOI."""
    paper = get_work(f"DOI:{args.doi}")
    if not paper:
        print(f"Paper not found: {args.doi}")
        return
    print(f"Title: {paper.get('title')}")
    print(f"Citations: {paper.get('cited_by_count')}")
    print(f"Year: {paper.get('publication_year')}")
    print(f"DOI: {paper.get('doi')}")
    print(f"URL: {paper.get('id')}")

def cmd_baseline(args):
    """Store current citation counts as baseline."""
    print("📦 Building citation baseline...")
    papers = collect_papers()

    baseline = {}
    for p in papers:
        baseline[p["id"]] = {
            "title": p.get("title", ""),
            "citationCount": p.get("citationCount", 0),
            "year": p.get("year"),
        }

    save_baseline(baseline)
    print(f"✅ Baseline saved: {len(baseline)} papers → {BASELINE_FILE}")

def cmd_report(args):
    """Generate full report with spike detection."""
    print("📋 Generating citation spike report...")
    papers = collect_papers()
    baseline = load_baseline()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_from": baseline.get("_updated", None),
        "total_papers": len(papers),
        "spikes": [],
        "top_cited": [
            {
                "title": p.get("title", ""),
                "citations": p.get("citationCount", 0),
                "year": p.get("year"),
                "doi": p.get("doi", ""),
            }
            for p in papers[:10]
        ],
    }

    if baseline and "_updated" in baseline:
        report["spikes"] = detect_spikes(papers, baseline)

    save_report(report)

    print(f"\n📊 Report Summary")
    print(f"   Papers analyzed: {report['total_papers']}")
    print(f"   Citation spikes: {len(report['spikes'])}")

    if report["spikes"]:
        print(f"\n🔥 Citation Spikes:")
        for s in report["spikes"][:10]:
            print(f"   +{s['delta']} ({s['pctChange']}%) | {s['title'][:60]}")

    print(f"\n🏆 Top Cited:")
    for p in report["top_cited"][:5]:
        print(f"   {p['citations']:>6} | {p.get('year','?')} | {p['title'][:55]}")

    return report

def main():
    parser = argparse.ArgumentParser(description="🔗 Citation Sentinel - AGI論文引用スパイク検知")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("trending", help="Show trending AGI papers")
    sub.add_parser("baseline", help="Store citation baseline")
    sub.add_parser("report", help="Generate spike detection report")

    chk = sub.add_parser("check", help="Check specific paper by DOI")
    chk.add_argument("--doi", required=True, help="Paper DOI")

    args = parser.parse_args()
    cmds = {
        "trending": cmd_trending,
        "baseline": cmd_baseline,
        "report": cmd_report,
        "check": cmd_check,
    }
    fn = cmds.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
