export const NODE_STATUS_COLORS: Record<string, string> = {
  pending: "#9CA3AF",
  ready: "#2563EB",
  running: "#3B82F6",
  awaiting_review: "#F59E0B",
  approved: "#22C55E",
  rejected: "#F97316",
  failed: "#EF4444",
  skipped: "#9CA3AF",
};

// Subtle background tints for each status (low opacity fills)
export const NODE_STATUS_BG: Record<string, string> = {
  pending: "rgba(156, 163, 175, 0.06)",
  ready: "rgba(37, 99, 235, 0.08)",
  running: "rgba(59, 130, 246, 0.12)",
  awaiting_review: "rgba(245, 158, 11, 0.10)",
  approved: "rgba(34, 197, 94, 0.10)",
  rejected: "rgba(249, 115, 22, 0.10)",
  failed: "rgba(239, 68, 68, 0.10)",
  skipped: "rgba(156, 163, 175, 0.06)",
};

export const CHAT_PHASE_COLORS: Record<string, string> = {
  gathering_requirements: "#3B82F6",
  selecting_documents: "#F59E0B",
  generating_graph: "#8B5CF6",
  graph_ready: "#22C55E",
  executing: "#3B82F6",
  completed: "#22C55E",
};

export function getStatusColor(status: string): string {
  return NODE_STATUS_COLORS[status] || "#9CA3AF";
}

export function getStatusBg(status: string): string {
  return NODE_STATUS_BG[status] || "transparent";
}
