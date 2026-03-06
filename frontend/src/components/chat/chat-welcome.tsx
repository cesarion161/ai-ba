"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useCreateProjectFromChat } from "@/hooks/use-projects";
import { useUIStore } from "@/stores/ui-store";

export function ChatWelcome() {
  const [prompt, setPrompt] = useState("");
  const createMutation = useCreateProjectFromChat();
  const setSelectedProject = useUIStore((s) => s.setSelectedProject);

  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    const result = await createMutation.mutateAsync({ initial_prompt: prompt });
    setSelectedProject(result.project_id);
  };

  return (
    <div className="flex h-full flex-col items-center justify-center p-8">
      <h2 className="mb-2 text-xl font-semibold">Start a New Analysis</h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Describe your business idea and I&apos;ll help you build a comprehensive analysis.
      </p>
      <div className="flex w-full max-w-lg gap-2">
        <Input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          placeholder="e.g., A marketplace for freelance designers..."
          className="flex-1"
        />
        <Button
          onClick={handleSubmit}
          disabled={!prompt.trim() || createMutation.isPending}
        >
          {createMutation.isPending ? "..." : "Go"}
        </Button>
      </div>
    </div>
  );
}
