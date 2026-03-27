#!/usr/bin/env python3
"""
Engagement Tracker - 投稿エンゲージメント追跡

X投稿の反応（いいね、RT、閲覧数）を追跡・分析
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import argparse
import sys

# Workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent
DATA_DIR = WORKSPACE_ROOT / "data"
ENGAGEMENT_DB = DATA_DIR / "engagement.db"


def init_db():
    """Initialize engagement database."""
    ENGAGEMENT_DB.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(ENGAGEMENT_DB))
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS engagement (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tweet_id TEXT NOT NULL UNIQUE,
            content_id INTEGER,
            title TEXT,
            posted_at TEXT NOT NULL,
            platform TEXT DEFAULT 'x',
            likes INTEGER DEFAULT 0,
            retweets INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0,
            quotes INTEGER DEFAULT 0,
            bookmarks INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            last_updated TEXT NOT NULL,
            FOREIGN KEY (content_id) REFERENCES content_queue(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tweet_id ON engagement(tweet_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_posted_at ON engagement(posted_at)
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ Database initialized: {ENGAGEMENT_DB}")


def track_engagement(
    tweet_id: str,
    content_id: int = None,
    title: str = "",
    posted_at: str = None,
    likes: int = 0,
    retweets: int = 0,
    replies: int = 0,
    views: int = 0,
    quotes: int = 0,
    bookmarks: int = 0
) -> int:
    """Track or update engagement for a tweet."""
    init_db()
    
    conn = sqlite3.connect(str(ENGAGEMENT_DB))
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    posted_at = posted_at or now
    
    # Calculate engagement rate
    engagement_rate = 0.0
    if views > 0:
        engagement_rate = ((likes + retweets + replies + quotes + bookmarks) / views) * 100
    
    # Check if exists
    cursor.execute("SELECT id FROM engagement WHERE tweet_id = ?", (tweet_id,))
    existing = cursor.fetchone()
    
    if existing:
        # Update
        cursor.execute("""
            UPDATE engagement
            SET likes = ?, retweets = ?, replies = ?, views = ?, quotes = ?, bookmarks = ?,
                engagement_rate = ?, last_updated = ?
            WHERE tweet_id = ?
        """, (likes, retweets, replies, views, quotes, bookmarks, engagement_rate, now, tweet_id))
        
        item_id = existing[0]
    else:
        # Insert
        cursor.execute("""
            INSERT INTO engagement
            (tweet_id, content_id, title, posted_at, likes, retweets, replies, views, quotes, bookmarks, engagement_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tweet_id, content_id, title, posted_at, likes, retweets, replies, views, quotes, bookmarks, engagement_rate, now))
        
        item_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    print(f"✅ Tracked [{tweet_id}]: {likes} likes, {retweets} RTs, {views} views ({engagement_rate:.2f}% engagement)")
    return item_id


def get_engagement(tweet_id: str) -> Optional[Dict]:
    """Get engagement data for a tweet."""
    init_db()
    
    conn = sqlite3.connect(str(ENGAGEMENT_DB))
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM engagement WHERE tweet_id = ?", (tweet_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row[0],
            "tweet_id": row[1],
            "content_id": row[2],
            "title": row[3],
            "posted_at": row[4],
            "platform": row[5],
            "likes": row[6],
            "retweets": row[7],
            "replies": row[8],
            "views": row[9],
            "quotes": row[10],
            "bookmarks": row[11],
            "engagement_rate": row[12],
            "last_updated": row[13]
        }
    
    return None


