/**
 * TemplatesTab - Browse and manage prompt templates
 */

import { useState, useMemo } from 'react';
import { Plus, Copy, Trash2, Edit, Maximize2, Search, Lock, GitBranch } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { useTemplates } from '../../hooks/useScratchpad';
import { useScratchPadStore } from '../../stores/scratchpad-store';
import { cn } from '../../lib/utils';
import type { TemplateListItem, TemplateCategory } from '../../../shared/types';

const CATEGORY_COLORS: Record<TemplateCategory, string> = {
  development: 'bg-blue-500/10 text-blue-700 dark:text-blue-400',
  planning: 'bg-purple-500/10 text-purple-700 dark:text-purple-400',
  review: 'bg-orange-500/10 text-orange-700 dark:text-orange-400',
  custom: 'bg-gray-500/10 text-gray-700 dark:text-gray-400'
};

export function TemplatesTab() {
  const {
    selectedProjectPath,
    searchQuery,
    setSearchQuery,
    selectedItem,
    setSelectedItem,
    openAddTemplateDialog,
    openEditTemplateDialog,
    openPreviewModal
  } = useScratchPadStore();

  const { templates, isLoading, getTemplate, deleteTemplate, cloneTemplate } =
    useTemplates(selectedProjectPath);
  const [deletingTemplate, setDeletingTemplate] = useState<string | null>(null);
  const [cloningTemplate, setCloningTemplate] = useState<string | null>(null);

  // Filter templates based on search query
  const filteredTemplates = useMemo(() => {
    if (!searchQuery) return templates;

    const query = searchQuery.toLowerCase();
    return templates.filter(
      (t) =>
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.trigger.toLowerCase().includes(query)
    );
  }, [templates, searchQuery]);

  const handleSelect = (id: string) => {
    setSelectedItem({
      column: 'templates',
      id
    });
  };

  const handleCopy = async (id: string) => {
    const template = await getTemplate(id);
    if (template) {
      await navigator.clipboard.writeText(template.content);
    }
  };

  const handleEdit = (id: string) => {
    openEditTemplateDialog(id);
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete template "${name}"?`)) return;

    setDeletingTemplate(id);
    const success = await deleteTemplate(id);
    setDeletingTemplate(null);

    // Clear selection if deleted template was selected
    if (success && selectedItem?.column === 'templates' && selectedItem.id === id) {
      setSelectedItem(null);
    }
  };

  const handleClone = async (id: string, name: string) => {
    const newTrigger = prompt(`Enter trigger for cloned template (e.g., /my-review):`);
    if (!newTrigger) return;

    setCloningTemplate(id);
    await cloneTemplate(id, newTrigger, `${name} (Copy)`);
    setCloningTemplate(null);
  };

  const handleExpand = async (id: string) => {
    const template = await getTemplate(id);
    if (template) {
      openPreviewModal(`${template.name} (${template.trigger})`, template.content);
    }
  };

  if (!selectedProjectPath) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-6">
        <Search className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <p className="text-sm text-muted-foreground">
          Select a project to view templates
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-border">
        <Input
          placeholder="Search templates..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-xs"
        />
        <Button variant="outline" size="sm" onClick={openAddTemplateDialog}>
          <Plus className="h-4 w-4 mr-1.5" />
          Add Template
        </Button>
      </div>

      {/* Templates List */}
      <div className="flex-1 overflow-auto pt-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : filteredTemplates.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-center">
            {searchQuery ? (
              <>
                <Search className="h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground">
                  No templates match "{searchQuery}"
                </p>
              </>
            ) : (
              <>
                <Plus className="h-8 w-8 text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground mb-1">
                  No custom templates yet
                </p>
                <p className="text-xs text-muted-foreground mb-2">
                  System templates are available by default
                </p>
                <Button variant="link" size="sm" onClick={openAddTemplateDialog}>
                  Create your first template
                </Button>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            {filteredTemplates.map((template) => (
              <TemplateCard
                key={template.id}
                template={template}
                isSelected={selectedItem?.column === 'templates' && selectedItem.id === template.id}
                isDeleting={deletingTemplate === template.id}
                isCloning={cloningTemplate === template.id}
                onSelect={() => handleSelect(template.id)}
                onCopy={() => handleCopy(template.id)}
                onEdit={() => handleEdit(template.id)}
                onDelete={() => handleDelete(template.id, template.name)}
                onClone={() => handleClone(template.id, template.name)}
                onExpand={() => handleExpand(template.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      {filteredTemplates.length > 0 && (
        <div className="pt-3 border-t border-border">
          <p className="text-xs text-muted-foreground">
            {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''}
            {searchQuery && ` (filtered)`}
          </p>
        </div>
      )}
    </div>
  );
}

// Template Card Component
interface TemplateCardProps {
  template: TemplateListItem;
  isSelected: boolean;
  isDeleting: boolean;
  isCloning: boolean;
  onSelect: () => void;
  onCopy: () => void;
  onEdit: () => void;
  onDelete: () => void;
  onClone: () => void;
  onExpand: () => void;
}

function TemplateCard({
  template,
  isSelected,
  isDeleting,
  isCloning,
  onSelect,
  onCopy,
  onEdit,
  onDelete,
  onClone,
  onExpand
}: TemplateCardProps) {
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
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-medium text-sm truncate">{template.name}</h4>
            {template.isSystem && (
              <Lock className="h-3 w-3 text-muted-foreground flex-shrink-0" />
            )}
          </div>

          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant="secondary"
              className={cn('text-xs', CATEGORY_COLORS[template.category])}
            >
              {template.category}
            </Badge>
            <code className="text-xs text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
              {template.trigger}
            </code>
          </div>

          {template.description && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-1">
              {template.description}
            </p>
          )}
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

          {template.isSystem ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation();
                onClone();
              }}
              disabled={isCloning}
              title="Clone to create editable copy"
            >
              {isCloning ? (
                <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
              ) : (
                <GitBranch className="h-3.5 w-3.5" />
              )}
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
            >
              <Edit className="h-3.5 w-3.5" />
            </Button>
          )}

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

          {!template.isSystem && (
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
          )}
        </div>
      </div>
    </div>
  );
}
