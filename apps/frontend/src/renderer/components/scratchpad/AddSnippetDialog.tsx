/**
 * AddSnippetDialog - Dialog for creating new snippets
 */

import { useState, useEffect } from 'react';
import { Plus, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '../ui/dialog';
import { useScratchPadStore } from '../../stores/scratchpad-store';
import { useSnippets } from '../../hooks/useScratchpad';
import { sanitizeFilename } from '../../../shared/types';

export function AddSnippetDialog() {
  const { isAddSnippetDialogOpen, closeAddSnippetDialog, selectedProjectPath } =
    useScratchPadStore();
  const { createSnippet } = useSnippets(selectedProjectPath);

  const [name, setName] = useState('');
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset form when dialog opens
  useEffect(() => {
    if (isAddSnippetDialogOpen) {
      setName('');
      setContent('');
      setError(null);
    }
  }, [isAddSnippetDialogOpen]);

  const handleSave = async () => {
    // Validation
    if (!name.trim()) {
      setError('Snippet name is required');
      return;
    }

    if (!selectedProjectPath) {
      setError('No project selected');
      return;
    }

    setIsSaving(true);
    setError(null);

    const success = await createSnippet(name.trim(), content);

    setIsSaving(false);

    if (success) {
      closeAddSnippetDialog();
    } else {
      setError('Failed to create snippet');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSave();
    }
  };

  // Generate filename preview
  const filenamePreview = name ? `${sanitizeFilename(name)}.md` : '';

  return (
    <Dialog open={isAddSnippetDialogOpen} onOpenChange={closeAddSnippetDialog}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Add New Snippet</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="snippet-name">
              Name <span className="text-destructive">*</span>
            </Label>
            <Input
              id="snippet-name"
              placeholder="my-helper-function"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={handleKeyDown}
              autoFocus
            />
            {filenamePreview && (
              <p className="text-xs text-muted-foreground">
                Will be saved as: <code className="bg-muted px-1 rounded">{filenamePreview}</code>
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="snippet-content">Content</Label>
            <Textarea
              id="snippet-content"
              placeholder="Paste your code or text snippet here..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={12}
              className="font-mono text-sm"
            />
          </div>

          {error && (
            <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
              {error}
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={closeAddSnippetDialog} disabled={isSaving}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || !name.trim()}>
            {isSaving ? (
              <>
                <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Saving...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                Add Snippet
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
