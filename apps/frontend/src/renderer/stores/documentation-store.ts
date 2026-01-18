import { create } from 'zustand';
import type {
  DocumentationItem,
  DocumentationType,
  DocumentationStatus,
  DocumentationLanguage,
  DocumentationTarget,
  DocumentationGenerationRequest,
  DocumentationGenerationResult
} from '../../shared/types';

interface DocumentationState {
  // Data
  items: DocumentationItem[];
  selectedItemId: string | null;
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;

  // Actions
  setItems: (items: DocumentationItem[]) => void;
  addItem: (item: DocumentationItem) => void;
  updateItem: (itemId: string, updates: Partial<DocumentationItem>) => void;
  updateItemStatus: (itemId: string, status: DocumentationStatus) => void;
  updateItemContent: (itemId: string, content: string, isEdited?: boolean) => void;
  removeItem: (itemId: string) => void;
  selectItem: (itemId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setGenerating: (generating: boolean) => void;
  setError: (error: string | null) => void;
  clearItems: () => void;

  // Selectors
  getSelectedItem: () => DocumentationItem | undefined;
  getItemsByType: (type: DocumentationType) => DocumentationItem[];
  getItemsByStatus: (status: DocumentationStatus) => DocumentationItem[];
  getItemsByFile: (filePath: string) => DocumentationItem[];
  getPendingItems: () => DocumentationItem[];
}

/**
 * Helper to find item index by id.
 * Returns -1 if not found.
 */
function findItemIndex(items: DocumentationItem[], itemId: string): number {
  return items.findIndex((item) => item.id === itemId);
}

/**
 * Helper to update a single item efficiently.
 * Uses slice instead of map to avoid iterating all items.
 */
function updateItemAtIndex(
  items: DocumentationItem[],
  index: number,
  updater: (item: DocumentationItem) => DocumentationItem
): DocumentationItem[] {
  if (index < 0 || index >= items.length) return items;

  const updatedItem = updater(items[index]);

  // If the item reference didn't change, return original array
  if (updatedItem === items[index]) {
    return items;
  }

  // Create new array with only the changed item replaced
  const newItems = [...items];
  newItems[index] = updatedItem;

  return newItems;
}

export const useDocumentationStore = create<DocumentationState>((set, get) => ({
  // Initial state
  items: [],
  selectedItemId: null,
  isLoading: false,
  isGenerating: false,
  error: null,

  // Actions
  setItems: (items) => set({ items }),

  addItem: (item) =>
    set((state) => ({
      items: [...state.items, item]
    })),

  updateItem: (itemId, updates) =>
    set((state) => {
      const index = findItemIndex(state.items, itemId);
      if (index === -1) return state;

      return {
        items: updateItemAtIndex(state.items, index, (item) => ({
          ...item,
          ...updates,
          updatedAt: new Date()
        }))
      };
    }),

  updateItemStatus: (itemId, status) =>
    set((state) => {
      const index = findItemIndex(state.items, itemId);
      if (index === -1) return state;

      return {
        items: updateItemAtIndex(state.items, index, (item) => ({
          ...item,
          status,
          updatedAt: new Date()
        }))
      };
    }),

  updateItemContent: (itemId, content, isEdited = false) =>
    set((state) => {
      const index = findItemIndex(state.items, itemId);
      if (index === -1) return state;

      return {
        items: updateItemAtIndex(state.items, index, (item) => ({
          ...item,
          ...(isEdited
            ? { editedContent: content, status: 'edited' as DocumentationStatus }
            : { generatedContent: content }),
          updatedAt: new Date()
        }))
      };
    }),

  removeItem: (itemId) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== itemId),
      selectedItemId: state.selectedItemId === itemId ? null : state.selectedItemId
    })),

  selectItem: (itemId) => set({ selectedItemId: itemId }),

  setLoading: (loading) => set({ isLoading: loading }),

  setGenerating: (generating) => set({ isGenerating: generating }),

  setError: (error) => set({ error }),

  clearItems: () =>
    set({
      items: [],
      selectedItemId: null,
      error: null
    }),

  // Selectors
  getSelectedItem: () => {
    const state = get();
    if (!state.selectedItemId) return undefined;
    return state.items.find((item) => item.id === state.selectedItemId);
  },

  getItemsByType: (type) => {
    const state = get();
    return state.items.filter((item) => item.type === type);
  },

  getItemsByStatus: (status) => {
    const state = get();
    return state.items.filter((item) => item.status === status);
  },

  getItemsByFile: (filePath) => {
    const state = get();
    return state.items.filter((item) => item.target.filePath === filePath);
  },

  getPendingItems: () => {
    const state = get();
    return state.items.filter((item) => item.status === 'pending' || item.status === 'generating');
  }
}));

