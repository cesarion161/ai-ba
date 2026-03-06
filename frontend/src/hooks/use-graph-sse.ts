"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

export function useGraphSSE(projectId: string | null) {
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

        if (eventType.startsWith("node.")) {
          // Invalidate graph data on any node event
          qc.invalidateQueries({ queryKey: ["graph", projectId] });
          qc.invalidateQueries({ queryKey: ["graph-status", projectId] });
        }
      } catch {
        // ignore
      }
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, [projectId, qc]);
}
