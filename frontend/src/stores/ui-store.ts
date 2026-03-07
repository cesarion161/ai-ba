import { create } from "zustand";

function getProjectIdFromURL(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return params.get("project") || null;
}

function syncProjectIdToURL(id: string | null) {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (id) {
    url.searchParams.set("project", id);
  } else {
    url.searchParams.delete("project");
  }
  window.history.replaceState({}, "", url.toString());
}

interface UIState {
  selectedProjectId: string | null;
  selectedNodeSlug: string | null;
  isNodeDetailOpen: boolean;
  centerTab: "graph" | "files";
  setCenterTab: (tab: "graph" | "files") => void;
  setSelectedProject: (id: string | null) => void;
  setSelectedNode: (slug: string | null) => void;
  openNodeDetail: (slug: string) => void;
  closeNodeDetail: () => void;
  hydrateFromURL: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedProjectId: null,
  selectedNodeSlug: null,
  isNodeDetailOpen: false,
  centerTab: "graph",
  setCenterTab: (tab) => set({ centerTab: tab }),
  setSelectedProject: (id) => {
    syncProjectIdToURL(id);
    set({ selectedProjectId: id, selectedNodeSlug: null, isNodeDetailOpen: false });
  },
  setSelectedNode: (slug) => set({ selectedNodeSlug: slug }),
  openNodeDetail: (slug) =>
    set({ selectedNodeSlug: slug, isNodeDetailOpen: true }),
  closeNodeDetail: () => set({ isNodeDetailOpen: false }),
  hydrateFromURL: () => {
    const id = getProjectIdFromURL();
    if (id) {
      set({ selectedProjectId: id });
    }
  },
}));
