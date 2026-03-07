"use client";

import { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { StatusBadge } from "@/components/ui/status-badge";
import { getStatusColor, getStatusBg } from "@/lib/colors";
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
  const bg = getStatusBg(status);
  const icon = NODE_TYPE_ICONS[nodeType] || "📄";

  const isRunning = status === "running";
  const isAnimated =
    isRunning || status === "awaiting_review" || status === "failed";

  return (
    <div
      className={cn(
        "rounded-lg border-2 px-3 py-2 shadow-sm transition-all duration-300",
        isRunning && "shadow-lg shadow-blue-500/20",
        status === "awaiting_review" && "animate-[slow-blink_2s_ease-in-out_infinite] shadow-md shadow-amber-500/20",
        status === "failed" && "animate-[glow-pulse_1.5s_ease-in-out_infinite]",
        status === "approved" && "shadow-md shadow-green-500/10",
        status === "pending" && "opacity-60",
        isAnimated && "shadow-md",
      )}
      style={{ borderColor: color, backgroundColor: bg, minWidth: 160 }}
    >
      <Handle type="target" position={Position.Top} className="!bg-muted-foreground" />
      <div className="flex items-center gap-2">
        <span className="text-sm">
          {isRunning ? (
            <span className="inline-block animate-spin">⚙️</span>
          ) : (
            icon
          )}
        </span>
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
