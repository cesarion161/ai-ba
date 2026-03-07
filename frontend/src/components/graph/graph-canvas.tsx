"use client";

import { useCallback, useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node as RFNode,
  type Edge as RFEdge,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useGraph } from "@/hooks/use-graph";
import { useGraphSSE } from "@/hooks/use-graph-sse";
import { useUIStore } from "@/stores/ui-store";
import { layoutGraph } from "@/lib/graph-layout";
import { getStatusColor } from "@/lib/colors";
import { CustomNode } from "./custom-node";
import { GraphToolbar } from "./graph-toolbar";
import { GraphEditToolbar } from "./graph-edit-toolbar";
import { GraphSkeleton } from "@/components/ui/loading-skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useProject } from "@/hooks/use-projects";

const nodeTypes = { custom: CustomNode };

interface GraphCanvasProps {
  projectId: string;
}

export function GraphCanvas({ projectId }: GraphCanvasProps) {
  const { data: graphData, isLoading } = useGraph(projectId);
  const { data: project } = useProject(projectId);
  const openNodeDetail = useUIStore((s) => s.openNodeDetail);
  const setSelectedNode = useUIStore((s) => s.setSelectedNode);

  useGraphSSE(projectId);

  const { initialNodes, initialEdges } = useMemo(() => {
    if (!graphData) return { initialNodes: [], initialEdges: [] };

    const layout = layoutGraph(graphData.nodes, graphData.edges);

    const rfNodes: RFNode[] = graphData.nodes.map((n) => {
      const pos = layout.nodes.find((ln) => ln.slug === n.slug);
      return {
        id: n.slug,
        type: "custom",
        position: { x: pos?.x || 0, y: pos?.y || 0 },
        data: {
          label: n.label,
          status: n.status,
          nodeType: n.node_type,
          branch: n.branch,
          requiresApproval: n.requires_approval,
        },
      };
    });

    const nodeStatusMap = Object.fromEntries(
      graphData.nodes.map((n) => [n.slug, n.status]),
    );

    const rfEdges: RFEdge[] = graphData.edges.map((e) => {
      const sourceStatus = nodeStatusMap[e.from_slug] || "pending";
      const isDone = sourceStatus === "approved" || sourceStatus === "skipped";
      const isActive = sourceStatus === "running";
      const edgeColor = isDone ? "#22C55E" : isActive ? "#3B82F6" : "#94a3b8";
      return {
        id: `${e.from_slug}-${e.to_slug}`,
        source: e.from_slug,
        target: e.to_slug,
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
        style: { stroke: edgeColor, strokeWidth: isDone ? 2 : 1.5 },
        animated: isActive,
      };
    });

    return { initialNodes: rfNodes, initialEdges: rfEdges };
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: RFNode) => {
      setSelectedNode(node.id);
      openNodeDetail(node.id);
    },
    [setSelectedNode, openNodeDetail],
  );

  if (isLoading) return <GraphSkeleton />;

  if (!graphData || graphData.nodes.length === 0) {
    return <EmptyState title="No graph yet" description="Generate a workflow to see the graph" />;
  }

  const isEditable = project?.chat_phase === "graph_ready" || !project?.chat_phase;

  return (
    <div className="flex h-full flex-col">
      <GraphToolbar projectId={projectId} />
      {isEditable && <GraphEditToolbar projectId={projectId} />}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.3}
          maxZoom={2}
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => getStatusColor((node.data as { status: string })?.status || "pending")}
            maskColor="rgba(0,0,0,0.1)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
