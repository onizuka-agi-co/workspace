#!/usr/bin/env python3
"""
AGI Papers X Poster - 論文図解をXに自動投稿
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# パス設定
WORKSPACE = Path("/config/.openclaw/workspace")
SKILLS_DIR = WORKSPACE / "skills"
PAPERS_DIR = WORKSPACE / "memory/docs/papers"
STATE_FILE = WORKSPACE / ".local/state/papers-x-poster.json"
LOG_FILE = WORKSPACE / ".local/state/papers-x-poster.log"


def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def load_state() -> dict:
    """状態読み込み"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"posted_papers": []}


def save_state(state: dict):
    """状態保存"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_unposted_papers(state: dict) -> list[Path]:
    """未投稿の論文図解を取得"""
    posted = set(state.get("posted_papers", []))
    papers = []

    # カテゴリフォルダから検索
    for category_dir in PAPERS_DIR.iterdir():
        if category_dir.is_dir() and category_dir.name not in ["2026", "category"]:
            for paper_file in category_dir.glob("*.md"):
                paper_id = paper_file.stem
                if paper_id not in posted:
                    papers.append(paper_file)

    # 日付フォルダから検索
    for year_dir in (PAPERS_DIR / "2026").glob("*"):
        if year_dir.is_dir():
            for month_dir in year_dir.glob("*"):
                if month_dir.is_dir():
                    for paper_file in month_dir.glob("*.md"):
                        paper_id = paper_file.stem
                        if paper_id not in posted:
                            papers.append(paper_file)

    # 新しい順にソート
    papers.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return papers


def extract_paper_info(paper_file: Path) -> dict:
    """論文情報を抽出"""
    content = paper_file.read_text()

    # タイトル抽出（最初の見出し）
    title = ""
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    # 要約抽出（最初の段落）
    summary = ""
    in_summary = False
    for line in content.split("\n"):
        if "要約" in line or "Summary" in line:
            in_summary = True
            continue
        if in_summary and line.strip() and not line.startswith("#"):
            summary = line.strip()
            break
        if in_summary and line.startswith("#"):
            break

    # カテゴリ
    category = paper_file.parent.name

    return {
        "id": paper_file.stem,
        "title": title,
        "summary": summary[:200] if summary else "",
        "category": category,
        "path": paper_file
    }


def post_to_x(paper_info: dict) -> bool:
    """Xに投稿"""
    log(f"Posting paper {paper_info['id']} to X...")

    # 投稿テキスト作成
    text = f"📄 {paper_info['title']}\n\n{paper_info['summary']}\n\n#ONIZUKA_AGI"

    try:
        # post-with-diagramコマンドで図解付き投稿
        result = subprocess.run(
            [
                "uv", "run",
                str(SKILLS_DIR / "x-write/scripts/x_write.py"),
                "post-with-diagram",
                text,
                "--style", "tech"
            ],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            log(f"Successfully posted: {paper_info['id']}")
            return True
        else:
            log(f"Error posting: {result.stderr[:200]}")
            # シンプルな投稿を試す
            result2 = subprocess.run(
                [
                    "uv", "run",
                    str(SKILLS_DIR / "x-write/scripts/x_write.py"),
                    "post", text
                ],
                cwd=WORKSPACE,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result2.returncode == 0:
                log(f"Successfully posted (simple): {paper_info['id']}")
                return True
            else:
                log(f"Error posting (simple): {result2.stderr[:200]}")
                return False
    except Exception as e:
        log(f"Exception: {e}")
        return False


def main():
    """メイン処理"""
    log("=== Papers X Poster Started ===")

    # 1. 状態読み込み
    state = load_state()

    # 2. 未投稿論文取得
    unposted = get_unposted_papers(state)
    log(f"Found {len(unposted)} unposted papers")

    if not unposted:
        log("No papers to post, exiting")
        return 0

    # 3. 最新の1件を投稿（1回の実行で1件のみ）
    paper_file = unposted[0]
    paper_info = extract_paper_info(paper_file)
    log(f"Processing: {paper_info['id']} - {paper_info['title'][:50]}...")

    # 4. Xに投稿
    if post_to_x(paper_info):
        # 5. 状態更新
        state["posted_papers"].append(paper_info["id"])
        # 最新100件のみ保持
        state["posted_papers"] = state["posted_papers"][-100:]
        save_state(state)
        log(f"=== Papers X Poster Completed: {paper_info['id']} posted ===")
        return 0
    else:
        log(f"=== Papers X Poster Failed: {paper_info['id']} ===")
        return 1


if __name__ == "__main__":
    sys.exit(main())
