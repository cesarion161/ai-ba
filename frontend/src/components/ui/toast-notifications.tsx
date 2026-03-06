"use client";

import { toast } from "sonner";

export function notifyNodeCompleted(slug: string) {
  toast.success(`Node "${slug}" completed`);
}

export function notifyNodeFailed(slug: string, error?: string) {
  toast.error(`Node "${slug}" failed`, {
    description: error,
  });
}

export function notifyWorkflowCompleted() {
  toast.success("Workflow completed", {
    description: "All nodes have been processed.",
  });
}
