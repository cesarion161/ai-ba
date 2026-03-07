"use client";

import { useProject } from "@/hooks/use-projects";
import { useUIStore } from "@/stores/ui-store";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { GraphSkeleton } from "@/components/ui/loading-skeleton";
import { WelcomeScreen } from "@/components/welcome/welcome-screen";
import { ChatPanel } from "@/components/chat/chat-panel";
import { FilesPanel } from "@/components/files/files-panel";
import { cn } from "@/lib/utils";

export function CenterPane() {
  const projectId = useUIStore((s) => s.selectedProjectId);
  const centerTab = useUIStore((s) => s.centerTab);
  const setCenterTab = useUIStore((s) => s.setCenterTab);
  const { data: project, isLoading } = useProject(projectId);

  if (!projectId) {
    return <WelcomeScreen />;
  }

  if (isLoading) {
    return <GraphSkeleton />;
  }

  const phase = project?.chat_phase;

  // During early phases, show chat in center (full-width)
  if (
    phase === "gathering_requirements" ||
    phase === "selecting_documents" ||
    phase === "generating_graph"
  ) {
    return (
      <div className="flex h-full flex-col">
        <ChatPanel projectId={projectId} mode="center" />
      </div>
    );
  }

  // Once graph is ready, show graph/files with tab switcher
  if (phase === "graph_ready" || phase === "executing" || phase === "completed") {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-1 border-b bg-background px-4">
          <button
            onClick={() => setCenterTab("graph")}
            className={cn(
              "px-3 py-2 text-sm font-medium border-b-2 transition-colors",
              centerTab === "graph"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            Graph
          </button>
          <button
            onClick={() => setCenterTab("files")}
            className={cn(
              "px-3 py-2 text-sm font-medium border-b-2 transition-colors",
              centerTab === "files"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground",
            )}
          >
            Files
          </button>
        </div>
        <div className="flex-1 min-h-0">
          {centerTab === "graph" ? (
            <GraphCanvas projectId={projectId} />
          ) : (
            <FilesPanel projectId={projectId} />
          )}
        </div>
      </div>
    );
  }

  // Template-based projects (no chat phase) - show graph directly
  if (!phase) {
    return <GraphCanvas projectId={projectId} />;
  }

  return <WelcomeScreen />;
}
