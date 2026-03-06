import dagre from "@dagrejs/dagre";
import type { GraphNode, GraphEdge } from "./api/graph";

interface LayoutResult {
  nodes: { slug: string; x: number; y: number }[];
  width: number;
  height: number;
}

export function layoutGraph(
  nodes: GraphNode[],
  edges: GraphEdge[],
): LayoutResult {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80, marginx: 40, marginy: 40 });

  for (const node of nodes) {
    g.setNode(node.slug, { width: 180, height: 60 });
  }

  for (const edge of edges) {
    g.setEdge(edge.from_slug, edge.to_slug);
  }

  dagre.layout(g);

  const layoutNodes = nodes.map((n) => {
    const pos = g.node(n.slug);
    return { slug: n.slug, x: pos.x - 90, y: pos.y - 30 };
  });

  const graph = g.graph();
  return {
    nodes: layoutNodes,
    width: (graph.width || 800) + 80,
    height: (graph.height || 600) + 80,
  };
}
