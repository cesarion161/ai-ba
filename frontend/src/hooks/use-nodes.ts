"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  approveNode,
  answerNode,
  editNodeOutput,
  fetchNode,
  fetchNodes,
  rejectNode,
  retryNode,
  skipNode,
} from "@/lib/api/nodes";

export function useNodes(projectId: string | null) {
  return useQuery({
    queryKey: ["nodes", projectId],
    queryFn: () => fetchNodes(projectId!),
    enabled: !!projectId,
  });
}

export function useNode(projectId: string | null, slug: string | null) {
  return useQuery({
    queryKey: ["node", projectId, slug],
    queryFn: () => fetchNode(projectId!, slug!),
    enabled: !!projectId && !!slug,
  });
}

export function useApproveNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => approveNode(projectId, slug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useRejectNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ slug, feedback }: { slug: string; feedback: string }) =>
      rejectNode(projectId, slug, feedback),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useRetryNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => retryNode(projectId, slug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useSkipNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (slug: string) => skipNode(projectId, slug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useAnswerNode(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      slug,
      answers,
    }: {
      slug: string;
      answers: Record<string, unknown>;
    }) => answerNode(projectId, slug, answers),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
      qc.invalidateQueries({ queryKey: ["graph", projectId] });
    },
  });
}

export function useEditNodeOutput(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      slug,
      outputData,
    }: {
      slug: string;
      outputData: Record<string, unknown>;
    }) => editNodeOutput(projectId, slug, outputData),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["nodes", projectId] });
    },
  });
}
