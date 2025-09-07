import { Badge } from './ui/badge';
import { Card, CardContent } from './ui/card';
import { Star, TrendingUp, MapPin, Users } from 'lucide-react';

interface BusinessData {
  id: string;
  name: string;
  blurredName: string;
  prefecture: string;
  area: string;
  businessType: 'デリヘル' | '箱ヘル' | 'NSソープ' | 'S着ソープ' | 'DC';
  spec: '低スペ' | 'スタンダード' | 'ハイスペ';
  utilizationRate: number;
}

interface RankingCardProps {
  business: BusinessData;
  rank: number;
  isLoggedIn: boolean;
  onClick: (id: string) => void;
}

export function RankingCard({ business, rank, isLoggedIn, onClick }: RankingCardProps) {
  const getRankStyle = (rank: number) => {
    if (rank === 1) {
      return {
        cardClass: 'bg-gradient-to-br from-amber-50 to-yellow-50 border-2 border-amber-300 shadow-lg',
        textSize: 'text-xl',
        rankSize: 'text-5xl',
        padding: 'py-8 px-5',
        textColor: 'text-amber-800',
        rankColor: 'text-amber-600'
      };
    } else if (rank <= 3) {
      return {
        cardClass: 'bg-gradient-to-br from-slate-50 to-gray-50 border-2 border-slate-300 shadow-md',
        textSize: 'text-lg',
        rankSize: 'text-4xl',
        padding: 'py-6 px-5',
        textColor: 'text-slate-700',
        rankColor: 'text-slate-600'
      };
    } else {
      return {
        cardClass: 'bg-white border border-blue-100 hover:shadow-md hover:border-blue-200 transition-all duration-200',
        textSize: 'text-base',
        rankSize: 'text-2xl',
        padding: 'py-4 px-4',
        textColor: 'text-gray-700',
        rankColor: 'text-blue-600'
      };
    }
  };

  const getUtilizationColor = (rate: number) => {
    if (rate >= 90) return 'bg-gradient-to-r from-red-100 to-pink-100 text-red-800 border border-red-200';
    if (rate >= 80) return 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-800 border border-orange-200';
    if (rate >= 70) return 'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-800 border border-yellow-200';
    return 'bg-gradient-to-r from-emerald-100 to-green-100 text-emerald-800 border border-emerald-200';
  };

  const getTrendIcon = (rate: number) => {
    if (rate >= 85) return <TrendingUp className="w-3 h-3 text-green-600" />;
    return null;
  };

  const style = getRankStyle(rank);
  const displayName = isLoggedIn ? business.name : business.blurredName;

  return (
    <Card 
      className={`${style.cardClass} cursor-pointer transition-all duration-200`}
      onClick={() => onClick(business.id)}
    >
      <CardContent className={style.padding}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`${style.rankSize} ${style.rankColor}`}>
              #{rank}
            </div>
            {rank <= 3 && <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />}
          </div>
          <div className="text-right">
            <Badge className={`${getUtilizationColor(business.utilizationRate)} text-lg px-3 py-1.5 font-medium`}>
              {business.utilizationRate}%
            </Badge>
            <div className="flex items-center justify-end mt-1">
              {getTrendIcon(business.utilizationRate)}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <h3 className={`${style.textSize} ${style.textColor} line-clamp-1 leading-tight`}>
            {displayName}
          </h3>
          
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-blue-500" />
            <span className={`text-sm ${style.textColor ? style.textColor.replace('-800', '-600') : 'text-gray-600'}`}>
              {business.prefecture} • {business.area}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-500" />
              <Badge variant="outline" className="text-xs border-blue-200 text-blue-700">
                {business.businessType}
              </Badge>
            </div>
            <Badge variant="outline" className="text-xs border-blue-200 text-blue-700">
              {business.spec}
            </Badge>
          </div>

          {rank <= 3 && (
            <div className="pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-500 text-center">
                {rank === 1 ? '🏆 最高稼働率店舗' : rank === 2 ? '🥈 第2位' : '🥉 第3位'}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}