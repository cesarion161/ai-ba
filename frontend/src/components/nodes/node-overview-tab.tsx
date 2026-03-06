"use client";

import { StatusBadge } from "@/components/ui/status-badge";
import type { Node } from "@/lib/api/nodes";

export function NodeOverviewTab({ node }: { node: Node }) {
  return (
    <div className="space-y-3 text-sm">
      <div className="flex justify-between">
        <span className="text-muted-foreground">Slug</span>
        <code className="text-xs">{node.slug}</code>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Label</span>
        <span>{node.label}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Branch</span>
        <span>{node.branch}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Type</span>
        <span>{node.node_type}</span>
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Status</span>
        <StatusBadge status={node.status} />
      </div>
      <div className="flex justify-between">
        <span className="text-muted-foreground">Retries</span>
        <span>{node.retry_count}</span>
      </div>
      {node.started_at && (
        <div className="flex justify-between">
          <span className="text-muted-foreground">Started</span>
          <span>{new Date(node.started_at).toLocaleString()}</span>
        </div>
      )}
      {node.completed_at && (
        <div className="flex justify-between">
          <span className="text-muted-foreground">Completed</span>
          <span>{new Date(node.completed_at).toLocaleString()}</span>
        </div>
      )}
      {node.user_feedback && (
        <div>
          <span className="text-muted-foreground">Feedback</span>
          <p className="mt-1 rounded bg-muted p-2 text-xs">{node.user_feedback}</p>
        </div>
      )}
    </div>
  );
}
