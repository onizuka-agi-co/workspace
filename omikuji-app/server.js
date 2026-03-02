const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// 運勢データ
const fortunes = [
  {
    name: "大吉",
    messages: [
      "素晴らしい一日になります",
      "願い事が叶うでしょう",
      "幸運が舞い込みます",
      "すべてが上手くいきます",
      "最高の一日を迎えられます"
    ],
    luckyItems: ["赤いもの", "四つ葉のクローバー", "金色のもの", "星柄のアイテム", "ハートの形"]
  },
  {
    name: "中吉",
    messages: [
      "良いことが起こる予感です",
      "努力が実を結びます",
      "周りからの評価が上がります",
      "穏やかな幸せが訪れます"
    ],
    luckyItems: ["青いもの", "本", "コーヒー", "丸いもの"]
  },
  {
    name: "小吉",
    messages: [
      "小さな喜びが見つかります",
      "身近な人との絆が深まります",
      "のんびり過ごすのが吉です",
      "新しい発見があるでしょう"
    ],
    luckyItems: ["緑のもの", "お茶", "手帳", "キーホルダー"]
  },
  {
    name: "吉",
    messages: [
      "平穏な一日になります",
      "計画通りに進みます",
      "無理せずマイペースで",
      "良い知らせが届くかも"
    ],
    luckyItems: ["白いもの", "ペン", "スマホケース", "マスク"]
  },
  {
    name: "末吉",
    messages: [
      "地道な努力が大切です",
      "焦らずゆっくりと",
      "将来の種まきの時期です",
      "助け合いが大事になります"
    ],
    luckyItems: ["茶色いもの", "靴", "傘", "財布"]
  },
  {
    name: "凶",
    messages: [
      "無理は禁物です",
      "慎重に行動しましょう",
      "今日は休むのが吉です",
      "周りの意見を聞いてみて"
    ],
    luckyItems: ["黒いもの", "水", "薬", "タオル"]
  },
  {
    name: "大凶",
    messages: [
      "家でゆっくり過ごしましょう",
      "衝動買いは控えめに",
      "明日はきっと良くなります",
      "気をつけて行動してください"
    ],
    luckyItems: ["灰色のもの", "枕", "音楽", "柔らかいもの"]
  }
];

// ランダムに要素を選ぶ関数
function getRandomElement(array) {
  return array[Math.floor(Math.random() * array.length)];
}

// おみくじを引く関数
function drawOmikuji() {
  // 大吉の確率を少し上げて、凶・大凶を減らす（実用的な配分）
  const weights = [25, 20, 15, 15, 12, 8, 5]; // 大吉〜大凶の確率配分
  const random = Math.random() * 100;
  let cumulative = 0;
  let selectedIndex = 0;

  for (let i = 0; i < weights.length; i++) {
    cumulative += weights[i];
    if (random < cumulative) {
      selectedIndex = i;
      break;
    }
  }

  const fortune = fortunes[selectedIndex];
  return {
    fortune: fortune.name,
    message: getRandomElement(fortune.messages),
    lucky_item: getRandomElement(fortune.luckyItems)
  };
}

// GET /omikuji エンドポイント
app.get('/omikuji', (req, res) => {
  const result = drawOmikuji();
  res.json(result);
});

// ルートエンドポイント
app.get('/', (req, res) => {
  res.json({
    message: "おみくじAPIへようこそ",
    endpoint: "/omikuji",
    usage: "GET /omikuji でおみくじを引けます"
  });
});

// サーバー起動
app.listen(PORT, () => {
  console.log(`おみくじサーバーが起動しました: http://localhost:${PORT}`);
});

module.exports = app;
