import { apiFetch } from "../api-client";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  template_key: string;
  status: string;
  chat_phase: string | null;
  selected_doc_types: string[] | null;
  created_at: string;
}

export interface ProjectListResponse {
  projects: Project[];
}

export function fetchProjects(): Promise<ProjectListResponse> {
  return apiFetch("/api/projects");
}

export function fetchProject(id: string): Promise<Project> {
  return apiFetch(`/api/projects/${id}`);
}

export function createProject(data: {
  name: string;
  description?: string;
  template_key?: string;
}): Promise<Project> {
  return apiFetch("/api/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function createProjectFromChat(data: {
  initial_prompt: string;
  name?: string;
}): Promise<{ id: string; project_id: string; content: string }> {
  return apiFetch("/api/projects/from-chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteProject(id: string): Promise<void> {
  return apiFetch(`/api/projects/${id}`, { method: "DELETE" });
}
