"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  useApproveNode,
  useRejectNode,
  useRetryNode,
  useSkipNode,
} from "@/hooks/use-nodes";
import type { Node } from "@/lib/api/nodes";

interface NodeActionsProps {
  projectId: string;
  node: Node;
}

export function NodeActions({ projectId, node }: NodeActionsProps) {
  const [feedback, setFeedback] = useState("");
  const [showReject, setShowReject] = useState(false);

  const approveMutation = useApproveNode(projectId);
  const rejectMutation = useRejectNode(projectId);
  const retryMutation = useRetryNode(projectId);
  const skipMutation = useSkipNode(projectId);

  const anyPending =
    approveMutation.isPending ||
    rejectMutation.isPending ||
    retryMutation.isPending ||
    skipMutation.isPending;

  if (node.status === "awaiting_review") {
    return (
      <div className="space-y-2">
        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={() => approveMutation.mutate(node.slug)}
            disabled={anyPending}
          >
            {approveMutation.isPending ? (
              <>
                <span className="mr-1.5 inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Approving...
              </>
            ) : (
              "Approve"
            )}
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={() => setShowReject(!showReject)}
            disabled={anyPending}
          >
            Reject
          </Button>
        </div>
        {showReject && (
          <div className="space-y-2">
            <Textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Reason for rejection..."
              rows={2}
            />
            <Button
              size="sm"
              variant="destructive"
              onClick={() =>
                rejectMutation.mutate({ slug: node.slug, feedback })
              }
              disabled={!feedback.trim() || anyPending}
            >
              {rejectMutation.isPending ? "Submitting..." : "Submit Rejection"}
            </Button>
          </div>
        )}
      </div>
    );
  }

  if (node.status === "failed") {
    return (
      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={() => retryMutation.mutate(node.slug)}
          disabled={retryMutation.isPending}
        >
          Retry
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => skipMutation.mutate(node.slug)}
          disabled={skipMutation.isPending}
        >
          Skip
        </Button>
      </div>
    );
  }

  if (node.status === "pending" || node.status === "ready") {
    return (
      <Button
        size="sm"
        variant="outline"
        onClick={() => skipMutation.mutate(node.slug)}
        disabled={skipMutation.isPending}
      >
        Skip
      </Button>
    );
  }

  return null;
}
