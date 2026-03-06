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

export interface SSEEvent {
  event: string;
  data: unknown;
}

export function fetchChatHistory(
  projectId: string,
  limit = 200,
  offset = 0,
): Promise<ChatHistoryResponse> {
  return apiFetch(
    `/api/projects/${projectId}/chat?limit=${limit}&offset=${offset}`,
  );
}

// Backend URL for direct streaming requests (bypasses Next.js buffering)
const STREAM_BACKEND =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

/**
 * POST a chat message and read the SSE response stream.
 * Yields parsed SSE events: user_message, assistant_token, assistant_done.
 *
 * Posts directly to the backend to avoid Next.js dev server buffering SSE.
 */
export async function* streamChatMessage(
  projectId: string,
  content: string,
): AsyncGenerator<SSEEvent> {
  const res = await fetch(
    `${STREAM_BACKEND}/api/projects/${projectId}/chat`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    },
  );

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("event: ")) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield { event: currentEvent || "message", data };
          // Break microtask so React can render between tokens
          await Promise.resolve();
        } catch {
          // skip unparseable
        }
        currentEvent = "";
      }
      // blank lines and comments (":") are ignored
    }
  }
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
