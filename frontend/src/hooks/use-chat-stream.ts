"use client";

import { useEffect, useRef, useState } from "react";

export function useChatStream(projectId: string | null) {
  const [streamingContent, setStreamingContent] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const url = `/api/projects/${projectId}/chat/stream`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const eventType = parsed.event || "message";

        if (eventType === "chat.token") {
          setIsStreaming(true);
          setStreamingContent((prev) => prev + (parsed.data?.token || ""));
          if (parsed.data?.done) {
            setIsStreaming(false);
            setStreamingContent("");
          }
        }
      } catch {
        // ignore
      }
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [projectId]);

  return { streamingContent, isStreaming };
}
