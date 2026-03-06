export interface NodeStatusChangedEvent {
  slug: string;
  status: string;
  label: string;
  branch: string;
}

export interface NodeRetryEvent {
  slug: string;
  attempt: number;
  max_retries: number;
}

export interface NodeFailedEvent {
  slug: string;
  error: string;
}

export interface NodeCompletedEvent {
  slug: string;
  output_summary?: string;
}

export interface WorkflowCompletedEvent {
  project_id: string;
  total_nodes: number;
  completed_nodes: number;
}

export interface ChatMessageEvent {
  role: string;
  content: string;
}

export interface ChatTokenEvent {
  token: string;
  done: boolean;
}

export interface GraphGeneratedEvent {
  node_count: number;
  phase: string;
}

export type SSEEventData =
  | NodeStatusChangedEvent
  | NodeRetryEvent
  | NodeFailedEvent
  | NodeCompletedEvent
  | WorkflowCompletedEvent
  | ChatMessageEvent
  | ChatTokenEvent
  | GraphGeneratedEvent;
