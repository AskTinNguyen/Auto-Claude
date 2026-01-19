/**
 * DocumentationEditor - Component for editing AI-generated documentation
 *
 * Allows users to:
 * - View AI-generated documentation
 * - Edit documentation content
 * - Save changes
 * - Apply documentation to files
 * - Discard changes
 */
import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Save, X, Check, FileText, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../ui/card';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { useDocumentationStore, getDocumentationContent, isDocumentationEdited } from '../../stores/documentation-store';
import type { DocumentationItem, DocumentationType, DocumentationLanguage, DocumentationStatus } from '../../../shared/types';

interface DocumentationEditorProps {
  /** Optional className for the container */
  className?: string;
  /** Optional callback when documentation is applied */
  onApplied?: (itemId: string) => void;
  /** Optional callback when changes are discarded */
  onDiscarded?: (itemId: string) => void;
  /** Whether the editor is disabled */
  disabled?: boolean;
}

/**
 * Get display label for documentation type
 */
function getDocTypeLabel(type: DocumentationType): string {
  const labels: Record<DocumentationType, string> = {
    docstring: 'Python Docstring',
    jsdoc: 'JSDoc Comment',
    readme: 'README Section',
    changelog: 'Changelog Entry',
    'api-docs': 'API Documentation'
  };
  return labels[type] || type;
}

/**
 * Get display label for language
 */
function getLanguageLabel(language: DocumentationLanguage): string {
  const labels: Record<DocumentationLanguage, string> = {
    python: 'Python',
    typescript: 'TypeScript',
    javascript: 'JavaScript',
    markdown: 'Markdown'
  };
  return labels[language] || language;
}

/**
 * Get display label and color for status
 */
function getStatusDisplay(status: DocumentationStatus): { label: string; color: string } {
  const displays: Record<DocumentationStatus, { label: string; color: string }> = {
    pending: { label: 'Pending', color: 'text-muted-foreground' },
    generating: { label: 'Generating...', color: 'text-info' },
    generated: { label: 'Generated', color: 'text-success' },
    edited: { label: 'Edited', color: 'text-warning' },
    applied: { label: 'Applied', color: 'text-success' },
    error: { label: 'Error', color: 'text-destructive' }
  };
  return displays[status] || { label: status, color: 'text-muted-foreground' };
}

