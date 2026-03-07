"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { MarkdownViewer } from "@/components/editor/markdown-viewer";
import { MarkdownEditor } from "@/components/editor/markdown-editor";
import { useEditNodeOutput } from "@/hooks/use-nodes";
import type { Node } from "@/lib/api/nodes";

function formatAskUserOutput(outputData: Record<string, unknown>): string {
  const questions = (outputData.questions as string[]) || [];
  const answers = (outputData.answers as Record<string, unknown>) || {};

  if (outputData.awaiting_answers && !Object.keys(answers).length) {
    return (
      "**Awaiting user answers**\n\n" +
      questions.map((q, i) => `${i + 1}. ${q}`).join("\n")
    );
  }

  const lines: string[] = ["## Questions & Answers\n"];
  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    const a = answers[String(i)] || answers[q] || "_No answer provided_";
    lines.push(`**Q: ${q}**\n\n${a}\n`);
  }
  return lines.join("\n");
}

function extractContent(node: Node): string {
  const od = node.output_data;
  if (!od) return "";

  if (typeof od === "string") return od;

  // ask_user nodes: format Q&A
  if (node.node_type === "ask_user" && (od.questions || od.answers)) {
    return formatAskUserOutput(od);
  }

  // critic_review: format verdict + feedback
  if (node.node_type === "critic_review" && od.verdict) {
    const score = od.score ?? "N/A";
    const verdict = String(od.verdict).toUpperCase();
    const feedback = od.feedback || "No feedback";
    return `## Review Result\n\n**Verdict:** ${verdict} &nbsp; **Score:** ${score}\n\n${feedback}`;
  }

  return (
    (od.document as string | undefined) ||
    (od.summary as string | undefined) ||
    (od.result as string | undefined) ||
    JSON.stringify(od, null, 2)
  );
}

export function NodeOutputTab({
  projectId,
  node,
}: {
  projectId: string;
  node: Node;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const editMutation = useEditNodeOutput(projectId);

  if (!node.output_data) {
    return (
      <p className="text-sm text-muted-foreground">No output data yet.</p>
    );
  }

  const content = extractContent(node);

  if (isEditing) {
    return (
      <MarkdownEditor
        initialContent={content}
        onSave={(newContent) => {
          editMutation.mutate({
            slug: node.slug,
            outputData: { ...node.output_data, document: newContent },
          });
          setIsEditing(false);
        }}
        onCancel={() => setIsEditing(false)}
      />
    );
  }

  return (
    <div>
      <div className="mb-2 flex justify-end">
        <Button size="sm" variant="outline" onClick={() => setIsEditing(true)}>
          Edit
        </Button>
      </div>
      <MarkdownViewer content={content} />
    </div>
  );
}
