import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useStores, SortBy } from '../hooks/useStores';
import StoreCard from '../components/StoreCard';
import LoadingSpinner from '../components/LoadingSpinner';

const Ranking: React.FC = () => {
  const [sortBy, setSortBy] = useState<SortBy>('current');
  const navigate = useNavigate();
  
  const { data: stores, isLoading, error, refetch } = useStores(sortBy);

  const handleStoreClick = (storeId: string) => {
    navigate(`/stores/${storeId}`);
  };

  const getSortLabel = (sort: SortBy) => {
    switch (sort) {
      case 'current': return '現在の稼働率';
      case 'previous': return '前日の稼働率';
      case 'weekly': return '週平均稼働率';
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <div className="text-red-500 text-6xl mb-4">⚠️</div>
        <h2 className="text-xl font-semibold text-gray-800 mb-2">
          エラーが発生しました
        </h2>
        <p className="text-gray-600 mb-4 max-w-md">
          データの取得に失敗しました。しばらく時間をおいて再度お試しください。
        </p>
        <button
          onClick={() => refetch()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          再試行
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-4">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          店舗ランキング
        </h1>
        
        <div className="flex space-x-2 mb-4">
          {(['current', 'previous', 'weekly'] as SortBy[]).map((sort) => (
            <button
              key={sort}
              onClick={() => setSortBy(sort)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                sortBy === sort
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {getSortLabel(sort)}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <LoadingSpinner />
        ) : stores && stores.length > 0 ? (
          stores.map((store, index) => (
            <StoreCard
              key={store.id}
              store={store}
              rank={index + 1}
              onClick={() => handleStoreClick(store.id)}
            />
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            データがありません
          </div>
        )}
      </div>
    </div>
  );
};

export default Ranking;