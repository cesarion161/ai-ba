"use client";

import { useProject } from "@/hooks/use-projects";
import { useUIStore } from "@/stores/ui-store";
import { ChatPanel } from "@/components/chat/chat-panel";

export function RightSidebar() {
  const projectId = useUIStore((s) => s.selectedProjectId);
  const { data: project } = useProject(projectId);

  if (!projectId) return null;

  const phase = project?.chat_phase;

  // Only show right sidebar chat when graph is visible in center
  if (
    phase === "graph_ready" ||
    phase === "executing" ||
    phase === "completed" ||
    !phase
  ) {
    return (
      <aside className="flex h-full flex-col border-l bg-muted/30">
        <div className="border-b px-3 py-2">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Chat
          </h2>
        </div>
        <div className="flex-1 overflow-hidden">
          <ChatPanel projectId={projectId} mode="sidebar" />
        </div>
      </aside>
    );
  }

  return null;
}
