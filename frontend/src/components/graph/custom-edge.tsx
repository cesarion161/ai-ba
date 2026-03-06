"use client";

import { memo } from "react";
import { BaseEdge, getStraightPath } from "@xyflow/react";

function CustomEdgeComponent({
  sourceX,
  sourceY,
  targetX,
  targetY,
  ...rest
}: {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  style?: React.CSSProperties;
  markerEnd?: string;
}) {
  const [edgePath] = getStraightPath({ sourceX, sourceY, targetX, targetY });

  return (
    <BaseEdge
      path={edgePath}
      style={{ stroke: "#94a3b8", strokeWidth: 1.5, ...rest.style }}
      markerEnd={rest.markerEnd}
    />
  );
}

export const CustomEdge = memo(CustomEdgeComponent);
