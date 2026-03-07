"use client";

import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useUIStore } from "@/stores/ui-store";
import { useNode } from "@/hooks/use-nodes";
import { NodeOverviewTab } from "./node-overview-tab";
import { NodeOutputTab } from "./node-output-tab";
import { NodeInputTab } from "./node-input-tab";
import { NodeArtifactsTab } from "./node-artifacts-tab";
import { NodeActions } from "./node-actions";
import { AskUserForm } from "./ask-user-form";
import { NodeDetailSkeleton } from "@/components/ui/loading-skeleton";

export function NodeDetailPanel() {
  const { selectedProjectId, selectedNodeSlug, isNodeDetailOpen, closeNodeDetail } =
    useUIStore();

  const { data: node, isLoading } = useNode(selectedProjectId, selectedNodeSlug);

  return (
    <Sheet open={isNodeDetailOpen} onOpenChange={(open) => !open && closeNodeDetail()}>
      <SheetContent className="w-[480px] overflow-y-auto sm:max-w-[480px]">
        <SheetHeader>
          <SheetTitle>{node?.label || selectedNodeSlug}</SheetTitle>
        </SheetHeader>

        {isLoading ? (
          <div className="px-4"><NodeDetailSkeleton /></div>
        ) : node ? (
          <div className="space-y-4 px-4 pb-6">
            <NodeActions projectId={selectedProjectId!} node={node} />

            {node.node_type === "ask_user" &&
              node.status === "awaiting_review" &&
              node.config?.questions ? (
                <AskUserForm
                  projectId={selectedProjectId!}
                  slug={node.slug}
                  questions={node.config.questions as string[]}
                />
              ) : null}

            <Tabs defaultValue="overview">
              <TabsList className="w-full">
                <TabsTrigger value="overview" className="flex-1">Overview</TabsTrigger>
                <TabsTrigger value="output" className="flex-1">Output</TabsTrigger>
                <TabsTrigger value="input" className="flex-1">Input</TabsTrigger>
                <TabsTrigger value="artifacts" className="flex-1">Artifacts</TabsTrigger>
              </TabsList>
              <TabsContent value="overview">
                <NodeOverviewTab node={node} />
              </TabsContent>
              <TabsContent value="output">
                <NodeOutputTab projectId={selectedProjectId!} node={node} />
              </TabsContent>
              <TabsContent value="input">
                <NodeInputTab node={node} />
              </TabsContent>
              <TabsContent value="artifacts">
                <NodeArtifactsTab />
              </TabsContent>
            </Tabs>
          </div>
        ) : (
          <p className="mt-4 px-4 text-sm text-muted-foreground">Node not found.</p>
        )}
      </SheetContent>
    </Sheet>
  );
}
