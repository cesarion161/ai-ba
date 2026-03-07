"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface MarkdownViewerProps {
  content: string;
}

/**
 * Convert LaTeX bracket delimiters to dollar-sign delimiters
 * that remark-math understands:
 *   \[ ... \]  or  [ ... ]  (display math) → $$ ... $$
 *   \( ... \)  (inline math) → $ ... $
 */
function normalizeLatex(text: string): string {
  // \[ ... \] → $$ ... $$
  let result = text.replace(/\\\[(.+?)\\\]/gs, (_, math) => `$$${math}$$`);
  // \( ... \) → $ ... $
  result = result.replace(/\\\((.+?)\\\)/gs, (_, math) => `$${math}$`);
  // Standalone [ \text{...} ... ] on its own line (LLM-style display math)
  result = result.replace(
    /^\[\s*(\\(?:text|frac|sqrt|times|div|cdot|sum|prod|int|lim|log|ln|sin|cos|tan)\b.+?)\s*\]$/gm,
    (_, math) => `$$${math}$$`,
  );
  return result;
}

export function MarkdownViewer({ content }: MarkdownViewerProps) {
  const normalized = useMemo(() => normalizeLatex(content), [content]);

  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
