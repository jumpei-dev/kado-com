import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export const useStoreDetail = (storeId: string) => {
  return useQuery({
    queryKey: ['store', storeId],
    queryFn: () => api.getStoreDetail(storeId),
    enabled: !!storeId,
    staleTime: 2 * 60 * 1000, // 2分
    refetchInterval: 2 * 60 * 1000, // 2分ごとに自動更新
  });
};