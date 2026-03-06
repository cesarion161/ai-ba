"use client";

import type { Node } from "@/lib/api/nodes";

export function NodeInputTab({ node }: { node: Node }) {
  if (!node.input_data || Object.keys(node.input_data).length === 0) {
    return <p className="text-sm text-muted-foreground">No input data.</p>;
  }

  return (
    <div className="space-y-3">
      {Object.entries(node.input_data).map(([key, value]) => (
        <div key={key}>
          <h4 className="text-xs font-semibold text-muted-foreground">{key}</h4>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-muted p-2 text-xs">
            {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  );
}
