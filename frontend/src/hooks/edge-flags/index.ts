'use client';

import { useQuery } from '@tanstack/react-query';
import { IMaintenanceNotice } from '@/lib/edge-flags';

const maintenanceNoticeKeysBase = ['maintenanceNotice'] as const;

export const maintenanceNoticeKeys = {
  all: maintenanceNoticeKeysBase,
} as const;

export const useMaintenanceNoticeQuery = (options?) => {
  return useQuery<IMaintenanceNotice>({
    queryKey: maintenanceNoticeKeys.all,
    queryFn: async (): Promise<IMaintenanceNotice> => {
      // Используем маршрут Next.js без префикса /api, чтобы не конфликтовать с бекенд-прокси
      const response = await fetch('/edge-flags');
      const data = await response.json();
      return data;
    },
    staleTime: 30 * 1000,
    refetchInterval: 60 * 1000,
    refetchOnWindowFocus: true,
    retry: 3,
    placeholderData: { enabled: false },
    ...options,
  });
};
