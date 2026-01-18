/**
 * ScratchPad Keyboard Shortcuts Hook
 *
 * Handles keyboard navigation and shortcuts for ScratchPad
 */

import { useEffect } from 'react';
import { useScratchPadStore } from '../stores/scratchpad-store';
import type { ScratchPadColumn } from '../stores/scratchpad-store';

export interface ScratchPadKeyboardCallbacks {
  onCopySelected?: () => void;
  onDeleteSelected?: () => void;
  onExpandPreview?: () => void;
  onAddSnippet?: () => void;
  onAddTemplate?: () => void;
  onNavigateList?: (direction: 'up' | 'down') => void;
}

/**
 * Hook for handling keyboard shortcuts in ScratchPad
 */
export function useScratchpadKeyboard(
  callbacks: ScratchPadKeyboardCallbacks,
  enabled: boolean = true
) {
  const {
    activeColumn,
    setActiveColumn,
    cycleColumn,
    setSearchQuery,
    jumpToColumn
  } = useScratchPadStore();

  useEffect(() => {
    if (!enabled) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      // Skip if user is typing in an input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        // Allow shortcuts in search input (only when explicitly handling search)
        if (!(target.id === 'scratchpad-search' && event.key === 'Escape')) {
          return;
        }
      }

      // Skip if modifier keys are pressed (except for column jumping shortcuts)
      if (event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }

      switch (event.key) {
        case '/':
          // Focus search
          event.preventDefault();
          document.getElementById('scratchpad-search')?.focus();
          break;

        case 'Escape':
          // Clear search and blur search input
          event.preventDefault();
          setSearchQuery('');
          if (target.id === 'scratchpad-search') {
            target.blur();
          }
          break;

        case '1':
          // Jump to Notes column
          event.preventDefault();
          jumpToColumn('notes');
          break;

        case '2':
          // Jump to Snippets column
          event.preventDefault();
          jumpToColumn('snippets');
          break;

        case '3':
          // Jump to Templates column
          event.preventDefault();
          jumpToColumn('templates');
          break;

        case 'Tab':
          // Cycle columns
          event.preventDefault();
          if (event.shiftKey) {
            cycleColumn('prev');
          } else {
            cycleColumn('next');
          }
          break;

        case 'c':
          // Copy selected item
          if (callbacks.onCopySelected) {
            event.preventDefault();
            callbacks.onCopySelected();
          }
          break;

        case 'd':
          // Delete selected item (only for snippets/templates)
          if (activeColumn !== 'notes' && callbacks.onDeleteSelected) {
            event.preventDefault();
            callbacks.onDeleteSelected();
          }
          break;

        case 'Enter':
        case ' ':
          // Expand preview
          if (callbacks.onExpandPreview) {
            event.preventDefault();
            callbacks.onExpandPreview();
          }
          break;

        case 's':
          // Add snippet (only in snippets column)
          if (activeColumn === 'snippets' && callbacks.onAddSnippet) {
            event.preventDefault();
            callbacks.onAddSnippet();
          }
          break;

        case 't':
          // Add template (only in templates column)
          if (activeColumn === 'templates' && callbacks.onAddTemplate) {
            event.preventDefault();
            callbacks.onAddTemplate();
          }
          break;

        case 'j':
        case 'ArrowDown':
          // Navigate list down
          if (callbacks.onNavigateList) {
            event.preventDefault();
            callbacks.onNavigateList('down');
          }
          break;

        case 'k':
        case 'ArrowUp':
          // Navigate list up
          if (callbacks.onNavigateList) {
            event.preventDefault();
            callbacks.onNavigateList('up');
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [
    enabled,
    activeColumn,
    callbacks,
    setSearchQuery,
    jumpToColumn,
    cycleColumn
  ]);
}

/**
 * Get keyboard shortcut hint text for display
 */
export function getKeyboardShortcuts(): Record<string, string> {
  return {
    '/': 'Focus search',
    'Esc': 'Clear search',
    '1-3': 'Jump to column',
    'Tab': 'Cycle columns',
    'c': 'Copy',
    'd': 'Delete',
    'Enter/Space': 'Preview',
    's': 'Add snippet',
    't': 'Add template',
    'j/k or ↑/↓': 'Navigate'
  };
}