def get_top_performing(limit: int = 10, days: int = 30) -> List[Dict]:
    """Get top performing tweets."""
    init_db()
    
    conn = sqlite3.connect(str(ENGAGEMENT_DB))
    cursor = conn.cursor()
    
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    cursor.execute("""
        SELECT * FROM engagement
        WHERE posted_at >= ?
        ORDER BY engagement_rate DESC
        LIMIT ?
    """, (since, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    items = []
    for row in rows:
        items.append({
            "id": row[0],
            "tweet_id": row[1],
            "content_id": row[2],
            "title": row[3],
            "posted_at": row[4],
            "platform": row[5],
            "likes": row[6],
            "retweets": row[7],
            "replies": row[8],
            "views": row[9],
            "quotes": row[10],
            "bookmarks": row[11],
            "engagement_rate": row[12],
            "last_updated": row[13]
        })
    
    return items


def get_stats(days: int = 30) -> Dict:
    """Get engagement statistics."""
    init_db()
    
    conn = sqlite3.connect(str(ENGAGEMENT_DB))
    cursor = conn.cursor()
    
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    stats = {}
    
    # Total tweets
    cursor.execute("SELECT COUNT(*) FROM engagement WHERE posted_at >= ?", (since,))
    stats["total_tweets"] = cursor.fetchone()[0]
    
    # Average engagement
    cursor.execute("""
        SELECT AVG(engagement_rate), AVG(likes), AVG(retweets), AVG(views)
        FROM engagement
        WHERE posted_at >= ?
    """, (since,))
    row = cursor.fetchone()
    stats["avg_engagement_rate"] = row[0] or 0.0
    stats["avg_likes"] = row[1] or 0.0
    stats["avg_retweets"] = row[2] or 0.0
    stats["avg_views"] = row[3] or 0.0
    
    # Total engagement
    cursor.execute("""
        SELECT SUM(likes), SUM(retweets), SUM(views)
        FROM engagement
        WHERE posted_at >= ?
    """, (since,))
    row = cursor.fetchone()
    stats["total_likes"] = row[0] or 0
    stats["total_retweets"] = row[1] or 0
    stats["total_views"] = row[2] or 0
    
    # Best performing
    cursor.execute("""
        SELECT tweet_id, title, engagement_rate
        FROM engagement
        WHERE posted_at >= ?
        ORDER BY engagement_rate DESC
        LIMIT 1
    """, (since,))
    row = cursor.fetchone()
    if row:
        stats["best_performing"] = {
            "tweet_id": row[0],
            "title": row[1],
            "engagement_rate": row[2]
        }
    
    conn.close()
    
    return stats


def generate_report(days: int = 7):
    """Generate engagement report."""
    stats = get_stats(days=days)
    top = get_top_performing(limit=5, days=days)
    
    print(f"\n📊 Engagement Report (Last {days} days)")
    print("=" * 60)
    print(f"Total Tweets: {stats['total_tweets']}")
    print(f"\nAverages:")
    print(f"  Engagement Rate: {stats['avg_engagement_rate']:.2f}%")
    print(f"  Likes: {stats['avg_likes']:.1f}")
    print(f"  Retweets: {stats['avg_retweets']:.1f}")
    print(f"  Views: {stats['avg_views']:.1f}")
    print(f"\nTotals:")
    print(f"  Likes: {stats['total_likes']}")
    print(f"  Retweets: {stats['total_retweets']}")
    print(f"  Views: {stats['total_views']}")
    
    if stats.get("best_performing"):
        best = stats["best_performing"]
        print(f"\n🏆 Best Performing:")
        print(f"  {best['title'][:50]}")
        print(f"  Engagement: {best['engagement_rate']:.2f}%")
    
    print(f"\n🔥 Top 5 Tweets:")
    for i, item in enumerate(top, 1):
        print(f"\n{i}. {item['title'][:50]}")
        print(f"   Engagement: {item['engagement_rate']:.2f}%")
        print(f"   {item['likes']} likes, {item['retweets']} RTs, {item['views']} views")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Engagement Tracker - 投稿エンゲージメント追跡"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Init
    subparsers.add_parser("init", help="Initialize database")
    
    # Track
    track_parser = subparsers.add_parser("track", help="Track engagement")
    track_parser.add_argument("--tweet-id", required=True, help="Tweet ID")
    track_parser.add_argument("--title", default="", help="Content title")
    track_parser.add_argument("--likes", type=int, default=0, help="Likes count")
    track_parser.add_argument("--retweets", type=int, default=0, help="Retweets count")
    track_parser.add_argument("--views", type=int, default=0, help="Views count")
    track_parser.add_argument("--replies", type=int, default=0, help="Replies count")
    
    # Stats
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    
    # Report
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--days", type=int, default=7, help="Days to report")
    
    # Top
    top_parser = subparsers.add_parser("top", help="Show top performing")
    top_parser.add_argument("--limit", type=int, default=10, help="Number of results")
    top_parser.add_argument("--days", type=int, default=30, help="Days to analyze")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
    elif args.command == "track":
        track_engagement(
            tweet_id=args.tweet_id,
            title=args.title,
            likes=args.likes,
            retweets=args.retweets,
            views=args.views,
            replies=args.replies
        )
    elif args.command == "stats":
        stats = get_stats(days=args.days)
        print(json.dumps(stats, indent=2))
    elif args.command == "report":
        generate_report(days=args.days)
    elif args.command == "top":
        top = get_top_performing(limit=args.limit, days=args.days)
        for item in top:
            print(f"\n[{item['tweet_id']}] {item['title'][:50]}")
            print(f"  {item['engagement_rate']:.2f}% - {item['likes']} likes, {item['retweets']} RTs")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
