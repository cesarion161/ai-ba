"use client";

import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

interface MarkdownEditorProps {
  initialContent: string;
  onSave: (content: string) => void;
  onCancel: () => void;
}

export function MarkdownEditor({
  initialContent,
  onSave,
  onCancel,
}: MarkdownEditorProps) {
  const [content, setContent] = useState(initialContent);

  return (
    <div className="space-y-2">
      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        rows={20}
        className="font-mono text-sm"
      />
      <div className="flex gap-2">
        <Button size="sm" onClick={() => onSave(content)}>
          Save
        </Button>
        <Button size="sm" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
