/**
 * ScratchPad Data Hooks
 *
 * Custom hooks for interacting with Notes, Snippets, and Templates
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  SnippetListItem,
  Snippet,
  TemplateListItem,
  FileTemplate,
  TemplateCategory
} from '../../shared/types';

// ============================================
// Notes Hooks
// ============================================

export function useNotes() {
  const [notes, setNotes] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadNotes = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    const result = await window.electronAPI.loadNotes();

    if (result.success) {
      setNotes(result.data || '');
    } else {
      setError(result.error || 'Failed to load notes');
    }

    setIsLoading(false);
  }, []);

  const saveNotes = useCallback(async (content: string) => {
    const result = await window.electronAPI.saveNotes(content);

    if (!result.success) {
      setError(result.error || 'Failed to save notes');
      return false;
    }

    setNotes(content);
    setError(null);
    return true;
  }, []);

  useEffect(() => {
    loadNotes();
  }, [loadNotes]);

  return {
    notes,
    isLoading,
    error,
    saveNotes,
    reload: loadNotes
  };
}

// ============================================
// Snippets Hooks
// ============================================

export function useSnippets(projectPath: string | null) {
  const [snippets, setSnippets] = useState<SnippetListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSnippets = useCallback(async () => {
    if (!projectPath) {
      setSnippets([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    const result = await window.electronAPI.listSnippets(projectPath);

    if (result.success) {
      setSnippets(result.data || []);
    } else {
      setError(result.error || 'Failed to load snippets');
    }

    setIsLoading(false);
  }, [projectPath]);

  const createSnippet = useCallback(
    async (name: string, content: string) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.createSnippet(projectPath, name, content);

      if (!result.success) {
        setError(result.error || 'Failed to create snippet');
        return false;
      }

      await loadSnippets();
      setError(null);
      return true;
    },
    [projectPath, loadSnippets]
  );

  const getSnippet = useCallback(
    async (name: string): Promise<Snippet | null> => {
      if (!projectPath) return null;

      const result = await window.electronAPI.getSnippet(projectPath, name);

      if (!result.success) {
        setError(result.error || 'Failed to get snippet');
        return null;
      }

      return result.data || null;
    },
    [projectPath]
  );

  const deleteSnippet = useCallback(
    async (name: string) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.deleteSnippet(projectPath, name);

      if (!result.success) {
        setError(result.error || 'Failed to delete snippet');
        return false;
      }

      await loadSnippets();
      setError(null);
      return true;
    },
    [projectPath, loadSnippets]
  );

  useEffect(() => {
    loadSnippets();
  }, [loadSnippets]);

  return {
    snippets,
    isLoading,
    error,
    createSnippet,
    getSnippet,
    deleteSnippet,
    reload: loadSnippets
  };
}

// ============================================
// Templates Hooks
// ============================================

export function useTemplates(projectPath: string | null) {
  const [templates, setTemplates] = useState<TemplateListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTemplates = useCallback(async () => {
    if (!projectPath) {
      setTemplates([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    const result = await window.electronAPI.listTemplates(projectPath);

    if (result.success) {
      setTemplates(result.data || []);
    } else {
      setError(result.error || 'Failed to load templates');
    }

    setIsLoading(false);
  }, [projectPath]);

  const createTemplate = useCallback(
    async (
      name: string,
      description: string,
      category: TemplateCategory,
      trigger: string,
      content: string
    ) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.createTemplate(
        projectPath,
        name,
        description,
        category,
        trigger,
        content
      );

      if (!result.success) {
        setError(result.error || 'Failed to create template');
        return false;
      }

      await loadTemplates();
      setError(null);
      return true;
    },
    [projectPath, loadTemplates]
  );

  const updateTemplate = useCallback(
    async (
      id: string,
      name: string,
      description: string,
      category: TemplateCategory,
      trigger: string,
      content: string
    ) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.updateTemplate(
        projectPath,
        id,
        name,
        description,
        category,
        trigger,
        content
      );

      if (!result.success) {
        setError(result.error || 'Failed to update template');
        return false;
      }

      await loadTemplates();
      setError(null);
      return true;
    },
    [projectPath, loadTemplates]
  );

  const deleteTemplate = useCallback(
    async (id: string) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.deleteTemplate(projectPath, id);

      if (!result.success) {
        setError(result.error || 'Failed to delete template');
        return false;
      }

      await loadTemplates();
      setError(null);
      return true;
    },
    [projectPath, loadTemplates]
  );

  const cloneTemplate = useCallback(
    async (sourceId: string, newTrigger: string, newName?: string, newDescription?: string) => {
      if (!projectPath) {
        setError('No project selected');
        return false;
      }

      const result = await window.electronAPI.cloneTemplate(
        projectPath,
        sourceId,
        newTrigger,
        newName,
        newDescription
      );

      if (!result.success) {
        setError(result.error || 'Failed to clone template');
        return false;
      }

      await loadTemplates();
      setError(null);
      return true;
    },
    [projectPath, loadTemplates]
  );

  const getTemplate = useCallback(
    async (id: string): Promise<FileTemplate | null> => {
      if (!projectPath) return null;

      const result = await window.electronAPI.getTemplate(projectPath, id);

      if (!result.success) {
        setError(result.error || 'Failed to get template');
        return null;
      }

      return result.data || null;
    },
    [projectPath]
  );

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  return {
    templates,
    isLoading,
    error,
    createTemplate,
    updateTemplate,
    deleteTemplate,
    cloneTemplate,
    getTemplate,
    reload: loadTemplates
  };
}
