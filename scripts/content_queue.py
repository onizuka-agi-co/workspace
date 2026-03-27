#!/usr/bin/env python3
"""
Content Queue - コンテンツキューマネージャー

自動生成されたコンテンツのキューイング・スケジュール投稿管理
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import argparse

# Workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
QUEUE_DB = DATA_DIR / "content_queue.db"


def init_db():
    """Initialize content queue database."""
    QUEUE_DB.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            content_type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT,
            image_url TEXT,
            explanation TEXT,
            metadata TEXT,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            scheduled_time TEXT,
            posted_time TEXT,
            engagement_data TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_status ON content_queue(status)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_scheduled ON content_queue(scheduled_time)
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {QUEUE_DB}")


def add_to_queue(
    source: str,
    content_type: str,
    title: str,
    summary: str = "",
    image_url: str = "",
    explanation: str = "",
    metadata: dict = None,
    priority: int = 1,
    scheduled_time: str = None
) -> int:
    """Add content to queue."""
    init_db()
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO content_queue 
        (source, content_type, title, summary, image_url, explanation, metadata, priority, scheduled_time, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        source,
        content_type,
        title,
        summary,
        image_url,
        explanation,
        json.dumps(metadata or {}),
        priority,
        scheduled_time,
        now,
        now
    ))
    
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Added to queue: [{item_id}] {title[:50]}")
    return item_id


def get_pending_items(limit: int = 10) -> List[Dict]:
    """Get pending items from queue."""
    init_db()
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM content_queue
        WHERE status = 'pending'
        ORDER BY priority DESC, created_at ASC
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "source": row[1],
            "content_type": row[2],
            "title": row[3],
            "summary": row[4],
            "image_url": row[5],
            "explanation": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
            "status": row[8],
            "priority": row[9],
            "scheduled_time": row[10],
            "posted_time": row[11],
            "engagement_data": json.loads(row[12]) if row[12] else {},
            "created_at": row[13],
            "updated_at": row[14]
        })
    
    return items


def get_scheduled_items() -> List[Dict]:
    """Get items scheduled for now or past."""
    init_db()
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        SELECT * FROM content_queue
        WHERE status = 'scheduled' AND scheduled_time <= ?
        ORDER BY scheduled_time ASC
    """, (now,))
    
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "source": row[1],
            "content_type": row[2],
            "title": row[3],
            "summary": row[4],
            "image_url": row[5],
            "explanation": row[6],
            "metadata": json.loads(row[7]) if row[7] else {},
            "status": row[8],
            "priority": row[9],
            "scheduled_time": row[10],
            "posted_time": row[11],
            "engagement_data": json.loads(row[12]) if row[12] else {},
            "created_at": row[13],
            "updated_at": row[14]
        })
    
    return items


def update_status(item_id: int, status: str, posted_time: str = None, engagement_data: dict = None):
    """Update item status."""
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if posted_time:
        cursor.execute("""
            UPDATE content_queue
            SET status = ?, posted_time = ?, updated_at = ?
            WHERE id = ?
        """, (status, posted_time, now, item_id))
    elif engagement_data:
        cursor.execute("""
            UPDATE content_queue
            SET status = ?, engagement_data = ?, updated_at = ?
            WHERE id = ?
        """, (status, json.dumps(engagement_data), now, item_id))
    else:
        cursor.execute("""
            UPDATE content_queue
            SET status = ?, updated_at = ?
            WHERE id = ?
        """, (status, now, item_id))
    
    conn.commit()
    conn.close()
    print(f"✅ Updated [{item_id}] status: {status}")


def schedule_item(item_id: int, scheduled_time: str):
    """Schedule item for posting at specific time."""
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE content_queue
        SET status = 'scheduled', scheduled_time = ?, updated_at = ?
        WHERE id = ?
    """, (scheduled_time, now, item_id))
    
    conn.commit()
    conn.close()
    print(f"✅ Scheduled [{item_id}] for {scheduled_time}")


def get_stats() -> Dict:
    """Get queue statistics."""
    init_db()
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    stats = {}
    
    # Total by status
    cursor.execute("""
        SELECT status, COUNT(*) FROM content_queue
        GROUP BY status
    """)
    stats["by_status"] = dict(cursor.fetchall())
    
    # Total by source
    cursor.execute("""
        SELECT source, COUNT(*) FROM content_queue
        GROUP BY source
    """)
    stats["by_source"] = dict(cursor.fetchall())
    
    # Total count
    cursor.execute("SELECT COUNT(*) FROM content_queue")
    stats["total"] = cursor.fetchone()[0]
    
    conn.close()
    
    return stats


def list_items(status: str = None, limit: int = 20):
    """List items in queue."""
    init_db()
    
    conn = sqlite3.connect(str(QUEUE_DB))
    cursor = conn.cursor()
    
    if status:
        cursor.execute("""
            SELECT id, source, title, status, priority, scheduled_time, created_at
            FROM content_queue
            WHERE status = ?
            ORDER BY priority DESC, created_at DESC
            LIMIT ?
        """, (status, limit))
    else:
        cursor.execute("""
            SELECT id, source, title, status, priority, scheduled_time, created_at
            FROM content_queue
            ORDER BY priority DESC, created_at DESC
            LIMIT ?
        """, (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    print("\n📋 Content Queue")
    print("=" * 80)
    
    for row in rows:
        item_id, source, title, status, priority, scheduled, created = row
        title_short = title[:50] + "..." if len(title) > 50 else title
        print(f"[{item_id:3d}] [{status:10s}] P{priority} {source:15s} {title_short}")
        if scheduled:
            print(f"       Scheduled: {scheduled}")
    
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Content Queue Manager - コンテンツキュー管理"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init
    subparsers.add_parser("init", help="Initialize database")
    
    # Stats
    subparsers.add_parser("stats", help="Show queue statistics")
    
    # List
    list_parser = subparsers.add_parser("list", help="List items in queue")
    list_parser.add_argument("--status", type=str, help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=20, help="Limit results")
    
    # Add (for testing)
    add_parser = subparsers.add_parser("add", help="Add item to queue (test)")
    add_parser.add_argument("--source", required=True, help="Content source")
    add_parser.add_argument("--title", required=True, help="Content title")
    add_parser.add_argument("--type", default="paper", help="Content type")
    add_parser.add_argument("--priority", type=int, default=1, help="Priority (1-3)")
    
    # Schedule
    schedule_parser = subparsers.add_parser("schedule", help="Schedule item for posting")
    schedule_parser.add_argument("item_id", type=int, help="Item ID")
    schedule_parser.add_argument("--time", required=True, help="Scheduled time (ISO format)")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
    elif args.command == "stats":
        stats = get_stats()
        print("\n📊 Queue Statistics")
        print("=" * 40)
        print(f"Total items: {stats['total']}")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status}: {count}")
        print("\nBy Source:")
        for source, count in stats["by_source"].items():
            print(f"  {source}: {count}")
    elif args.command == "list":
        list_items(status=args.status, limit=args.limit)
    elif args.command == "add":
        add_to_queue(
            source=args.source,
            content_type=args.type,
            title=args.title,
            priority=args.priority
        )
    elif args.command == "schedule":
        schedule_item(args.item_id, args.time)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
