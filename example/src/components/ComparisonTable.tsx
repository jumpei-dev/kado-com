import { X, Star } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';

interface EstablishmentData {
  id: string;
  name: string;
  area: string;
  rating: number;
  utilizationRate: number;
  priceRange: string;
  image: string;
  reviews: number;
  openHours: string;
  features: string[];
}

interface ComparisonTableProps {
  establishments: EstablishmentData[];
  onRemove: (id: string) => void;
  onClear: () => void;
}

export function ComparisonTable({ establishments, onRemove, onClear }: ComparisonTableProps) {
  if (establishments.length === 0) {
    return null;
  }

  const getUtilizationColor = (rate: number) => {
    if (rate >= 80) return 'text-red-600 bg-red-50';
    if (rate >= 60) return 'text-orange-600 bg-orange-50';
    if (rate >= 40) return 'text-yellow-600 bg-yellow-50';
    return 'text-green-600 bg-green-50';
  };

  const getUtilizationLabel = (rate: number) => {
    if (rate >= 80) return '混雑';
    if (rate >= 60) return 'やや混雑';
    if (rate >= 40) return '普通';
    return '空いている';
  };

  return (
    <Card className="mt-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>店舗比較 ({establishments.length}件)</CardTitle>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={onClear}>
              すべてクリア
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <tbody>
              <tr className="border-b">
                <td className="py-3 px-2 w-24">店舗画像</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2 min-w-48">
                    <div className="relative">
                      <img
                        src={establishment.image}
                        alt={establishment.name}
                        className="w-full h-32 object-cover rounded-lg"
                      />
                      <Button
                        variant="destructive"
                        size="sm"
                        className="absolute top-2 right-2 w-6 h-6 p-0"
                        onClick={() => onRemove(establishment.id)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">店舗名</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    <div className="">
                      {establishment.name}
                    </div>
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">エリア</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    {establishment.area}
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">稼働率</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    <Badge className={`${getUtilizationColor(establishment.utilizationRate)}`}>
                      {getUtilizationLabel(establishment.utilizationRate)} {establishment.utilizationRate}%
                    </Badge>
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">時給</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    {establishment.priceRange}
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">評価</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    <div className="flex items-center gap-2">
                      <div className="flex">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`w-4 h-4 ${
                              i < establishment.rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm text-muted-foreground">
                        ({establishment.reviews})
                      </span>
                    </div>
                  </td>
                ))}
              </tr>

              <tr className="border-b">
                <td className="py-3 px-2">営業時間</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    {establishment.openHours}
                  </td>
                ))}
              </tr>

              <tr>
                <td className="py-3 px-2">特徴</td>
                {establishments.map((establishment) => (
                  <td key={establishment.id} className="py-3 px-2">
                    <div className="flex flex-wrap gap-1">
                      {establishment.features.map((feature, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}