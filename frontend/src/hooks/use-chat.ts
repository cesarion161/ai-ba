"use client";

import { useCallback, useRef, useState } from "react";
import { flushSync } from "react-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChatHistoryResponse,
  ChatMessage,
  fetchChatHistory,
  selectDocuments,
  streamChatMessage,
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
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [isPending, setIsPending] = useState(false);
  const accumulatedRef = useRef("");
  const rafRef = useRef<number>(0);

  const send = useCallback(
    async (content: string) => {
      if (isPending || isStreaming) return;
      setIsPending(true);
      accumulatedRef.current = "";

      // Optimistic: show user message immediately
      await qc.cancelQueries({ queryKey: ["chat", projectId] });
      qc.setQueryData<ChatHistoryResponse>(["chat", projectId], (old) => {
        if (!old) return old;
        return {
          ...old,
          total: old.total + 1,
          messages: [
            ...old.messages,
            {
              id: `optimistic-${Date.now()}`,
              project_id: projectId,
              role: "user",
              content,
              metadata_: null,
              created_at: new Date().toISOString(),
            },
          ],
        };
      });

      try {
        for await (const event of streamChatMessage(projectId, content)) {
          switch (event.event) {
            case "user_message": {
              // Replace optimistic message with the real saved one
              const msg = event.data as ChatMessage;
              qc.setQueryData<ChatHistoryResponse>(
                ["chat", projectId],
                (old) => {
                  if (!old) return old;
                  return {
                    ...old,
                    messages: old.messages.map((m) =>
                      m.id.startsWith("optimistic-") && m.role === "user"
                        ? msg
                        : m,
                    ),
                  };
                },
              );
              flushSync(() => {
                setIsPending(false);
                setIsStreaming(true);
              });
              break;
            }
            case "assistant_token": {
              const { token } = event.data as { token: string };
              accumulatedRef.current += token;
              // Flush each token synchronously so React renders immediately
              const snapshot = accumulatedRef.current;
              flushSync(() => {
                setStreamingContent(snapshot);
              });
              break;
            }
            case "assistant_done": {
              cancelAnimationFrame(rafRef.current);
              // Done — clear streaming, refetch history for the saved message
              flushSync(() => {
                setStreamingContent("");
                setIsStreaming(false);
              });
              qc.invalidateQueries({ queryKey: ["chat", projectId] });
              qc.invalidateQueries({ queryKey: ["project", projectId] });
              break;
            }
          }
        }
      } catch (err) {
        // On error, refetch to get whatever was saved
        qc.invalidateQueries({ queryKey: ["chat", projectId] });
      } finally {
        cancelAnimationFrame(rafRef.current);
        setIsPending(false);
        setIsStreaming(false);
        setStreamingContent("");
        accumulatedRef.current = "";
      }
    },
    [projectId, qc, isPending, isStreaming],
  );

  return { send, streamingContent, isStreaming, isPending };
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
