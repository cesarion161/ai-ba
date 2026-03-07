"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchGraph,
  fetchGraphStatus,
  fetchPreflight,
  runGraph,
  deleteGraphNode,
  addGraphNode,
  addGraphEdge,
} from "@/lib/api/graph";

export function useGraph(projectId: string | null) {
  return useQuery({
    queryKey: ["graph", projectId],
    queryFn: () => fetchGraph(projectId!),
    enabled: !!projectId,
  });
}

export function useGraphStatus(projectId: string | null) {
  return useQuery({
    queryKey: ["graph-status", projectId],
    queryFn: () => fetchGraphStatus(projectId!),
    enabled: !!projectId,
    refetchInterval: 3000,
  });
}

export function useRunGraph(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => runGraph(projectId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
      qc.invalidateQueries({ queryKey: ["graph-status", projectId] });
      qc.invalidateQueries({ queryKey: ["project", projectId] });
    },
  });
}

export function useDeleteGraphNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => deleteGraphNode(projectId, slug),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["graph", projectId] }),
  });
}

export function useAddGraphNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: addGraphNode.bind(null, projectId),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["graph", projectId] }),
  });
}

export function usePreflight(projectId: string | null) {
  return useQuery({
    queryKey: ["preflight", projectId],
    queryFn: () => fetchPreflight(projectId!),
    enabled: !!projectId,
  });
}

export function useAddGraphEdge(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ from, to }: { from: string; to: string }) =>
      addGraphEdge(projectId, from, to),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["graph", projectId] }),
  });
}
