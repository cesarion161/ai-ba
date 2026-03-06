"use client";

import { cn } from "@/lib/utils";
import type { Project } from "@/lib/api/projects";

interface ProjectListItemProps {
  project: Project;
  isSelected: boolean;
  onSelect: () => void;
}

const PHASE_LABELS: Record<string, string> = {
  gathering_requirements: "Gathering...",
  selecting_documents: "Selecting docs",
  generating_graph: "Generating...",
  graph_ready: "Ready",
  executing: "Running",
  completed: "Done",
};

export function ProjectListItem({
  project,
  isSelected,
  onSelect,
}: ProjectListItemProps) {
  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full rounded-md px-3 py-2 text-left transition-colors hover:bg-accent",
        isSelected && "bg-accent",
      )}
    >
      <div className="truncate text-sm font-medium">{project.name}</div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>{project.chat_phase ? PHASE_LABELS[project.chat_phase] || project.chat_phase : project.template_key}</span>
        <span>&middot;</span>
        <span>{new Date(project.created_at).toLocaleDateString()}</span>
      </div>
    </button>
  );
}
