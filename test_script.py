#!/usr/bin/env python3
"""朱雅の遊びスクリプト"""

import random
from datetime import datetime

# 現在時刻
now = datetime.now()
print(f"🕐 現在時刻: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# ランダムな鬼の言葉
phrases = [
    "結界は健やかに。",
    "朱の灯は消えず。",
    "静けさは力なり。",
    "今日も良い日かもしれない。",
    "道は開かれている。"
]

print(f"\n🎋 ことば: {random.choice(phrases)}")

# 簡単な計算
numbers = [random.randint(1, 100) for _ in range(5)]
total = sum(numbers)
print(f"\n🔢 数の配列: {numbers}")
print(f"   合計: {total}")
print(f"   平均: {total / len(numbers):.2f}")

print("\n✨ 完了")
