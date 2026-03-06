import { create } from "zustand";

interface UIState {
  selectedProjectId: string | null;
  selectedNodeSlug: string | null;
  isNodeDetailOpen: boolean;
  setSelectedProject: (id: string | null) => void;
  setSelectedNode: (slug: string | null) => void;
  openNodeDetail: (slug: string) => void;
  closeNodeDetail: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  selectedProjectId: null,
  selectedNodeSlug: null,
  isNodeDetailOpen: false,
  setSelectedProject: (id) =>
    set({ selectedProjectId: id, selectedNodeSlug: null, isNodeDetailOpen: false }),
  setSelectedNode: (slug) => set({ selectedNodeSlug: slug }),
  openNodeDetail: (slug) =>
    set({ selectedNodeSlug: slug, isNodeDetailOpen: true }),
  closeNodeDetail: () => set({ isNodeDetailOpen: false }),
}));
