/**
 * AddTemplateDialog - Dialog for creating/editing templates
 */

import { useState, useEffect } from 'react';
import { Plus, Save, X, FileCode } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '../ui/dialog';
import { useScratchPadStore } from '../../stores/scratchpad-store';
import { useTemplates } from '../../hooks/useScratchpad';
import { isValidTrigger, type TemplateCategory } from '../../../shared/types';

const CATEGORIES: { value: TemplateCategory; label: string }[] = [
  { value: 'development', label: 'Development' },
  { value: 'planning', label: 'Planning' },
  { value: 'review', label: 'Review' },
  { value: 'custom', label: 'Custom' }
];

export function AddTemplateDialog() {
  const {
    isAddTemplateDialogOpen,
    closeAddTemplateDialog,
    selectedProjectPath,
    editingTemplateId
  } = useScratchPadStore();
  const { createTemplate, updateTemplate, getTemplate } = useTemplates(selectedProjectPath);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState<TemplateCategory>('custom');
  const [trigger, setTrigger] = useState('');
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEditMode = !!editingTemplateId;

  // Load template data when editing
  useEffect(() => {
    if (isAddTemplateDialogOpen && editingTemplateId) {
      setIsLoading(true);
      getTemplate(editingTemplateId).then((template) => {
        if (template) {
          setName(template.name);
          setDescription(template.description);
          setCategory(template.category);
          setTrigger(template.trigger);
          setContent(template.content);
        }
        setIsLoading(false);
      });
    } else if (isAddTemplateDialogOpen) {
      // Reset form for create mode
      setName('');
      setDescription('');
      setCategory('custom');
      setTrigger('');
      setContent('');
      setError(null);
    }
  }, [isAddTemplateDialogOpen, editingTemplateId, getTemplate]);

  const handleSave = async () => {
    // Validation
    if (!name.trim()) {
      setError('Template name is required');
      return;
    }

    if (!trigger.trim()) {
      setError('Trigger is required');
      return;
    }

    if (!isValidTrigger(trigger)) {
      setError('Invalid trigger format. Use /[a-z0-9-]+ (e.g., /code-review)');
      return;
    }

    if (!selectedProjectPath) {
      setError('No project selected');
      return;
    }

    setIsSaving(true);
    setError(null);

    let success: boolean;

    if (isEditMode && editingTemplateId) {
      success = await updateTemplate(
        editingTemplateId,
        name.trim(),
        description.trim(),
        category,
        trigger.trim(),
        content
      );
    } else {
      success = await createTemplate(
        name.trim(),
        description.trim(),
        category,
        trigger.trim(),
        content
      );
    }

    setIsSaving(false);

    if (success) {
      closeAddTemplateDialog();
    } else {
      setError(`Failed to ${isEditMode ? 'update' : 'create'} template`);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !isSaving) {
      handleSave();
    }
  };

  const insertPlaceholder = () => {
    const textarea = document.getElementById('template-content') as HTMLTextAreaElement;
    if (textarea) {
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const newContent =
        content.substring(0, start) + '{{input}}' + content.substring(end);
      setContent(newContent);

      // Set cursor position after inserted text
      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 9;
        textarea.focus();
      }, 0);
    }
  };

  return (
    <Dialog open={isAddTemplateDialogOpen} onOpenChange={closeAddTemplateDialog}>
      <DialogContent className="max-w-3xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>{isEditMode ? 'Edit Template' : 'Add New Template'}</DialogTitle>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          </div>
        ) : (
          <div className="space-y-4 py-4 flex-1 overflow-auto">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="template-name">
                  Name <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="template-name"
                  placeholder="Code Review"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoFocus={!isEditMode}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="template-trigger">
                  Trigger <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="template-trigger"
                  placeholder="/code-review"
                  value={trigger}
                  onChange={(e) => setTrigger(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="template-description">Description</Label>
              <Input
                id="template-description"
                placeholder="Review code for quality and security"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                onKeyDown={handleKeyDown}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="template-category">Category</Label>
              <Select value={category} onValueChange={(v) => setCategory(v as TemplateCategory)}>
                <SelectTrigger id="template-category">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>
                      {cat.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="template-content">Content</Label>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={insertPlaceholder}
                  className="h-7 text-xs"
                >
                  <FileCode className="h-3 w-3 mr-1" />
                  Insert {'{{input}}'}
                </Button>
              </div>
              <Textarea
                id="template-content"
                placeholder="Review the following code:&#10;&#10;{{input}}&#10;&#10;Provide specific feedback..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={12}
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Use <code className="bg-muted px-1 rounded">{'{{input}}'}</code> as a placeholder
                for user input
              </p>
            </div>

            {error && (
              <div className="text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
                {error}
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={closeAddTemplateDialog} disabled={isSaving}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving || isLoading || !name.trim() || !trigger.trim()}>
            {isSaving ? (
              <>
                <div className="h-4 w-4 mr-2 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Saving...
              </>
            ) : isEditMode ? (
              <>
                <Save className="h-4 w-4 mr-2" />
                Update Template
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                Add Template
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
