"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MarkdownViewer } from "@/components/editor/markdown-viewer";
import { MarkdownEditor } from "@/components/editor/markdown-editor";
import { useEditNodeOutput } from "@/hooks/use-nodes";
import type { Node } from "@/lib/api/nodes";

export function NodeOutputTab({
  projectId,
  node,
}: {
  projectId: string;
  node: Node;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const editMutation = useEditNodeOutput(projectId);

  if (!node.output_data) {
    return (
      <p className="text-sm text-muted-foreground">No output data yet.</p>
    );
  }

  const raw =
    typeof node.output_data === "string"
      ? node.output_data
      : (node.output_data.document as string | undefined) ||
        (node.output_data.summary as string | undefined) ||
        JSON.stringify(node.output_data, null, 2);
  const content = String(raw);

  if (isEditing) {
    return (
      <MarkdownEditor
        initialContent={content}
        onSave={(newContent) => {
          editMutation.mutate({
            slug: node.slug,
            outputData: { ...node.output_data, document: newContent },
          });
          setIsEditing(false);
        }}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  return (
    <div>
      <div className="mb-2 flex justify-end">
        <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
          Edit
        </Button>
      </div>
      <MarkdownViewer content={content} />
    </div>
  );
}
