"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchDocumentTypes } from "@/lib/api/document-types";
import { useSelectDocuments } from "@/hooks/use-chat";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface DocTypeSelectorProps {
  projectId: string;
}

export function DocTypeSelector({ projectId }: DocTypeSelectorProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { data } = useQuery({
    queryKey: ["document-types"],
    queryFn: fetchDocumentTypes,
  });
  const selectMutation = useSelectDocuments(projectId);

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleConfirm = () => {
    if (selected.size === 0) return;
    selectMutation.mutate(Array.from(selected));
  };

  const docTypes = data?.document_types || [];

  return (
    <Card className="mx-auto max-w-lg p-4">
      <h3 className="mb-3 text-sm font-semibold">Select Document Types</h3>
      <div className="space-y-2">
        {docTypes.map((dt) => (
          <label
            key={dt.key}
            className="flex cursor-pointer items-start gap-3 rounded-md p-2 hover:bg-accent"
          >
            <Checkbox
              checked={selected.has(dt.key)}
              onCheckedChange={() => toggle(dt.key)}
              className="mt-0.5"
            />
            <div>
              <div className="text-sm font-medium">{dt.label}</div>
              <div className="text-xs text-muted-foreground">
                {dt.description}
              </div>
            </div>
          </label>
        ))}
      </div>
      <Button
        onClick={handleConfirm}
        disabled={selected.size === 0 || selectMutation.isPending}
        className="mt-4 w-full"
      >
        {selectMutation.isPending
          ? "Generating workflow..."
          : `Confirm (${selected.size} selected)`}
      </Button>
    </Card>
  );
}
