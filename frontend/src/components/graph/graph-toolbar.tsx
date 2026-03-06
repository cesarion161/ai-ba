"use client";

import { Button } from "@/components/ui/button";
import { useRunGraph, useGraphStatus } from "@/hooks/use-graph";
import { useProject } from "@/hooks/use-projects";

interface GraphToolbarProps {
  projectId: string;
}

export function GraphToolbar({ projectId }: GraphToolbarProps) {
  const { data: project } = useProject(projectId);
  const { data: status } = useGraphStatus(projectId);
  const runMutation = useRunGraph(projectId);

  const phase = project?.chat_phase;
  const canRun = phase === "graph_ready" || !phase;
  const progress = status?.progress_pct || 0;
  const isExecuting = phase === "executing";

  return (
    <div className="flex items-center gap-3 border-b bg-background px-4 py-2">
      <Button
        size="sm"
        onClick={() => runMutation.mutate()}
        disabled={!canRun || runMutation.isPending}
      >
        {runMutation.isPending ? "Starting..." : "Run Graph"}
      </Button>
      {(isExecuting || progress > 0) && (
        <div className="flex items-center gap-2">
          <div className="h-2 w-32 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="text-xs text-muted-foreground">
            {progress.toFixed(0)}%
          </span>
        </div>
      )}
      {status && (
        <span className="text-xs text-muted-foreground">
          {status.total_nodes} nodes
        </span>
      )}
    </div>
  );
}
