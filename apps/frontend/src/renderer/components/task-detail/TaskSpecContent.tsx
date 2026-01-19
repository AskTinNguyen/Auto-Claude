import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, Loader2, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Task } from '../../../shared/types';

interface TaskSpecContentProps {
  task: Task;
}

export function TaskSpecContent({ task }: TaskSpecContentProps) {
  const { t } = useTranslation(['tasks']);
  const [content, setContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadSpecContent() {
      if (!task.specsPath) {
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Read spec.md file
        const specFilePath = `${task.specsPath}/spec.md`;
        const result = await window.electronAPI.readFile(specFilePath);

        if (!result.success || result.data === undefined) {
          throw new Error(result.error || 'Failed to read spec.md');
        }

        setContent(result.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setIsLoading(false);
      }
    }

    loadSpecContent();
  }, [task.specsPath]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin mr-2" />
        <span className="text-sm">Loading specification...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 p-4 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive">
        <AlertCircle className="h-4 w-4 flex-shrink-0" />
        <span className="text-sm">{error}</span>
      </div>
    );
  }

  if (!content) {
    return null;
  }

  return (
    <div className="space-y-3">
      <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wide flex items-center gap-1.5">
        <FileText className="h-3 w-3" />
        Specification
      </h3>
      <div className="bg-muted/30 rounded-lg px-4 py-3 border border-border/50 overflow-hidden max-w-full">
        <div
          className="prose prose-sm prose-invert max-w-none overflow-hidden prose-p:text-foreground/90 prose-p:leading-relaxed prose-headings:text-foreground prose-strong:text-foreground prose-li:text-foreground/90 prose-ul:my-2 prose-li:my-0.5 prose-a:break-all prose-pre:overflow-x-auto prose-img:max-w-full [&_img]:!max-w-full [&_img]:h-auto [&_code]:break-all [&_code]:whitespace-pre-wrap [&_*]:max-w-full"
          style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
