"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAnswerNode } from "@/hooks/use-nodes";

interface AskUserFormProps {
  projectId: string;
  slug: string;
  questions: string[];
}

export function AskUserForm({ projectId, slug, questions }: AskUserFormProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const answerMutation = useAnswerNode(projectId);

  const handleSubmit = () => {
    answerMutation.mutate({ slug, answers });
  };

  return (
    <div className="space-y-3">
      {questions.map((q, i) => (
        <div key={i}>
          <label className="mb-1 block text-sm font-medium">{q}</label>
          <Input
            value={answers[q] || ""}
            onChange={(e) =>
              setAnswers((prev) => ({ ...prev, [q]: e.target.value }))
            }
          />
        </div>
      ))}
      <Button
        onClick={handleSubmit}
        disabled={answerMutation.isPending}
        size="sm"
      >
        Submit Answers
      </Button>
    </div>
  );
}
