"use client";

import { useProject } from "@/hooks/use-projects";
import { useUIStore } from "@/stores/ui-store";
import { GraphCanvas } from "@/components/graph/graph-canvas";
import { GraphSkeleton } from "@/components/ui/loading-skeleton";
import { WelcomeScreen } from "@/components/welcome/welcome-screen";
import { ChatPanel } from "@/components/chat/chat-panel";

export function CenterPane() {
  const projectId = useUIStore((s) => s.selectedProjectId);
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

  // Once graph is ready, show the graph canvas
  if (phase === "graph_ready" || phase === "executing" || phase === "completed") {
    return <GraphCanvas projectId={projectId} />;
  }

  // Template-based projects (no chat phase) - show graph directly
  if (!phase) {
    return <GraphCanvas projectId={projectId} />;
  }

  return <WelcomeScreen />;
}
