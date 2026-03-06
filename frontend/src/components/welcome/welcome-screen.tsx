"use client";

import { ChatWelcome } from "@/components/chat/chat-welcome";

export function WelcomeScreen() {
  return (
    <div className="flex h-full flex-col items-center justify-center bg-gradient-to-b from-background to-muted/20">
      <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold">AI Business Analysis</h1>
        <p className="mt-2 text-muted-foreground">
          Describe your business idea and get comprehensive analysis documents
        </p>
      </div>
      <ChatWelcome />
    </div>
  );
}
