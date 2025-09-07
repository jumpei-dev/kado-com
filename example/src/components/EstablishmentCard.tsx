import { Star, MapPin, Clock, Users } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';

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

interface EstablishmentCardProps {
  establishment: EstablishmentData;
  onCompare: (establishment: EstablishmentData) => void;
  isComparing: boolean;
}

export function EstablishmentCard({ establishment, onCompare, isComparing }: EstablishmentCardProps) {
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
    <Card className="overflow-hidden hover:shadow-lg transition-shadow duration-200">
      <div className="aspect-video relative overflow-hidden">
        <img 
          src={establishment.image} 
          alt={establishment.name}
          className="w-full h-full object-cover"
        />
        <div className="absolute top-3 right-3">
          <Badge className={`${getUtilizationColor(establishment.utilizationRate)} px-2 py-1`}>
            {getUtilizationLabel(establishment.utilizationRate)} {establishment.utilizationRate}%
          </Badge>
        </div>
      </div>
      
      <CardContent className="p-4">
        <div className="space-y-3">
          <div>
            <h3 className="truncate">{establishment.name}</h3>
            <div className="flex items-center gap-1 text-muted-foreground">
              <MapPin className="w-4 h-4" />
              <span>{establishment.area}</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1">
              <div className="flex items-center">
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
            <div className="">
              {establishment.priceRange}
            </div>
          </div>

          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Clock className="w-4 h-4" />
            <span>{establishment.openHours}</span>
          </div>

          <div className="flex flex-wrap gap-1">
            {establishment.features.slice(0, 2).map((feature, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {feature}
              </Badge>
            ))}
            {establishment.features.length > 2 && (
              <Badge variant="secondary" className="text-xs">
                +{establishment.features.length - 2}
              </Badge>
            )}
          </div>

          <div className="flex gap-2 pt-2">
            <Button variant="outline" size="sm" className="flex-1">
              詳細を見る
            </Button>
            <Button 
              variant={isComparing ? "default" : "outline"} 
              size="sm" 
              onClick={() => onCompare(establishment)}
            >
              {isComparing ? '比較中' : '比較'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}