/**
 * Documentation - Main view for documentation generation and editing
 *
 * Features:
 * - Split view with editor and preview
 * - List of documentation items
 * - Generate new documentation
 * - Edit and apply documentation
 */
import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Plus, RefreshCw, FileText, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { cn } from '../lib/utils';
import { DocumentationEditor } from './documentation/DocumentationEditor';
import { DocumentationPreview } from './documentation/DocumentationPreview';
import { useDocumentationStore, loadDocumentationItems, generateDocumentation } from '../stores/documentation-store';
import type { DocumentationItem, DocumentationType } from '../../shared/types';

interface DocumentationProps {
  projectId: string;
}

/**
 * Get display label for documentation type
 */
function getDocTypeLabel(type: DocumentationType): string {
  const labels: Record<DocumentationType, string> = {
    docstring: 'Docstring',
    jsdoc: 'JSDoc',
    readme: 'README',
    changelog: 'Changelog',
    'api-docs': 'API Docs'
  };
  return labels[type] || type;
}

/**
 * Get color for documentation type
 */
function getDocTypeColor(type: DocumentationType): string {
  const colors: Record<DocumentationType, string> = {
    docstring: 'bg-blue-500/10 text-blue-500',
    jsdoc: 'bg-green-500/10 text-green-500',
    readme: 'bg-purple-500/10 text-purple-500',
    changelog: 'bg-orange-500/10 text-orange-500',
    'api-docs': 'bg-pink-500/10 text-pink-500'
  };
  return colors[type] || 'bg-gray-500/10 text-gray-500';
}

export function Documentation({ projectId }: DocumentationProps) {
  const { t } = useTranslation(['common', 'tasks']);
  const {
    items,
    selectedItemId,
    setSelectedItemId,
    isLoading,
    error
  } = useDocumentationStore();

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // Load documentation items on mount
  useEffect(() => {
    loadDocumentationItems(projectId);
  }, [projectId]);

  // Handle item selection
  const handleSelectItem = (itemId: string) => {
    setSelectedItemId(itemId);
  };

  // Handle generate documentation
  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenerationError(null);
    try {
      // TODO: Add dialog to configure documentation generation
      // For now, generate docs for the whole project
      await generateDocumentation(projectId, {
        types: ['docstring', 'jsdoc'],
        targetPath: '.'
      });
      // Reload items after generation
      await loadDocumentationItems(projectId);
    } catch (err) {
      console.error('Failed to generate documentation:', err);
      setGenerationError(err instanceof Error ? err.message : 'Failed to generate documentation');
    } finally {
      setIsGenerating(false);
    }
  };

  // Handle refresh
  const handleRefresh = async () => {
    await loadDocumentationItems(projectId);
  };

  // Show error state
  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              {t('common:labels.error')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{error}</p>
            <Button onClick={handleRefresh} className="mt-4">
              <RefreshCw className="mr-2 h-4 w-4" />
              {t('common:buttons.retry')}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Show empty state
  if (!isLoading && items.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              {t('common:labels.noDocumentation')}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground mb-4">
              {t('common:messages.noDocumentationGenerated')}
            </p>
            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full"
            >
              {isGenerating ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  {t('common:labels.generating')}
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" />
                  {t('common:buttons.generateDocumentation')}
                </>
              )}
            </Button>
            {generationError && (
              <p className="mt-2 text-sm text-destructive">{generationError}</p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main view with list, editor, and preview
  return (
    <div className="h-full flex gap-4 p-4">
      {/* Left sidebar - Documentation items list */}
      <Card className="w-64 flex flex-col">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">Documentation</CardTitle>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={cn('h-4 w-4', isLoading && 'animate-spin')} />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-0">
          <ScrollArea className="h-full">
            <div className="space-y-1 p-2">
              {items.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleSelectItem(item.id)}
                  className={cn(
                    'w-full text-left px-3 py-2 rounded-md transition-colors',
                    'hover:bg-accent hover:text-accent-foreground',
                    selectedItemId === item.id && 'bg-accent text-accent-foreground'
                  )}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className={cn('text-xs px-2 py-0.5 rounded', getDocTypeColor(item.type))}>
                      {getDocTypeLabel(item.type)}
                    </span>
                  </div>
                  <p className="text-sm font-medium truncate">{item.targetName || 'Untitled'}</p>
                  <p className="text-xs text-muted-foreground truncate">{item.filePath}</p>
                </button>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Center - Editor */}
      <div className="flex-1 overflow-hidden">
        <DocumentationEditor className="h-full" />
      </div>

      {/* Right - Preview */}
      <div className="flex-1 overflow-hidden">
        <DocumentationPreview className="h-full" />
      </div>
    </div>
  );
}
