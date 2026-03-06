"use client";

import { useCallback, useEffect, useState } from "react";
import { TopBar } from "./top-bar";
import { LeftSidebar } from "./left-sidebar";
import { CenterPane } from "./center-pane";
import { RightSidebar } from "./right-sidebar";
import { ResizeHandle } from "./resize-handle";
import { NodeDetailPanel } from "@/components/nodes/node-detail-panel";
import { useUIStore } from "@/stores/ui-store";
import { useProjectSSE } from "@/hooks/use-project-sse";

export function AppShell() {
  const [leftWidth, setLeftWidth] = useState(260);
  const [rightWidth, setRightWidth] = useState(340);
  const projectId = useUIStore((s) => s.selectedProjectId);
  const hydrateFromURL = useUIStore((s) => s.hydrateFromURL);

  useEffect(() => {
    hydrateFromURL();
  }, [hydrateFromURL]);

  useProjectSSE(projectId);

  const handleLeftResize = useCallback((delta: number) => {
    setLeftWidth((w) => Math.max(180, Math.min(400, w + delta)));
  }, []);

  const handleRightResize = useCallback((delta: number) => {
    setRightWidth((w) => Math.max(240, Math.min(500, w - delta)));
  }, []);

  return (
    <div className="flex h-screen flex-col">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <div style={{ width: leftWidth }} className="flex-shrink-0">
          <LeftSidebar />
        </div>
        <ResizeHandle direction="horizontal" onResize={handleLeftResize} />
        <div className="flex-1 overflow-hidden">
          <CenterPane />
        </div>
        <ResizeHandle direction="horizontal" onResize={handleRightResize} />
        <div style={{ width: rightWidth }} className="flex-shrink-0">
          <RightSidebar />
        </div>
      </div>
      <NodeDetailPanel />
    </div>
  );
}
