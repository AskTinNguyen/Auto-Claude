/**
 * ScratchPad Store
 *
 * Manages UI state for ScratchPad (Notes, Snippets, Templates)
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ScratchPadColumn = 'notes' | 'snippets' | 'templates';

export interface SelectedItem {
  column: ScratchPadColumn;
  id: string; // For snippets: name, for templates: id
}

interface ScratchPadState {
  // UI State
  isOpen: boolean;
  activeColumn: ScratchPadColumn;
  searchQuery: string;
  selectedProjectPath: string | null;
  selectedItem: SelectedItem | null;

  // Modal States
  isAddSnippetDialogOpen: boolean;
  isAddTemplateDialogOpen: boolean;
  isPreviewModalOpen: boolean;
  previewContent: { title: string; content: string } | null;

  // Edit State (for templates)
  editingTemplateId: string | null;

  // Actions - Navigation
  setIsOpen: (isOpen: boolean) => void;
  setActiveColumn: (column: ScratchPadColumn) => void;
  setSearchQuery: (query: string) => void;
  setSelectedProjectPath: (path: string | null) => void;

  // Actions - Selection
  setSelectedItem: (item: SelectedItem | null) => void;
  clearSelection: () => void;

  // Actions - Modals
  openAddSnippetDialog: () => void;
  closeAddSnippetDialog: () => void;
  openAddTemplateDialog: () => void;
  closeAddTemplateDialog: () => void;
  openPreviewModal: (title: string, content: string) => void;
  closePreviewModal: () => void;

  // Actions - Template Editing
  setEditingTemplateId: (id: string | null) => void;
  openEditTemplateDialog: (id: string) => void;
  closeEditTemplateDialog: () => void;

  // Actions - Navigation Helpers
  jumpToColumn: (column: ScratchPadColumn) => void;
  cycleColumn: (direction: 'next' | 'prev') => void;
}

const COLUMN_ORDER: ScratchPadColumn[] = ['notes', 'snippets', 'templates'];

export const useScratchPadStore = create<ScratchPadState>()(
  persist(
    (set, get) => ({
      // Initial State
      isOpen: false,
      activeColumn: 'notes',
      searchQuery: '',
      selectedProjectPath: null,
      selectedItem: null,

      isAddSnippetDialogOpen: false,
      isAddTemplateDialogOpen: false,
      isPreviewModalOpen: false,
      previewContent: null,

      editingTemplateId: null,

      // Navigation Actions
      setIsOpen: (isOpen) => set({ isOpen }),

      setActiveColumn: (column) => set({
        activeColumn: column,
        // Clear selection when changing columns
        selectedItem: null
      }),

      setSearchQuery: (query) => set({ searchQuery: query }),

      setSelectedProjectPath: (path) => set({
        selectedProjectPath: path,
        // Clear selection when changing projects
        selectedItem: null
      }),

      // Selection Actions
      setSelectedItem: (item) => set({ selectedItem: item }),

      clearSelection: () => set({ selectedItem: null }),

      // Modal Actions
      openAddSnippetDialog: () => set({ isAddSnippetDialogOpen: true }),

      closeAddSnippetDialog: () => set({ isAddSnippetDialogOpen: false }),

      openAddTemplateDialog: () => set({
        isAddTemplateDialogOpen: true,
        editingTemplateId: null // Ensure we're in create mode
      }),

      closeAddTemplateDialog: () => set({ isAddTemplateDialogOpen: false }),

      openPreviewModal: (title, content) => set({
        isPreviewModalOpen: true,
        previewContent: { title, content }
      }),

      closePreviewModal: () => set({
        isPreviewModalOpen: false,
        previewContent: null
      }),

      // Template Editing Actions
      setEditingTemplateId: (id) => set({ editingTemplateId: id }),

      openEditTemplateDialog: (id) => set({
        isAddTemplateDialogOpen: true,
        editingTemplateId: id
      }),

      closeEditTemplateDialog: () => set({
        isAddTemplateDialogOpen: false,
        editingTemplateId: null
      }),

      // Navigation Helpers
      jumpToColumn: (column) => set({
        activeColumn: column,
        selectedItem: null
      }),

      cycleColumn: (direction) => {
        const currentIndex = COLUMN_ORDER.indexOf(get().activeColumn);
        let nextIndex: number;

        if (direction === 'next') {
          nextIndex = (currentIndex + 1) % COLUMN_ORDER.length;
        } else {
          nextIndex = (currentIndex - 1 + COLUMN_ORDER.length) % COLUMN_ORDER.length;
        }

        set({
          activeColumn: COLUMN_ORDER[nextIndex],
          selectedItem: null
        });
      }
    }),
    {
      name: 'scratchpad-storage', // LocalStorage key
      partialize: (state) => ({
        // Only persist these fields
        selectedProjectPath: state.selectedProjectPath,
        activeColumn: state.activeColumn
      })
    }
  )
);

// Helper Selectors
export function useActiveColumn(): ScratchPadColumn {
  return useScratchPadStore((state) => state.activeColumn);
}

export function useSearchQuery(): string {
  return useScratchPadStore((state) => state.searchQuery);
}

export function useSelectedProjectPath(): string | null {
  return useScratchPadStore((state) => state.selectedProjectPath);
}

export function useSelectedItem(): SelectedItem | null {
  return useScratchPadStore((state) => state.selectedItem);
}

export function useIsColumnActive(column: ScratchPadColumn): boolean {
  return useScratchPadStore((state) => state.activeColumn === column);
}