// Helper functions for working with documentation items

/**
 * Create a new documentation item
 */
export function createDocumentationItem(
  type: DocumentationType,
  language: DocumentationLanguage,
  target: DocumentationTarget,
  content = ''
): DocumentationItem {
  return {
    id: `doc-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    type,
    language,
    status: 'pending',
    target,
    generatedContent: content,
    createdAt: new Date(),
    updatedAt: new Date()
  };
}

/**
 * Get the final content of a documentation item (edited or generated)
 */
export function getDocumentationContent(item: DocumentationItem): string {
  return item.editedContent ?? item.generatedContent;
}

/**
 * Check if a documentation item has been modified by the user
 */
export function isDocumentationEdited(item: DocumentationItem): boolean {
  return item.status === 'edited' || !!item.editedContent;
}

/**
 * Generate documentation via IPC
 */
export async function generateDocumentation(
  request: DocumentationGenerationRequest
): Promise<DocumentationGenerationResult> {
  const store = useDocumentationStore.getState();
  store.setGenerating(true);
  store.setError(null);

  try {
    // Create pending documentation item
    const language: DocumentationLanguage =
      request.type === 'docstring'
        ? 'python'
        : request.type === 'jsdoc'
        ? 'typescript'
        : 'markdown';

    const item = createDocumentationItem(request.type, language, {
      filePath: request.filePath,
      name: request.targetName || '',
      lineNumber: request.lineNumber
    });

    store.addItem(item);
    store.updateItemStatus(item.id, 'generating');

    // Call backend via IPC (will be implemented in IPC handlers)
    const result = await window.electron.ipc.invoke('documentation:generate', request);

    if (result.success && result.content) {
      // Update item with generated content
      store.updateItemContent(item.id, result.content, false);
      store.updateItemStatus(item.id, 'generated');
      store.selectItem(item.id);

      return { success: true, content: result.content };
    } else {
      // Mark as error
      store.updateItem(item.id, {
        status: 'error',
        error: result.error || 'Unknown error during generation'
      });
      store.setError(result.error || 'Failed to generate documentation');

      return { success: false, error: result.error };
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to generate documentation';
    store.setError(errorMsg);
    return { success: false, error: errorMsg };
  } finally {
    store.setGenerating(false);
  }
}

/**
 * Apply documentation to a file
 */
export async function applyDocumentation(itemId: string): Promise<boolean> {
  const store = useDocumentationStore.getState();
  const item = store.items.find((i) => i.id === itemId);

  if (!item) {
    store.setError('Documentation item not found');
    return false;
  }

  store.setLoading(true);
  store.setError(null);

  try {
    const content = getDocumentationContent(item);

    // Call backend via IPC to apply documentation (will be implemented in IPC handlers)
    const result = await window.electron.ipc.invoke('documentation:apply', {
      filePath: item.target.filePath,
      targetName: item.target.name,
      lineNumber: item.target.lineNumber,
      content,
      type: item.type
    });

    if (result.success) {
      store.updateItemStatus(itemId, 'applied');
      return true;
    } else {
      store.setError(result.error || 'Failed to apply documentation');
      return false;
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to apply documentation';
    store.setError(errorMsg);
    return false;
  } finally {
    store.setLoading(false);
  }
}

/**
 * Validate documentation
 */
export async function validateDocumentation(itemId: string): Promise<boolean> {
  const store = useDocumentationStore.getState();
  const item = store.items.find((i) => i.id === itemId);

  if (!item) {
    store.setError('Documentation item not found');
    return false;
  }

  try {
    const content = getDocumentationContent(item);

    // Call backend via IPC to validate (will be implemented in IPC handlers)
    const result = await window.electron.ipc.invoke('documentation:validate', {
      content,
      type: item.type,
      language: item.language
    });

    return result.valid;
  } catch (err) {
    console.error('Failed to validate documentation:', err);
    return false;
  }
}

/**
 * Load documentation items for a project
 */
export async function loadDocumentationItems(projectId: string): Promise<void> {
  const store = useDocumentationStore.getState();
  store.setLoading(true);
  store.setError(null);

  try {
    // Call backend via IPC to load items (will be implemented in IPC handlers)
    const result = await window.electron.ipc.invoke('documentation:list', { projectId });

    if (result.success && result.items) {
      store.setItems(result.items);
    } else {
      store.setError(result.error || 'Failed to load documentation items');
    }
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Failed to load documentation items';
    store.setError(errorMsg);
  } finally {
    store.setLoading(false);
  }
}
