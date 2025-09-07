import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Button } from './ui/button';

interface FilterState {
  area: string;
  businessType: string;
  spec: string;
  period: string;
}

interface FilterBarProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  onApplyFilters: () => void;
}

const areas = ['全国', '東日本', '西日本', '北海道', '東北', '関東', '中部', '関西', '中国', '四国', '九州・沖縄'];
const businessTypes = ['全業種', 'デリヘル', '箱ヘル', 'NSソープ', 'S着ソープ', 'DC'];
const specs = ['すべて', '低スペ', 'スタンダード', 'ハイスペ'];
const periods = ['先週', '過去1ヶ月', '過去3ヶ月', '過去1年'];

export function FilterBar({ filters, onFiltersChange, onApplyFilters }: FilterBarProps) {
  const handleFilterChange = (key: keyof FilterState, value: string) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  return (
    <div className="px-4 py-4 bg-gradient-to-r from-blue-50/60 to-sky-50/60 border-b border-blue-100">
      <div className="space-y-3 max-w-md mx-auto">
        <div className="grid grid-cols-2 gap-2">
          <Select value={filters.area} onValueChange={(value) => handleFilterChange('area', value)}>
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="エリア" />
            </SelectTrigger>
            <SelectContent>
              {areas.map((area) => (
                <SelectItem key={area} value={area} className="text-sm">
                  {area}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filters.businessType} onValueChange={(value) => handleFilterChange('businessType', value)}>
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="業種" />
            </SelectTrigger>
            <SelectContent>
              {businessTypes.map((type) => (
                <SelectItem key={type} value={type} className="text-sm">
                  {type}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <Select value={filters.spec} onValueChange={(value) => handleFilterChange('spec', value)}>
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="スペック" />
            </SelectTrigger>
            <SelectContent>
              {specs.map((spec) => (
                <SelectItem key={spec} value={spec} className="text-sm">
                  {spec}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={filters.period} onValueChange={(value) => handleFilterChange('period', value)}>
            <SelectTrigger className="text-sm">
              <SelectValue placeholder="期間" />
            </SelectTrigger>
            <SelectContent>
              {periods.map((period) => (
                <SelectItem key={period} value={period} className="text-sm">
                  {period}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <Button 
          onClick={onApplyFilters}
          className="w-full bg-gradient-to-r from-blue-200 to-sky-200 hover:from-blue-300 hover:to-sky-300 text-blue-800 border-0 shadow-sm"
        >
          絞り込む
        </Button>
      </div>
    </div>
  );
}