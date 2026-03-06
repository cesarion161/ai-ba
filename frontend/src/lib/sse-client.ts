const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export interface SSEOptions {
  onMessage: (event: string, data: unknown) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
}

export function createSSEConnection(
  path: string,
  options: SSEOptions,
): EventSource {
  const url = `${BASE_URL}${path}`;
  const source = new EventSource(url);

  source.onopen = () => options.onOpen?.();
  source.onerror = (e) => options.onError?.(e);

  source.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      options.onMessage("message", data);
    } catch {
      options.onMessage("message", event.data);
    }
  };

  return source;
}

export function subscribeSSE(
  path: string,
  eventTypes: string[],
  onEvent: (type: string, data: unknown) => void,
): EventSource {
  const url = `${BASE_URL}${path}`;
  const source = new EventSource(url);

  for (const type of eventTypes) {
    source.addEventListener(type, (event: MessageEvent) => {
      try {
        onEvent(type, JSON.parse(event.data));
      } catch {
        onEvent(type, event.data);
      }
    });
  }

  // Also listen for generic messages
  source.onmessage = (event) => {
    try {
      const parsed = JSON.parse(event.data);
      onEvent(parsed.event || "message", parsed.data || parsed);
    } catch {
      onEvent("message", event.data);
    }
  };

  return source;
}
