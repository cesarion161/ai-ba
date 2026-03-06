"use client";

import { Badge } from "@/components/ui/badge";
import { getStatusColor } from "@/lib/colors";

const STATUS_LABELS: Record<string, string> = {
  pending: "Pending",
  ready: "Ready",
  running: "Running",
  awaiting_review: "Awaiting Review",
  approved: "Approved",
  rejected: "Rejected",
  failed: "Failed",
  skipped: "Skipped",
};

export function StatusBadge({ status }: { status: string }) {
  const color = getStatusColor(status);
  const label = STATUS_LABELS[status] || status;

  return (
    <Badge
      variant="outline"
      style={{ borderColor: color, color }}
      className="text-xs font-medium"
    >
      {label}
    </Badge>
  );
}
