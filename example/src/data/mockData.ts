export interface BusinessData {
  id: string;
  name: string;
  blurredName: string;
  prefecture: string;
  area: string;
  businessType: 'デリヘル' | '箱ヘル' | 'NSソープ' | 'S着ソープ' | 'DC';
  spec: '低スペ' | 'スタンダード' | 'ハイスペ';
  utilizationRate: number;
  weeklyData: {
    week: string;
    rate: number;
  }[];
  monthlyData: {
    month: string;
    rate: number;
  }[];
}

export const mockBusinesses: BusinessData[] = [
  {
    id: '1',
    name: 'プレミアムクラブ銀座',
    blurredName: 'プ●●●●●ブ銀座',
    prefecture: '東京都',
    area: '関東',
    businessType: 'デリヘル',
    spec: 'ハイスペ',
    utilizationRate: 94,
    weeklyData: [
      { week: '先週', rate: 94 },
      { week: '2週間前', rate: 89 },
      { week: '3週間前', rate: 91 },
      { week: '4週間前', rate: 87 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 90 },
      { month: '過去3ヶ月', rate: 88 }
    ]
  },
  {
    id: '2',
    name: 'ロイヤルスパ大阪',
    blurredName: 'ロ●●●●大阪',
    prefecture: '大阪府',
    area: '関西',
    businessType: 'NSソープ',
    spec: 'ハイスペ',
    utilizationRate: 91,
    weeklyData: [
      { week: '先週', rate: 91 },
      { week: '2週間前', rate: 88 },
      { week: '3週間前', rate: 85 },
      { week: '4週間前', rate: 89 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 88 },
      { month: '過去3ヶ月', rate: 86 }
    ]
  },
  {
    id: '3',
    name: 'エレガントラウンジ',
    blurredName: 'エ●●●●ラウンジ',
    prefecture: '愛知県',
    area: '中部',
    businessType: '箱ヘル',
    spec: 'スタンダード',
    utilizationRate: 88,
    weeklyData: [
      { week: '先週', rate: 88 },
      { week: '2週間前', rate: 84 },
      { week: '3週間前', rate: 86 },
      { week: '4週間前', rate: 82 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 85 },
      { month: '過去3ヶ月', rate: 83 }
    ]
  },
  {
    id: '4',
    name: 'ビューティークラブ',
    blurredName: 'ビ●●●●クラブ',
    prefecture: '福岡県',
    area: '九州・沖縄',
    businessType: 'DC',
    spec: 'スタンダード',
    utilizationRate: 85,
    weeklyData: [
      { week: '先週', rate: 85 },
      { week: '2週間前', rate: 81 },
      { week: '3週間前', rate: 83 },
      { week: '4週間前', rate: 79 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 82 },
      { month: '過去3ヶ月', rate: 80 }
    ]
  },
  {
    id: '5',
    name: 'ラグジュアリーサロン',
    blurredName: 'ラ●●●●サロン',
    prefecture: '宮城県',
    area: '東北',
    businessType: 'S着ソープ',
    spec: 'ハイスペ',
    utilizationRate: 82,
    weeklyData: [
      { week: '先週', rate: 82 },
      { week: '2週間前', rate: 78 },
      { week: '3週間前', rate: 80 },
      { week: '4週間前', rate: 76 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 79 },
      { month: '過去3ヶ月', rate: 77 }
    ]
  },
  {
    id: '6',
    name: 'スイートハーツ',
    blurredName: 'ス●●●●ハーツ',
    prefecture: '北海道',
    area: '北海道',
    businessType: 'デリヘル',
    spec: '低スペ',
    utilizationRate: 79,
    weeklyData: [
      { week: '先週', rate: 79 },
      { week: '2週間前', rate: 75 },
      { week: '3週間前', rate: 77 },
      { week: '4週間前', rate: 73 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 76 },
      { month: '過去3ヶ月', rate: 74 }
    ]
  },
  {
    id: '7',
    name: 'パラダイスクラブ',
    blurredName: 'パ●●●●クラブ',
    prefecture: '広島県',
    area: '中国',
    businessType: '箱ヘル',
    spec: 'スタンダード',
    utilizationRate: 76,
    weeklyData: [
      { week: '先週', rate: 76 },
      { week: '2週間前', rate: 72 },
      { week: '3週間前', rate: 74 },
      { week: '4週間前', rate: 70 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 73 },
      { month: '過去3ヶ月', rate: 71 }
    ]
  },
  {
    id: '8',
    name: 'ドリームランド',
    blurredName: 'ド●●●ランド',
    prefecture: '香川県',
    area: '四国',
    businessType: 'DC',
    spec: '低スペ',
    utilizationRate: 73,
    weeklyData: [
      { week: '先週', rate: 73 },
      { week: '2週間前', rate: 69 },
      { week: '3週間前', rate: 71 },
      { week: '4週間前', rate: 67 }
    ],
    monthlyData: [
      { month: '過去1ヶ月', rate: 70 },
      { month: '過去3ヶ月', rate: 68 }
    ]
  }
];

export const mockTwitterPosts = [
  {
    id: '1',
    content: '最新の稼働率データを更新しました！今週は関東エリアが好調です 📊',
    timestamp: '2時間前'
  },
  {
    id: '2', 
    content: 'お店選びで迷っている方、LINE相談受付中です💬 稼働率だけでなく、働きやすさも重要です！',
    timestamp: '5時間前'
  },
  {
    id: '3',
    content: '新規登録ユーザー様には詳細データを公開中✨ ログインして最新情報をチェック！',
    timestamp: '1日前'
  }
];