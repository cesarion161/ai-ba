"use client";

import { cn } from "@/lib/utils";

const PHASES = [
  { key: "gathering_requirements", label: "Requirements" },
  { key: "selecting_documents", label: "Documents" },
  { key: "generating_graph", label: "Graph" },
  { key: "graph_ready", label: "Review" },
  { key: "executing", label: "Executing" },
  { key: "completed", label: "Complete" },
];

export function PhaseIndicator({ currentPhase }: { currentPhase: string }) {
  const currentIndex = PHASES.findIndex((p) => p.key === currentPhase);

  return (
    <div className="flex items-center gap-1">
      {PHASES.map((phase, i) => (
        <div key={phase.key} className="flex items-center">
          <div
            className={cn(
              "rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors",
              i < currentIndex && "bg-primary/20 text-primary",
              i === currentIndex && "bg-primary text-primary-foreground",
              i > currentIndex && "bg-muted text-muted-foreground",
            )}
          >
            {phase.label}
          </div>
          {i < PHASES.length - 1 && (
            <div
              className={cn(
                "mx-1 h-px w-4",
                i < currentIndex ? "bg-primary" : "bg-border",
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
