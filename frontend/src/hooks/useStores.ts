import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export type SortBy = 'current' | 'previous' | 'weekly';

export const useStores = (sortBy: SortBy = 'current') => {
  return useQuery({
    queryKey: ['stores', sortBy],
    queryFn: () => api.getStores(sortBy),
    staleTime: 5 * 60 * 1000, // 5分
    refetchInterval: 5 * 60 * 1000, // 5分ごとに自動更新
  });
};