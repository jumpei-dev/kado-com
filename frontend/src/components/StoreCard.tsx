import React from 'react';
import { Store } from '../lib/api';

interface StoreCardProps {
  store: Store;
  rank: number;
  onClick?: () => void;
}

const StoreCard: React.FC<StoreCardProps> = ({ store, rank, onClick }) => {
  const formatRate = (rate?: number) => {
    if (rate === undefined || rate === null) return 'N/A';
    return `${rate.toFixed(1)}%`;
  };

  const getRankColor = (rank: number) => {
    if (rank === 1) return 'text-yellow-600';
    if (rank === 2) return 'text-gray-500';
    if (rank === 3) return 'text-amber-600';
    return 'text-gray-700';
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md p-4 cursor-pointer hover:shadow-lg transition-shadow"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className={`text-2xl font-bold ${getRankColor(rank)}`}>
            #{rank}
          </span>
          <h3 className="text-lg font-semibold text-gray-800 truncate">
            {store.name}
          </h3>
        </div>
        <span className="text-sm text-gray-500 capitalize">
          {store.genre}
        </span>
      </div>
      
      <div className="grid grid-cols-3 gap-2 text-sm">
        <div className="text-center">
          <div className="text-gray-500">現在</div>
          <div className="font-semibold text-blue-600">
            {formatRate(store.workingRate)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-gray-500">前日</div>
          <div className="font-semibold text-gray-700">
            {formatRate(store.previousRate)}
          </div>
        </div>
        <div className="text-center">
          <div className="text-gray-500">週平均</div>
          <div className="font-semibold text-green-600">
            {formatRate(store.weeklyRate)}
          </div>
        </div>
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        {store.area}
      </div>
    </div>
  );
};

export default StoreCard;