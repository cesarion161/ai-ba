import { toast } from "sonner";
import { ApiError } from "./api-client";

export function formatError(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred";
}

export function showErrorToast(error: unknown, context?: string) {
  const message = formatError(error);
  toast.error(context || "Error", { description: message });
}
