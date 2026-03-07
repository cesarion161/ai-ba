"use client";

import { useMemo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

interface MarkdownViewerProps {
  content: string;
  compact?: boolean;
}

/**
 * Convert LaTeX bracket delimiters to dollar-sign delimiters
 * that remark-math understands:
 *   \[ ... \]  or  [ ... ]  (display math) → $$ ... $$
 *   \( ... \)  (inline math) → $ ... $
 */
function normalizeLatex(text: string): string {
  // \[ ... \] → $$ ... $$ (handle multiline by replacing line by line isn't needed — these are typically single line)
  let result = text.replace(new RegExp("\\\\\\[(.+?)\\\\\\]", "g"), (_, math) => `$$${math}$$`);
  // \( ... \) → $ ... $
  result = result.replace(new RegExp("\\\\\\((.+?)\\\\\\)", "g"), (_, math) => `$${math}$`);
  // Standalone [ \text{...} ... ] on its own line (LLM-style display math)
  result = result.replace(
    /^\[\s*(\\(?:text|frac|sqrt|times|div|cdot|sum|prod|int|lim|log|ln|sin|cos|tan)\b.+?)\s*\]$/gm,
    (_, math) => `$$${math}$$`,
  );
  return result;
}

export function MarkdownViewer({ content, compact }: MarkdownViewerProps) {
  const normalized = useMemo(() => normalizeLatex(content), [content]);

  return (
    <div
      className={
        compact
          ? "prose prose-sm dark:prose-invert max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 [&_p]:my-1 [&_ul]:my-1 [&_ol]:my-1 [&_li]:my-0"
          : "prose prose-sm dark:prose-invert max-w-none"
      }
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
