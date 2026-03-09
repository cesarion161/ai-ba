"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAnswerNode } from "@/hooks/use-nodes";

interface AskUserFormProps {
  projectId: string;
  slug: string;
  questions: string[];
  outputData?: {
    answers?: Record<string, string>;
    prefilled?: boolean;
  } | null;
}

export function AskUserForm({ projectId, slug, questions, outputData }: AskUserFormProps) {
  const prefilled = outputData?.prefilled === true;
  const [answers, setAnswers] = useState<Record<string, string>>(
    outputData?.answers ?? {}
  );
  const answerMutation = useAnswerNode(projectId);

  const handleSubmit = () => {
    answerMutation.mutate({ slug, answers });
  };

  return (
    <div className="space-y-3">
      {prefilled && (
        <p className="text-sm text-muted-foreground italic">
          Pre-filled from your chat. Review and submit.
        </p>
      )}
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
