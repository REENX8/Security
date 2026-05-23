// TanStack Query hooks.

import { useQuery, useMutation } from "@tanstack/react-query";
import { getStats, getHistory, checkUrl, checkBatch, getHealth } from "./client.js";

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
    refetchInterval: 30_000,
  });
}

export function useHistory(params) {
  return useQuery({
    queryKey: ["history", params],
    queryFn: () => getHistory(params),
    keepPreviousData: true,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 60_000,
  });
}

export function useCheckUrl() {
  return useMutation({
    mutationFn: (url) => checkUrl(url),
  });
}

export function useCheckBatch() {
  return useMutation({
    mutationFn: (urls) => checkBatch(urls),
  });
}
