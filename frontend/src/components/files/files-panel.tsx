"use client";

import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNodes } from "@/hooks/use-nodes";
import { useUIStore } from "@/stores/ui-store";
import type { Node } from "@/lib/api/nodes";

interface FilesPanelProps {
  projectId: string;
}

function getFileContent(node: Node): string | null {
  if (!node.output_data) return null;
  if (typeof node.output_data === "string") return node.output_data;
  const doc =
    (node.output_data.document as string | undefined) ||
    (node.output_data.summary as string | undefined) ||
    (node.output_data.result as string | undefined);
  return doc || null;
}

function getFileExtension(node: Node): string {
  if (node.node_type === "format_export") return ".md";
  if (node.node_type === "calculate") return ".txt";
  return ".md";
}

export function FilesPanel({ projectId }: FilesPanelProps) {
  const { data } = useNodes(projectId);
  const openNodeDetail = useUIStore((s) => s.openNodeDetail);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const files = useMemo(() => {
    if (!data?.nodes) return [];
    return data.nodes.filter(
      (n) =>
        (n.status === "approved" || n.status === "skipped") &&
        getFileContent(n) !== null,
    );
  }, [data]);

  const allSelected = files.length > 0 && selected.size === files.length;

  function toggleAll() {
    if (allSelected) {
      setSelected(new Set());
    } else {
      setSelected(new Set(files.map((f) => f.slug)));
    }
  }

  function toggle(slug: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  function downloadSelected() {
    const toDownload = files.filter((f) => selected.has(f.slug));
    for (const node of toDownload) {
      const content = getFileContent(node);
      if (!content) continue;
      const blob = new Blob([content], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${node.slug}${getFileExtension(node)}`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  if (files.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-sm text-muted-foreground">
          No generated files yet. Complete workflow nodes to see results here.
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b px-4 py-2">
        <Checkbox
          checked={allSelected}
          onCheckedChange={toggleAll}
          aria-label="Select all"
        />
        <span className="text-sm font-medium">
          {selected.size > 0
            ? `${selected.size} of ${files.length} selected`
            : `${files.length} files`}
        </span>
        <Button
          size="sm"
          variant="outline"
          onClick={downloadSelected}
          disabled={selected.size === 0}
          className="ml-auto"
        >
          Download Selected
        </Button>
      </div>
      <ScrollArea className="flex-1">
        <div className="divide-y">
          {files.map((node) => (
            <div
              key={node.slug}
              className="flex items-center gap-3 px-4 py-3 hover:bg-muted/50 cursor-pointer"
              onClick={() => openNodeDetail(node.slug)}
            >
              <Checkbox
                checked={selected.has(node.slug)}
                onCheckedChange={() => toggle(node.slug)}
                onClick={(e) => e.stopPropagation()}
                aria-label={`Select ${node.label}`}
              />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{node.label}</p>
                <p className="text-xs text-muted-foreground">
                  {node.node_type} &middot; {node.branch}
                </p>
              </div>
              <span className="text-xs text-muted-foreground shrink-0">
                {node.slug}{getFileExtension(node)}
              </span>
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
