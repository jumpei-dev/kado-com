import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Slider } from './ui/slider';
import { Checkbox } from './ui/checkbox';
import { Button } from './ui/button';
import { X } from 'lucide-react';

interface FilterState {
  area: string;
  priceRange: number[];
  utilizationRate: number[];
  rating: number;
  features: string[];
}

interface FilterSidebarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  isOpen: boolean;
  onClose: () => void;
}

const areas = [
  '全エリア',
  '新宿・歌舞伎町',
  '渋谷',
  '池袋',
  '上野',
  '錦糸町',
  '吉原',
  '大阪・飛田',
  '名古屋・中村区',
  '福岡・中洲'
];

const features = [
  '即スタート可能',
  '研修制度あり',
  '高時給保証',
  '個室完備',
  '送迎あり',
  '24時間営業',
  'ノルマなし',
  '未経験歓迎'
];

export function FilterSidebar({ filters, onFiltersChange, isOpen, onClose }: FilterSidebarProps) {
  const handleAreaChange = (area: string) => {
    onFiltersChange({ ...filters, area });
  };

  const handlePriceRangeChange = (value: number[]) => {
    onFiltersChange({ ...filters, priceRange: value });
  };

  const handleUtilizationRateChange = (value: number[]) => {
    onFiltersChange({ ...filters, utilizationRate: value });
  };

  const handleRatingChange = (rating: number) => {
    onFiltersChange({ ...filters, rating });
  };

  const handleFeatureToggle = (feature: string) => {
    const newFeatures = filters.features.includes(feature)
      ? filters.features.filter(f => f !== feature)
      : [...filters.features, feature];
    onFiltersChange({ ...filters, features: newFeatures });
  };

  const clearAllFilters = () => {
    onFiltersChange({
      area: '全エリア',
      priceRange: [0, 100000],
      utilizationRate: [0, 100],
      rating: 0,
      features: []
    });
  };

  return (
    <div className={`fixed inset-y-0 left-0 z-50 w-80 bg-background border-r transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${
      isOpen ? 'translate-x-0' : '-translate-x-full'
    }`}>
      <div className="flex items-center justify-between p-4 border-b lg:hidden">
        <h2>フィルター</h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="w-4 h-4" />
        </Button>
      </div>
      
      <div className="p-4 space-y-6 overflow-y-auto h-full">
        <div className="flex items-center justify-between">
          <h2 className="hidden lg:block">フィルター</h2>
          <Button variant="ghost" size="sm" onClick={clearAllFilters}>
            クリア
          </Button>
        </div>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">エリア</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Select value={filters.area} onValueChange={handleAreaChange}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {areas.map((area) => (
                  <SelectItem key={area} value={area}>
                    {area}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              時給範囲: ¥{filters.priceRange[0].toLocaleString()} - ¥{filters.priceRange[1].toLocaleString()}
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Slider
              value={filters.priceRange}
              onValueChange={handlePriceRangeChange}
              max={100000}
              min={0}
              step={5000}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>¥0</span>
              <span>¥100,000</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">
              稼働率: {filters.utilizationRate[0]}% - {filters.utilizationRate[1]}%
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Slider
              value={filters.utilizationRate}
              onValueChange={handleUtilizationRateChange}
              max={100}
              min={0}
              step={5}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-2">
              <span>0%</span>
              <span>100%</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">最低評価</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <Select value={filters.rating.toString()} onValueChange={(value) => handleRatingChange(parseInt(value))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">指定なし</SelectItem>
                <SelectItem value="1">★1以上</SelectItem>
                <SelectItem value="2">★2以上</SelectItem>
                <SelectItem value="3">★3以上</SelectItem>
                <SelectItem value="4">★4以上</SelectItem>
                <SelectItem value="5">★5のみ</SelectItem>
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">特徴</CardTitle>
          </CardHeader>
          <CardContent className="pt-0 space-y-3">
            {features.map((feature) => (
              <div key={feature} className="flex items-center space-x-2">
                <Checkbox
                  id={feature}
                  checked={filters.features.includes(feature)}
                  onCheckedChange={() => handleFeatureToggle(feature)}
                />
                <label htmlFor={feature} className="text-sm">
                  {feature}
                </label>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}