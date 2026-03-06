"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchChatHistory,
  selectDocuments,
  sendChatMessage,
} from "@/lib/api/chat";

export function useChatHistory(projectId: string | null) {
  return useQuery({
    queryKey: ["chat", projectId],
    queryFn: () => fetchChatHistory(projectId!),
    enabled: !!projectId,
  });
}

export function useSendMessage(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (content: string) => sendChatMessage(projectId, content),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chat", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useSelectDocuments(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keys: string[]) => selectDocuments(projectId, keys),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["chat", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}
