import { apiFetch } from "../api-client";

export interface UIConfig {
  status_colors: Record<string, string>;
  node_status_colors: Record<string, string>;
  chat_phase_colors: Record<string, string>;
}

export function fetchUIConfig(): Promise<UIConfig> {
  return apiFetch("/api/config/ui");
}
