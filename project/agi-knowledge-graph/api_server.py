#!/usr/bin/env python3
"""
AGI Knowledge Graph API Server

FastAPI-based REST API for the AGI Knowledge Graph.

Usage:
    python api_server.py                    # Start on port 8002
    python api_server.py --port 9000        # Custom port

Endpoints:
    GET /              - API info
    GET /health        - Health check
    GET /stats         - Graph statistics
    GET /search?q=...  - Search papers
    GET /coauthors?author=...  - Co-author network
    GET /graph         - Full graph export (JSON)
    POST /rebuild      - Rebuild graph from cache
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from graph_engine import KnowledgeGraph

try:
    from fastapi import FastAPI, Query
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Install dependencies: pip install fastapi uvicorn")
    sys.exit(1)

app = FastAPI(
    title="AGI Knowledge Graph API",
    description="REST API for querying the AGI Knowledge Graph",
    version="2.0.0",
)

kg = KnowledgeGraph()


@app.on_event("startup")
async def startup():
    """Load graph on startup."""
    kg.load_from_cache()
    kg.build_graph()


@app.get("/")
async def root():
    return {
        "name": "AGI Knowledge Graph API",
        "version": "2.0.0",
        "endpoints": ["/health", "/stats", "/search", "/coauthors", "/graph", "/rebuild"],
        "papers_loaded": len(kg.papers),
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "papers": len(kg.papers),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/stats")
async def stats():
    return kg.get_stats()


@app.get("/search")
async def search(q: str = Query(..., description="Search query"), limit: int = Query(20, ge=1, le=100)):
    results = kg.search_papers(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}


@app.get("/coauthors")
async def coauthors(author: str = Query(..., description="Author name"), min_collabs: int = Query(1, ge=1)):
    results = kg.get_coauthors(author, min_collabs=min_collabs)
    if not results:
        return JSONResponse(status_code=404, content={"error": f"Author '{author}' not found"})
    return {"author": author, "coauthors": [{"name": r[0], "collaborations": r[1]} for r in results]}


@app.get("/graph")
async def graph_export():
    output = kg.export_json()
    return output if isinstance(output, dict) else {"data": output}


@app.post("/rebuild")
async def rebuild():
    """Rebuild graph from papers cache."""
    kg.load_from_cache()
    kg.build_graph()
    return {"status": "rebuilt", "papers": len(kg.papers)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGI Knowledge Graph API Server")
    parser.add_argument("--port", type=int, default=8002, help="Port to run on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port)
