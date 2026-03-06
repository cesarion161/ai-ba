"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { StatusBadge } from "@/components/ui/status-badge";
import { getStatusColor } from "@/lib/colors";
import { cn } from "@/lib/utils";

interface CustomNodeData {
  label: string;
  status: string;
  nodeType: string;
  branch: string;
  requiresApproval: boolean;
  [key: string]: unknown;
}

const NODE_TYPE_ICONS: Record<string, string> = {
  research: "🔍",
  calculate: "📊",
  generate_document: "📝",
  ask_user: "💬",
  critic_review: "🔎",
  densify: "📚",
  format_export: "📦",
};

function CustomNodeComponent({ data }: { data: CustomNodeData }) {
  const { label, status, nodeType, branch } = data;
  const color = getStatusColor(status);
  const icon = NODE_TYPE_ICONS[nodeType] || "📄";

  const isAnimated =
    status === "running" || status === "awaiting_review" || status === "failed";

  return (
    <div
      className={cn(
        "rounded-lg border-2 bg-background px-3 py-2 shadow-sm transition-all",
        status === "running" && "animate-pulse",
        status === "awaiting_review" && "animate-[slow-blink_2s_ease-in-out_infinite]",
        status === "failed" && "animate-[glow-pulse_1.5s_ease-in-out_infinite]",
        isAnimated && "shadow-md",
      )}
      style={{ borderColor: color, minWidth: 160 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-muted-foreground" />
      <div className="flex items-center gap-2">
        <span className="text-sm">{icon}</span>
        <div className="flex-1 truncate text-xs font-medium">{label}</div>
      </div>
      <div className="mt-1 flex items-center justify-between">
        <span className="text-[10px] text-muted-foreground">{branch}</span>
        <StatusBadge status={status} />
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-muted-foreground" />
    </div>
  );
}

export const CustomNode = memo(CustomNodeComponent);
