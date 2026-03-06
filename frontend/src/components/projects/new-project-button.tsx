"use client";

import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";

export function NewProjectButton() {
  const setSelectedProject = useUIStore((s) => s.setSelectedProject);

  return (
    <Button
      variant="outline"
      size="sm"
      className="w-full"
      onClick={() => setSelectedProject(null)}
    >
      + New Project
    </Button>
  );
}
