"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useProjectSSE(projectId: string | null) {
  const qc = useQueryClient();
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!projectId) return;

    const url = `/api/projects/${projectId}/stream`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const eventType = parsed.event || "message";

        if (
          eventType.startsWith("node.") ||
          eventType === "workflow.completed"
        ) {
          qc.invalidateQueries({ queryKey: ["graph", projectId] });
          qc.invalidateQueries({ queryKey: ["graph-status", projectId] });
          qc.invalidateQueries({ queryKey: ["nodes", projectId] });
        }

        if (eventType === "graph.generated") {
          qc.invalidateQueries({ queryKey: ["graph", projectId] });
          qc.invalidateQueries({ queryKey: ["project", projectId] });
        }

        if (eventType.startsWith("chat.")) {
          qc.invalidateQueries({ queryKey: ["chat", projectId] });
        }
      } catch {
        // ignore parse errors
      }
    };

    source.onerror = () => {
      // Auto-reconnect is built into EventSource
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [projectId, qc]);
}