export const DocumentationEditor = React.forwardRef<HTMLDivElement, DocumentationEditorProps>(
  ({ className, onApplied, onDiscarded, disabled = false }, ref) => {
    const { t } = useTranslation(['common', 'tasks']);
    const {
      getSelectedItem,
      updateItemContent,
      removeItem,
      isLoading,
      error: storeError
    } = useDocumentationStore();

    const selectedItem = getSelectedItem();
    const [localContent, setLocalContent] = React.useState<string>('');
    const [hasLocalChanges, setHasLocalChanges] = React.useState(false);
    const [applyError, setApplyError] = React.useState<string | null>(null);

    // Sync local content when selected item changes
    React.useEffect(() => {
      if (selectedItem) {
        const content = getDocumentationContent(selectedItem);
        setLocalContent(content);
        setHasLocalChanges(false);
        setApplyError(null);
      } else {
        setLocalContent('');
        setHasLocalChanges(false);
        setApplyError(null);
      }
    }, [selectedItem?.id, selectedItem?.generatedContent, selectedItem?.editedContent]);

    // Handle content change
    const handleContentChange = (value: string) => {
      setLocalContent(value);
      setHasLocalChanges(true);
    };

    // Handle save (update store with edited content)
    const handleSave = () => {
      if (!selectedItem) return;

      updateItemContent(selectedItem.id, localContent, true);
      setHasLocalChanges(false);
    };

    // Handle apply (save to file via IPC)
    const handleApply = async () => {
      if (!selectedItem) return;

      setApplyError(null);

      try {
        // First save local changes
        if (hasLocalChanges) {
          handleSave();
        }

        // Apply to file via IPC
        const result = await window.electron.ipc.invoke('documentation:apply', {
          filePath: selectedItem.target.filePath,
          targetName: selectedItem.target.name,
          lineNumber: selectedItem.target.lineNumber,
          content: localContent,
          type: selectedItem.type
        });

        if (result.success) {
          onApplied?.(selectedItem.id);
        } else {
          setApplyError(result.error || 'Failed to apply documentation');
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Failed to apply documentation';
        setApplyError(errorMsg);
      }
    };

    // Handle discard
    const handleDiscard = () => {
      if (!selectedItem) return;

      if (window.confirm(t('common:labels.confirmDiscard') || 'Are you sure you want to discard this documentation?')) {
        removeItem(selectedItem.id);
        onDiscarded?.(selectedItem.id);
      }
    };

    // Handle reset to generated
    const handleReset = () => {
      if (!selectedItem) return;
      setLocalContent(selectedItem.generatedContent);
      setHasLocalChanges(true);
    };

    // No item selected
    if (!selectedItem) {
      return (
        <div
          ref={ref}
          className={cn('flex items-center justify-center h-full text-muted-foreground', className)}
        >
          <div className="text-center space-y-2">
            <FileText className="h-12 w-12 mx-auto opacity-50" />
            <p>{t('common:labels.noSelection') || 'No documentation selected'}</p>
          </div>
        </div>
      );
    }

    const statusDisplay = getStatusDisplay(selectedItem.status);
    const isEdited = isDocumentationEdited(selectedItem);
    const canApply = selectedItem.status !== 'pending' && selectedItem.status !== 'generating';

    return (
      <div ref={ref} className={cn('h-full flex flex-col', className)}>
        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-lg truncate">
                  {getDocTypeLabel(selectedItem.type)}
                </CardTitle>
                <CardDescription className="truncate mt-1">
                  {selectedItem.target.filePath}
                  {selectedItem.target.name && ` • ${selectedItem.target.name}`}
                  {selectedItem.target.lineNumber && ` (L${selectedItem.target.lineNumber})`}
                </CardDescription>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-muted-foreground">
                  {getLanguageLabel(selectedItem.language)}
                </span>
                <span className={cn('text-xs font-medium', statusDisplay.color)}>
                  {statusDisplay.label}
                </span>
              </div>
            </div>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col space-y-4 overflow-hidden">
            {/* Error Display */}
            {(storeError || applyError || selectedItem.error) && (
              <div className="flex items-start gap-2 rounded-lg bg-destructive/10 border border-destructive/30 p-3 text-sm text-destructive" role="alert">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
                <span>{applyError || storeError || selectedItem.error}</span>
              </div>
            )}

            {/* Content Editor */}
            <div className="flex-1 flex flex-col space-y-2 overflow-hidden">
              <div className="flex items-center justify-between">
                <Label htmlFor="doc-content" className="text-sm font-medium">
                  {t('common:labels.content') || 'Content'}
                  {isEdited && (
                    <span className="ml-2 text-xs text-warning font-normal">
                      ({t('common:labels.modified') || 'Modified'})
                    </span>
                  )}
                </Label>
                {isEdited && selectedItem.generatedContent && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={handleReset}
                    disabled={disabled || isLoading}
                    className="h-auto py-1 px-2 text-xs"
                  >
                    {t('common:labels.resetToGenerated') || 'Reset to generated'}
                  </Button>
                )}
              </div>
              <Textarea
                id="doc-content"
                value={localContent}
                onChange={(e) => handleContentChange(e.target.value)}
                disabled={disabled || isLoading || selectedItem.status === 'generating'}
                className="flex-1 font-mono text-xs resize-none"
                placeholder={t('common:labels.enterContent') || 'Enter documentation content...'}
              />
            </div>
          </CardContent>

          <CardFooter className="flex items-center justify-between gap-3 border-t pt-4">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDiscard}
                disabled={disabled || isLoading}
              >
                <X className="h-4 w-4 mr-1.5" />
                {t('common:labels.discard') || 'Discard'}
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleSave}
                disabled={disabled || isLoading || !hasLocalChanges}
              >
                <Save className="h-4 w-4 mr-1.5" />
                {t('common:labels.save') || 'Save'}
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleApply}
                disabled={disabled || isLoading || !canApply}
              >
                <Check className="h-4 w-4 mr-1.5" />
                {t('common:labels.apply') || 'Apply'}
              </Button>
            </div>
          </CardFooter>
        </Card>
      </div>
    );
  }
);

DocumentationEditor.displayName = 'DocumentationEditor';
