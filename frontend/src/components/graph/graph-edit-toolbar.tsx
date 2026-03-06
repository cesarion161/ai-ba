"use client";

import { Button } from "@/components/ui/button";
import { useDeleteGraphNode } from "@/hooks/use-graph";
import { useUIStore } from "@/stores/ui-store";

interface GraphEditToolbarProps {
  projectId: string;
}

export function GraphEditToolbar({ projectId }: GraphEditToolbarProps) {
  const selectedNodeSlug = useUIStore((s) => s.selectedNodeSlug);
  const deleteMutation = useDeleteGraphNode(projectId);

  return (
    <div className="flex items-center gap-2 border-b bg-muted/50 px-4 py-1">
      <span className="text-xs text-muted-foreground">Edit mode</span>
      {selectedNodeSlug && (
        <Button
          variant="destructive"
          size="sm"
          onClick={() => deleteMutation.mutate(selectedNodeSlug)}
          disabled={deleteMutation.isPending}
        >
          Delete Selected
        </Button>
      )}
    </div>
  );
}
