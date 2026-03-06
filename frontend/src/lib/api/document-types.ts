import { apiFetch } from "../api-client";

export interface DocumentType {
  id: string;
  key: string;
  label: string;
  description: string;
  category: string;
  default_dependencies: string[] | null;
  is_active: boolean;
  created_at: string;
}

export interface DocumentTypeListResponse {
  document_types: DocumentType[];
}

export function fetchDocumentTypes(): Promise<DocumentTypeListResponse> {
  return apiFetch("/api/document-types");
}
