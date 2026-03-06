import { apiFetch } from "../api-client";

export interface GraphNode {
  slug: string;
  label: string;
  branch: string;
  node_type: string;
  status: string;
  requires_approval: boolean;
}

export interface GraphEdge {
  from_slug: string;
  to_slug: string;
}

export interface GraphResponse {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphStatusResponse {
  project_id: string;
  total_nodes: number;
  by_status: Record<string, number>;
  branches: { branch: string; nodes: GraphNode[] }[];
  progress_pct: number;
}

export function fetchGraph(projectId: string): Promise<GraphResponse> {
  return apiFetch(`/api/projects/${projectId}/graph`);
}

export function runGraph(
  projectId: string,
): Promise<{ task_id: string; status: string }> {
  return apiFetch(`/api/projects/${projectId}/graph/run`, { method: "POST" });
}

export function fetchGraphStatus(
  projectId: string,
): Promise<GraphStatusResponse> {
  return apiFetch(`/api/projects/${projectId}/graph/status`);
}

// Graph editing
export function addGraphNode(
  projectId: string,
  data: {
    slug: string;
    label: string;
    branch?: string;
    node_type: string;
    requires_approval?: boolean;
    config?: Record<string, unknown>;
    depends_on?: string[];
  },
) {
  return apiFetch(`/api/projects/${projectId}/graph/nodes`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateGraphNode(
  projectId: string,
  slug: string,
  data: {
    label?: string;
    config?: Record<string, unknown>;
    requires_approval?: boolean;
  },
) {
  return apiFetch(`/api/projects/${projectId}/graph/nodes/${slug}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteGraphNode(projectId: string, slug: string) {
  return apiFetch(`/api/projects/${projectId}/graph/nodes/${slug}`, {
    method: "DELETE",
  });
}

export function addGraphEdge(
  projectId: string,
  fromSlug: string,
  toSlug: string,
) {
  return apiFetch(`/api/projects/${projectId}/graph/edges`, {
    method: "POST",
    body: JSON.stringify({ from_slug: fromSlug, to_slug: toSlug }),
  });
}

export function deleteGraphEdge(
  projectId: string,
  fromSlug: string,
  toSlug: string,
) {
  return apiFetch(
    `/api/projects/${projectId}/graph/edges?from_slug=${fromSlug}&to_slug=${toSlug}`,
    { method: "DELETE" },
  );
}
