"use client";

interface MarkdownViewerProps {
  content: string;
}

export function MarkdownViewer({ content }: MarkdownViewerProps) {
  // Simple markdown rendering with basic formatting
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <pre className="whitespace-pre-wrap rounded bg-muted p-4 text-sm leading-relaxed">
        {content}
      </pre>
    </div>
  );
}
