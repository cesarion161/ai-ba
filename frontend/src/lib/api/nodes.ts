import { apiFetch } from "../api-client";

export interface Node {
  id: string;
  slug: string;
  label: string;
  branch: string;
  node_type: string;
  status: string;
  requires_approval: boolean;
  config: Record<string, unknown> | null;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  user_feedback: string | null;
  retry_count: number;
  started_at: string | null;
  completed_at: string | null;
}

export interface NodeListResponse {
  nodes: Node[];
}

export function fetchNodes(projectId: string): Promise<NodeListResponse> {
  return apiFetch(`/api/projects/${projectId}/nodes`);
}

export function fetchNode(projectId: string, slug: string): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}`);
}

export function approveNode(projectId: string, slug: string): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/approve`, {
    method: "POST",
  });
}

export function rejectNode(
  projectId: string,
  slug: string,
  feedback: string,
): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/reject`, {
    method: "POST",
    body: JSON.stringify({ feedback }),
  });
}

export function retryNode(projectId: string, slug: string): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/retry`, {
    method: "POST",
  });
}

export function skipNode(projectId: string, slug: string): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/skip`, {
    method: "POST",
  });
}

export function answerNode(
  projectId: string,
  slug: string,
  answers: Record<string, unknown>,
): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/answer`, {
    method: "POST",
    body: JSON.stringify({ answers }),
  });
}

export function editNodeOutput(
  projectId: string,
  slug: string,
  outputData: Record<string, unknown>,
): Promise<Node> {
  return apiFetch(`/api/projects/${projectId}/nodes/${slug}/output`, {
    method: "PUT",
    body: JSON.stringify({ output_data: outputData }),
  });
}
