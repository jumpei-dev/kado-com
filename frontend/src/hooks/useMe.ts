import { useQuery } from '@tanstack/react-query';
import { api, User } from '../lib/api';

export const useMe = () => {
  return useQuery({
    queryKey: ['me'],
    queryFn: () => api.getMe(),
    staleTime: 5 * 60 * 1000, // 5分
    retry: 2,
  });
};