/**
 * SavedSnippetsTab - Browse and manage code/text snippets
 */

import { useState, useMemo } from 'react';
import { Plus, Copy, Trash2, Maximize2, Search } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useSnippets } from '../../hooks/useScratchpad';
import { useScratchPadStore } from '../../stores/scratchpad-store';
import { cn } from '../../lib/utils';
import type { SnippetListItem } from '../../../shared/types';

export function SavedSnippetsTab() {
  const {
    selectedProjectPath,
    searchQuery,
    setSearchQuery,
    selectedItem,
    setSelectedItem,
    openAddSnippetDialog,
    openPreviewModal
  } = useScratchPadStore();

  const { snippets, isLoading, getSnippet, deleteSnippet } = useSnippets(selectedProjectPath);
  const [deletingSnippet, setDeletingSnippet] = useState<string | null>(null);

  // Filter snippets based on search query
  const filteredSnippets = useMemo(() => {
    if (!searchQuery) return snippets;

    const query = searchQuery.toLowerCase();
    return snippets.filter(
      (s) =>
        s.name.toLowerCase().includes(query) ||
        s.preview.toLowerCase().includes(query)
    );
  }, [snippets, searchQuery]);

  const handleSelect = (name: string) => {
    setSelectedItem({
      column: 'snippets',
      id: name
    });
  };

  const handleCopy = async (name: string) => {
    const snippet = await getSnippet(name);
    if (snippet) {
      await navigator.clipboard.writeText(snippet.content);
    }
  };

  const handleDelete = async (name: string) => {
    if (!confirm(`Delete snippet "${name}"?`)) return;

    setDeletingSnippet(name);
    await deleteSnippet(name);
    setDeletingSnippet(null);

    // Clear selection if deleted snippet was selected
    if (selectedItem?.column === 'snippets' && selectedItem.id === name) {
      setSelectedItem(null);
    }
  };

  const handleExpand = async (name: string) => {
    const snippet = await getSnippet(name);
    if (snippet) {
      openPreviewModal(snippet.name, snippet.content);
    }
  };

  if (!selectedProjectPath) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <Search className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <p className="text-sm text-muted-foreground">
          Select a project to view snippets
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-border">
        <Input
          id="scratchpad-search"
          placeholder="Search snippets..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-xs"
        />
        <Button variant="outline" size="sm" onClick={openAddSnippetDialog}>
          <Plus className="h-4 w-4 mr-1.5" />
          Add Snippet
        </Button>
      </div>

      {/* Snippets List */}
      <div className="flex-1 overflow-auto pt-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : filteredSnippets.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            {searchQuery ? (
              <>
                <Search className="h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground">
                  No snippets match "{searchQuery}"
                </p>
              </>
            ) : (
              <>
                <Plus className="h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground mb-1">No snippets yet</p>
                <Button variant="link" size="sm" onClick={openAddSnippetDialog}>
                  Create your first snippet
                </Button>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredSnippets.map((snippet) => (
              <SnippetCard
                key={snippet.name}
                snippet={snippet}
                isSelected={selectedItem?.column === 'snippets' && selectedItem.id === snippet.name}
                isDeleting={deletingSnippet === snippet.name}
                onSelect={() => handleSelect(snippet.name)}
                onCopy={() => handleCopy(snippet.name)}
                onDelete={() => handleDelete(snippet.name)}
                onExpand={() => handleExpand(snippet.name)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      {filteredSnippets.length > 0 && (
        <div className="pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground">
            {filteredSnippets.length} snippet{filteredSnippets.length !== 1 ? 's' : ''}
            {searchQuery && ` (filtered)`}
          </p>
        </div>
      )}
    </div>
  );
}

// Snippet Card Component
interface SnippetCardProps {
  snippet: SnippetListItem;
  isSelected: boolean;
  isDeleting: boolean;
  onSelect: () => void;
  onCopy: () => void;
  onDelete: () => void;
  onExpand: () => void;
}

function SnippetCard({
  snippet,
  isSelected,
  isDeleting,
  onSelect,
  onCopy,
  onDelete,
  onExpand
}: SnippetCardProps) {
  return (
    <div
      className={cn(
        'group relative p-3 rounded-md border border-border',
        'hover:bg-accent/50 cursor-pointer transition-colors',
        isSelected && 'bg-accent border-primary'
      )}
      onClick={onSelect}
      onDoubleClick={onExpand}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-sm truncate">{snippet.name}</h4>
          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
            {snippet.preview}
          </p>
          <p className="text-xs text-muted-foreground/70 mt-1">
            {new Date(snippet.updatedAt).toLocaleDateString()}
          </p>
        </div>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation();
              onCopy();
            }}
          >
            <Copy className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation();
              onExpand();
            }}
          >
            <Maximize2 className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive"
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
