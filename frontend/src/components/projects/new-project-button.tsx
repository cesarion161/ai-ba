"use client";

import { Button } from "@/components/ui/button";
import { useUIStore } from "@/stores/ui-store";
import { useCreateProjectFromChat } from "@/hooks/use-projects";
import { useState } from "react";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

export function NewProjectButton() {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const createMutation = useCreateProjectFromChat();
  const setSelectedProject = useUIStore((s) => s.setSelectedProject);

  const handleCreate = async () => {
    if (!prompt.trim()) return;
    const result = await createMutation.mutateAsync({
      initial_prompt: prompt,
    });
    setSelectedProject(result.project_id);
    setOpen(false);
    setPrompt("");
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm" className="w-full">
          + New Project
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Business Analysis</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Describe your business idea and I&apos;ll help you analyze it.
          </p>
          <Input
            placeholder="e.g., A SaaS platform for restaurant inventory management..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <Button
            onClick={handleCreate}
            disabled={!prompt.trim() || createMutation.isPending}
            className="w-full"
          >
            {createMutation.isPending ? "Creating..." : "Start Analysis"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
