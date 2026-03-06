"use client";

import { ProjectList } from "@/components/projects/project-list";

export function LeftSidebar() {
  return (
    <aside className="flex h-full flex-col border-r bg-muted/30">
      <div className="border-b px-3 py-2">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Projects
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        <ProjectList />
      </div>
    </aside>
  );
}
