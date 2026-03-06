import { apiFetch } from "../api-client";

export interface ChatMessage {
  id: string;
  project_id: string;
  role: string;
  content: string;
  metadata_: Record<string, unknown> | null;
  created_at: string;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  total: number;
  has_more: boolean;
}

export function fetchChatHistory(
  projectId: string,
  limit = 50,
  offset = 0,
): Promise<ChatHistoryResponse> {
  return apiFetch(
    `/api/projects/${projectId}/chat?limit=${limit}&offset=${offset}`,
  );
}

export function sendChatMessage(
  projectId: string,
  content: string,
): Promise<ChatMessage> {
  return apiFetch(`/api/projects/${projectId}/chat`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function selectDocuments(
  projectId: string,
  docTypeKeys: string[],
): Promise<ChatMessage> {
  return apiFetch(`/api/projects/${projectId}/chat/select-documents`, {
    method: "POST",
    body: JSON.stringify({ doc_type_keys: docTypeKeys }),
  });
}
