"use client";

import { Button } from "@/components/ui/button";
import { useRunGraph, useGraphStatus, usePreflight } from "@/hooks/use-graph";
import { useProject } from "@/hooks/use-projects";

interface GraphToolbarProps {
  projectId: string;
}

export function GraphToolbar({ projectId }: GraphToolbarProps) {
  const { data: project } = useProject(projectId);
  const { data: status } = useGraphStatus(projectId);
  const { data: preflight } = usePreflight(projectId);
  const runMutation = useRunGraph(projectId);

  const phase = project?.chat_phase;
  const isExecuting = phase === "executing";
  const isCompleted = phase === "completed";
  const hasIssues = preflight && !preflight.can_run;
  const canRun =
    (phase === "graph_ready" || !phase) &&
    !runMutation.isPending &&
    !hasIssues;
  const progress = status?.progress_pct || 0;

  const runningCount = status?.by_status?.running || 0;
  const awaitingCount = status?.by_status?.awaiting_review || 0;

  const buttonLabel = runMutation.isPending
    ? "Starting..."
    : isExecuting
      ? "Running..."
      : isCompleted
        ? "Completed"
        : hasIssues
          ? "Cannot Run"
          : "Run Graph";

  return (
    <div className="flex flex-col border-b bg-background">
      <div className="flex items-center gap-3 px-4 py-2">
        <Button
          size="sm"
          onClick={() => runMutation.mutate()}
          disabled={!canRun || isExecuting || isCompleted}
          variant={isExecuting ? "secondary" : hasIssues ? "destructive" : "default"}
          title={hasIssues ? preflight.issues.join("\n") : undefined}
        >
          {isExecuting && (
            <span className="mr-1.5 inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
          )}
          {buttonLabel}
        </Button>
        {(isExecuting || progress > 0) && (
          <div className="flex items-center gap-2">
            <div className="h-2 w-32 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground">
              {progress.toFixed(0)}%
            </span>
          </div>
        )}
        {isExecuting && runningCount > 0 && (
          <span className="text-xs text-blue-500">
            {runningCount} processing
          </span>
        )}
        {awaitingCount > 0 && (
          <span className="text-xs text-amber-500">
            {awaitingCount} awaiting review
          </span>
        )}
        {status && (
          <span className="text-xs text-muted-foreground">
            {status.total_nodes} nodes
          </span>
        )}
      </div>
      {hasIssues && (
        <div className="border-t border-destructive/20 bg-destructive/5 px-4 py-2">
          {preflight.issues.map((issue, i) => (
            <p key={i} className="text-xs text-destructive">
              ⚠ {issue}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}
