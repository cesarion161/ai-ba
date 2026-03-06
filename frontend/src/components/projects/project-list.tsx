"use client";

import { useState } from "react";
import { useProjects } from "@/hooks/use-projects";
import { useUIStore } from "@/stores/ui-store";
import { ProjectListItem } from "./project-list-item";
import { NewProjectButton } from "./new-project-button";
import { DeleteProjectDialog } from "./delete-project-dialog";
import { ProjectListSkeleton } from "@/components/ui/loading-skeleton";
import { EmptyState } from "@/components/ui/empty-state";

export function ProjectList() {
  const { data, isLoading } = useProjects();
  const { selectedProjectId, setSelectedProject } = useUIStore();
  const [deleteTarget, setDeleteTarget] = useState<{
    id: string;
    name: string;
  } | null>(null);

  if (isLoading) return <ProjectListSkeleton />;

  const projects = data?.projects || [];

  return (
    <div className="flex h-full flex-col">
      <div className="p-2">
        <NewProjectButton />
      </div>
      <div className="flex-1 space-y-0.5 overflow-y-auto px-2">
        {projects.length === 0 ? (
          <EmptyState title="No projects yet" description="Create your first project to get started" />
        ) : (
          projects.map((p) => (
            <div
              key={p.id}
              onContextMenu={(e) => {
                e.preventDefault();
                setDeleteTarget({ id: p.id, name: p.name });
              }}
            >
              <ProjectListItem
                project={p}
                isSelected={selectedProjectId === p.id}
                onSelect={() => setSelectedProject(p.id)}
              />
            </div>
          ))
        )}
      </div>
      {deleteTarget && (
        <DeleteProjectDialog
          projectId={deleteTarget.id}
          projectName={deleteTarget.name}
          open={!!deleteTarget}
          onOpenChange={(open) => !open && setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
