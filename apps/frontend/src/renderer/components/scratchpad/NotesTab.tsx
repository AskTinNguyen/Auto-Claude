/**
 * NotesTab - Markdown notes editor with auto-save
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Copy, Download, Save, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { useNotes } from '../../hooks/useScratchpad';
import { cn } from '../../lib/utils';

// Debounce utility
function useDebouncedCallback<T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback(
    ((...args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    }) as T,
    [callback, delay]
  );
}

export function NotesTab() {
  const { notes, isLoading, error, saveNotes } = useNotes();
  const [localContent, setLocalContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');

  // Initialize local content when notes load
  useEffect(() => {
    setLocalContent(notes);
  }, [notes]);

  // Auto-save handler (debounced by 1 second)
  const handleAutoSave = useCallback(
    async (content: string) => {
      if (content === notes) return; // No changes

      setIsSaving(true);
      setSaveStatus('saving');

      const success = await saveNotes(content);

      setIsSaving(false);
      setSaveStatus(success ? 'saved' : 'idle');

      // Clear saved status after 2 seconds
      if (success) {
        setTimeout(() => setSaveStatus('idle'), 2000);
      }
    },
    [saveNotes, notes]
  );

  const debouncedAutoSave = useDebouncedCallback(handleAutoSave, 1000);

  // Handle content change
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    setLocalContent(newContent);
    debouncedAutoSave(newContent);
  };

  // Manual save
  const handleManualSave = async () => {
    await handleAutoSave(localContent);
  };

  // Copy to clipboard
  const handleCopy = async () => {
    await navigator.clipboard.writeText(localContent);
  };

  // Download as file
  const handleDownload = () => {
    const blob = new Blob([localContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scratchpad-${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Calculate character and line counts
  const charCount = localContent.length;
  const lineCount = localContent.split('\n').length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-2 pb-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-1.5" />
            Copy
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-4 w-4 mr-1.5" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleManualSave}
            disabled={isSaving || localContent === notes}
          >
            <Save className="h-4 w-4 mr-1.5" />
            Save
          </Button>
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {saveStatus === 'saving' && (
            <div className="flex items-center gap-1.5">
              <div className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
              <span>Saving...</span>
            </div>
          )}
          {saveStatus === 'saved' && (
            <div className="flex items-center gap-1.5 text-green-600 dark:text-green-500">
              <CheckCircle2 className="h-3 w-3" />
              <span>Saved</span>
            </div>
          )}
          <span>
            {charCount.toLocaleString()} chars, {lineCount.toLocaleString()} lines
          </span>
        </div>
      </div>

      {/* Editor */}
      <div className="flex-1 pt-3">
        <Textarea
          value={localContent}
          onChange={handleChange}
          placeholder="Start typing your notes...&#10;&#10;Supports Markdown formatting.&#10;Auto-saves after 1 second of inactivity."
          className={cn(
            'h-full resize-none font-mono text-sm',
            'focus-visible:ring-0 focus-visible:ring-offset-0',
            'border-0'
          )}
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="mt-2 text-sm text-destructive bg-destructive/10 px-3 py-2 rounded-md">
          {error}
        </div>
      )}
    </div>
  );
}
