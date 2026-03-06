import { NextRequest } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await params;
  const upstream = `${API_URL}/api/projects/${projectId}/stream`;

  const response = await fetch(upstream, {
    headers: { Accept: "text/event-stream" },
    // @ts-expect-error -- Node fetch supports duplex for streaming
    duplex: "half",
  });

  if (!response.ok || !response.body) {
    return new Response("Upstream SSE connection failed", { status: 502 });
  }

  return new Response(response.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
