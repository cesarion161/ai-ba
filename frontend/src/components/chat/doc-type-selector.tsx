"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchDocumentTypes, DocumentType } from "@/lib/api/document-types";
import { useSelectDocuments } from "@/hooks/use-chat";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/** Logical stage ordering and display labels for categories. */
const CATEGORY_ORDER: { key: string; label: string }[] = [
  { key: "strategy", label: "Strategy" },
  { key: "research", label: "Market Research" },
  { key: "requirements", label: "Requirements" },
  { key: "product", label: "Product" },
  { key: "technical", label: "Technical" },
  { key: "planning", label: "Planning" },
  { key: "delivery", label: "Delivery & QA" },
];

const categoryIndex = new Map(CATEGORY_ORDER.map((c, i) => [c.key, i]));
const categoryLabel = new Map(CATEGORY_ORDER.map((c) => [c.key, c.label]));

function groupAndSort(
  docTypes: DocumentType[],
): { label: string; items: DocumentType[] }[] {
  const sorted = [...docTypes].sort(
    (a, b) =>
      (categoryIndex.get(a.category) ?? 99) -
      (categoryIndex.get(b.category) ?? 99),
  );

  const groups: { label: string; items: DocumentType[] }[] = [];
  let currentCat = "";
  for (const dt of sorted) {
    if (dt.category !== currentCat) {
      currentCat = dt.category;
      groups.push({
        label: categoryLabel.get(currentCat) ?? currentCat,
        items: [],
      });
    }
    groups[groups.length - 1].items.push(dt);
  }
  return groups;
}

interface DocTypeSelectorProps {
  projectId: string;
}

export function DocTypeSelector({ projectId }: DocTypeSelectorProps) {
  const { data } = useQuery({
    queryKey: ["document-types"],
    queryFn: fetchDocumentTypes,
  });
  const selectMutation = useSelectDocuments(projectId);

  const docTypes = data?.document_types || [];

  // Pre-select all document types by default
  const allKeys = useMemo(
    () => new Set(docTypes.map((dt) => dt.key)),
    [docTypes],
  );
  const [selected, setSelected] = useState<Set<string> | null>(null);
  const effective = selected ?? allKeys;

  const toggle = (key: string) => {
    setSelected((prev) => {
      const base = prev ?? new Set(allKeys);
      const next = new Set(base);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleConfirm = () => {
    if (effective.size === 0) return;
    selectMutation.mutate(Array.from(effective));
  };

  const groups = useMemo(() => groupAndSort(docTypes), [docTypes]);

  return (
    <Card className="mx-auto max-w-lg p-4">
      <h3 className="mb-3 text-sm font-semibold">Select Document Types</h3>
      <div className="space-y-4">
        {groups.map((group) => (
          <div key={group.label}>
            <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {group.label}
            </h4>
            <div className="space-y-1">
              {group.items.map((dt) => (
                <label
                  key={dt.key}
                  className="flex cursor-pointer items-start gap-3 rounded-md p-2 hover:bg-accent"
                >
                  <Checkbox
                    checked={effective.has(dt.key)}
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
          </div>
        ))}
      </div>
      <Button
        onClick={handleConfirm}
        disabled={effective.size === 0 || selectMutation.isPending}
        className="mt-4 w-full"
      >
        {selectMutation.isPending
          ? "Generating workflow..."
          : `Confirm (${effective.size} selected)`}
      </Button>
    </Card>
  );
}
