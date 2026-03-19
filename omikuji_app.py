#!/usr/bin/env python3
"""Simple CLI omikuji app."""

import random

OMIKUJI_RESULTS = {
    "大吉": "素晴らしい一日になりそうです！新しいことに挑戦するのに最適です。",
    "中吉": "順調な運気です。焦らず進めば良い結果がついてきます。",
    "小吉": "小さな幸運が重なる日です。身近な嬉しさを大切にしましょう。",
    "吉": "安定した運勢です。いつも通りの積み重ねが力になります。",
    "末吉": "これから運気が上向いていきます。丁寧な準備が鍵です。",
    "凶": "無理をせず慎重に。休息を取ることで流れが変わります。",
    "大凶": "試練の日かもしれません。深呼吸して、一歩ずつ進みましょう。",
}


def main() -> None:
    result = random.choice(list(OMIKUJI_RESULTS.keys()))
    message = OMIKUJI_RESULTS[result]

    print("🎉 おみくじ 🎉")
    print(f"結果: {result}")
    print(f"運勢: {message}")


if __name__ == "__main__":
    main()
