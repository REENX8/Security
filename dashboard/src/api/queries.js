// TanStack Query hooks.

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getStats, getHistory, checkUrl, checkBatch, getHealth,
  getWhitelist, addWhitelistEntry, deleteWhitelistEntry,
  getFeedback, submitFeedback,
} from "./client.js";

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

// --- Whitelist ---

export function useWhitelist(params) {
  return useQuery({
    queryKey: ["whitelist", params],
    queryFn: () => getWhitelist(params),
    keepPreviousData: true,
  });
}

export function useAddWhitelistEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data) => addWhitelistEntry(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["whitelist"] }),
  });
}

export function useDeleteWhitelistEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (domain) => deleteWhitelistEntry(domain),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["whitelist"] }),
  });
}

// --- Feedback ---

export function useFeedback(params) {
  return useQuery({
    queryKey: ["feedback", params],
    queryFn: () => getFeedback(params),
    keepPreviousData: true,
  });
}

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: (data) => submitFeedback(data),
  });
}
