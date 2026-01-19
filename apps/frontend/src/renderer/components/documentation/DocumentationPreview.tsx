/**
 * DocumentationPreview - Component for previewing documentation with syntax highlighting
 *
 * Features:
 * - Syntax highlighting for code blocks
 * - Markdown rendering for documentation
 * - Support for multiple documentation types
 * - Copy to clipboard functionality
 * - Responsive design
 */
import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Copy, CheckCircle, FileText, Code } from 'lucide-react';
import ReactMarkdown, { Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../ui/card';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { useDocumentationStore, getDocumentationContent } from '../../stores/documentation-store';
import type { DocumentationItem, DocumentationType, DocumentationLanguage } from '../../../shared/types';

interface DocumentationPreviewProps {
  /** Optional className for the container */
  className?: string;
  /** Whether to show copy button */
  showCopyButton?: boolean;
}

/**
 * Get language identifier for syntax highlighting
 */
function getLanguageForType(type: DocumentationType, language: DocumentationLanguage): string {
  if (type === 'docstring') return 'python';
  if (type === 'jsdoc') return 'typescript';
  if (type === 'readme' || type === 'changelog') return 'markdown';
  if (type === 'api-docs') return language === 'python' ? 'python' : 'typescript';
  return 'text';
}

/**
 * Render code block with syntax highlighting (using CSS classes)
 */
function CodeBlock({ language, children }: { language?: string; children?: React.ReactNode }) {
  const codeContent = typeof children === 'string' ? children : String(children || '');

  return (
    <pre className="overflow-x-auto rounded-md bg-muted p-4 text-sm">
      <code className={cn('font-mono', language && `language-${language}`)}>
        {codeContent}
      </code>
    </pre>
  );
}

/**
 * Render inline code
 */
function InlineCode({ children }: { children?: React.ReactNode }) {
  return (
    <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-sm">
      {children}
    </code>
  );
}

export const DocumentationPreview = React.forwardRef<HTMLDivElement, DocumentationPreviewProps>(
  ({ className, showCopyButton = true }, ref) => {
    const { t } = useTranslation(['common']);
    const { getSelectedItem } = useDocumentationStore();
    const selectedItem = getSelectedItem();
    const [copySuccess, setCopySuccess] = React.useState(false);

    // Handle copy to clipboard
    const handleCopy = async () => {
      if (!selectedItem) return;

      try {
        const content = getDocumentationContent(selectedItem);
        await navigator.clipboard.writeText(content);
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      } catch (err) {
        console.error('Failed to copy to clipboard:', err);
      }
    };

    // Custom components for ReactMarkdown
    const markdownComponents: Components = React.useMemo(
      () => ({
        // Code blocks with syntax highlighting
        code({ inline, className, children, ...props }: any) {
          const match = /language-(\w+)/.exec(className || '');
          const language = match ? match[1] : undefined;

          return inline ? (
            <InlineCode>{children}</InlineCode>
          ) : (
            <CodeBlock language={language}>{children}</CodeBlock>
          );
        },
        // Headings
        h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6">{children}</h1>,
        h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 mt-5">{children}</h2>,
        h3: ({ children }) => <h3 className="text-lg font-medium mb-2 mt-4">{children}</h3>,
        // Paragraphs
        p: ({ children }) => <p className="mb-3 leading-relaxed">{children}</p>,
        // Lists
        ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="ml-4">{children}</li>,
        // Blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-border pl-4 italic text-muted-foreground mb-3">
            {children}
          </blockquote>
        ),
        // Links
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            {children}
          </a>
        ),
        // Tables
        table: ({ children }) => (
          <div className="overflow-x-auto mb-3">
            <table className="min-w-full border border-border">{children}</table>
          </div>
        ),
        th: ({ children }) => (
          <th className="border border-border bg-muted px-3 py-2 text-left font-medium">
            {children}
          </th>
        ),
        td: ({ children }) => (
          <td className="border border-border px-3 py-2">{children}</td>
        )
      }),
      []
    );

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

    const content = getDocumentationContent(selectedItem);
    const language = getLanguageForType(selectedItem.type, selectedItem.language);

    // Render plain code for non-markdown types
    const isMarkdownType = selectedItem.type === 'readme' || selectedItem.type === 'changelog';

    return (
      <div ref={ref} className={cn('h-full flex flex-col', className)}>
        <Card className="flex-1 flex flex-col">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Code className="h-5 w-5" />
              {t('common:labels.preview') || 'Preview'}
            </CardTitle>
            {showCopyButton && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCopy}
                disabled={!content}
              >
                {copySuccess ? (
                  <>
                    <CheckCircle className="h-4 w-4 mr-1.5 text-success" />
                    {t('common:labels.copied') || 'Copied!'}
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 mr-1.5" />
                    {t('common:labels.copy') || 'Copy'}
                  </>
                )}
              </Button>
            )}
          </CardHeader>

          <CardContent className="flex-1 overflow-auto">
            {content ? (
              <div className="h-full">
                {isMarkdownType ? (
                  // Render markdown with syntax highlighting
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                      {content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  // Render as code block for docstrings and JSDoc
                  <CodeBlock language={language}>{content}</CodeBlock>
                )}
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <div className="text-center space-y-2">
                  <FileText className="h-8 w-8 mx-auto opacity-50" />
                  <p className="text-sm">
                    {t('common:labels.noContent') || 'No content to preview'}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }
);

DocumentationPreview.displayName = 'DocumentationPreview';
