"use client";

import { useEffect, useRef } from "react";
import { useChatHistory, useSendMessage } from "@/hooks/use-chat";
import { useProject } from "@/hooks/use-projects";
import { useChatStream } from "@/hooks/use-chat-stream";
import { ChatMessageBubble } from "./chat-message";
import { ChatInput } from "./chat-input";
import { DocTypeSelector } from "./doc-type-selector";
import { ChatSkeleton } from "@/components/ui/loading-skeleton";
import { PhaseIndicator } from "@/components/welcome/phase-indicator";
import { cn } from "@/lib/utils";

interface ChatPanelProps {
  projectId: string;
  mode: "center" | "sidebar";
}

export function ChatPanel({ projectId, mode }: ChatPanelProps) {
  const { data: chatData, isLoading } = useChatHistory(projectId);
  const { data: project } = useProject(projectId);
  const sendMutation = useSendMessage(projectId);
  const { streamingContent } = useChatStream(projectId);
  const scrollRef = useRef<HTMLDivElement>(null);

  const messages = chatData?.messages || [];
  const phase = project?.chat_phase;

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages.length, streamingContent]);

  if (isLoading) return <ChatSkeleton />;

  const showDocSelector = phase === "selecting_documents";

  return (
    <div className={cn("flex h-full flex-col", mode === "center" && "mx-auto max-w-2xl")}>
      {mode === "center" && phase && (
        <div className="border-b p-3">
          <PhaseIndicator currentPhase={phase} />
        </div>
      )}
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((msg) => (
          <ChatMessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}
        {streamingContent && (
          <ChatMessageBubble role="assistant" content={streamingContent} />
        )}
        {showDocSelector && <DocTypeSelector projectId={projectId} />}
      </div>
      <ChatInput
        onSend={(content) => sendMutation.mutate(content)}
        disabled={sendMutation.isPending || showDocSelector || phase === "generating_graph"}
        placeholder={
          phase === "generating_graph"
            ? "Generating workflow..."
            : "Type a message..."
        }
      />
    </div>
  );
}
