export const NODE_STATUS_COLORS: Record<string, string> = {
  pending: "#6B7280",
  ready: "#6B7280",
  running: "#3B82F6",
  awaiting_review: "#F59E0B",
  approved: "#22C55E",
  rejected: "#F97316",
  failed: "#EF4444",
  skipped: "#6B7280",
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
  return NODE_STATUS_COLORS[status] || "#6B7280";
}
