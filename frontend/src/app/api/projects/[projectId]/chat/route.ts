import { NextRequest } from "next/server";

export const runtime = "edge";
export const dynamic = "force-dynamic";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * GET /api/projects/:projectId/chat
 * Proxies chat history request to backend.
 */
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await params;
  const search = req.nextUrl.searchParams.toString();
  const qs = search ? `?${search}` : "";

  const upstream = await fetch(
    `${BACKEND}/api/projects/${projectId}/chat${qs}`,
  );
  const data = await upstream.text();
  return new Response(data, {
    status: upstream.status,
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * POST /api/projects/:projectId/chat
 * Proxies the request to the backend and streams the SSE response through.
 * Uses edge runtime for native streaming without buffering.
 */
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ projectId: string }> },
) {
  const { projectId } = await params;
  const body = await req.text();

  const upstream = await fetch(`${BACKEND}/api/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  if (!upstream.ok || !upstream.body) {
    const text = await upstream.text().catch(() => "Backend error");
    return new Response(text, { status: upstream.status });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
