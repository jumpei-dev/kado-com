import { ArrowLeft } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';

interface BusinessData {
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

interface ShopDetailProps {
  business: BusinessData;
  isLoggedIn: boolean;
  onBack: () => void;
}

export function ShopDetail({ business, isLoggedIn, onBack }: ShopDetailProps) {
  const displayName = isLoggedIn ? business.name : business.blurredName;

  const getUtilizationColor = (rate: number) => {
    if (rate >= 90) return 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border border-red-200';
    if (rate >= 80) return 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-800 border border-orange-200';
    if (rate >= 70) return 'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border border-yellow-200';
    return 'bg-gradient-to-r from-emerald-100 to-green-100 text-emerald-800 border border-emerald-200';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50/40 to-sky-50/40">
      <div className="max-w-[640px] mx-auto bg-white/95 shadow-sm min-h-screen">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-100/80 to-sky-100/80 backdrop-blur-sm px-4 py-3">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" onClick={onBack} className="p-2 text-blue-700 hover:bg-blue-50/50">
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg text-blue-700">店舗詳細</h1>
          </div>
          </div>

        <div className="px-4 py-6 space-y-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle className="text-xl">{displayName}</CardTitle>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <span>{business.area}</span>
              <span>•</span>
              <span>{business.prefecture}</span>
            </div>
            <div className="flex gap-2">
              <Badge variant="outline">{business.businessType}</Badge>
              <Badge variant="outline">{business.spec}</Badge>
            </div>
          </CardHeader>
        </Card>

        {/* Current Utilization Rate */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">現在の稼働��</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <Badge className={`${getUtilizationColor(business.utilizationRate)} text-2xl px-4 py-2`}>
                {business.utilizationRate}%
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Weekly Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">週間推移</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {business.weeklyData.map((data, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50/60 to-sky-50/60 rounded-lg border border-blue-100">
                <span className="text-sm">{data.week}</span>
                <Badge className={getUtilizationColor(data.rate)}>
                  {data.rate}%
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Monthly Data */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">月間平均</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {business.monthlyData.map((data, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50/60 to-sky-50/60 rounded-lg border border-blue-100">
                <span className="text-sm">{data.month}</span>
                <Badge className={getUtilizationColor(data.rate)}>
                  {data.rate}%
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Call to Action */}
        <Card className="bg-gradient-to-r from-blue-50/60 to-sky-50/60 border-blue-200">
          <CardContent className="p-4 text-center">
            <h3 className="mb-2">詳細情報・お店への紹介をご希望の方</h3>
            <p className="text-sm text-gray-600 mb-4">
              稼働率以外の詳細情報や、お店への紹介サポートをご提供しています
            </p>
            <Button className="w-full bg-gradient-to-r from-blue-200 to-sky-200 hover:from-blue-300 hover:to-sky-300 text-blue-800 border-0 shadow-sm">
              LINE で相談する
            </Button>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}