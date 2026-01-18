/**
 * ContentPreviewModal - Full-screen preview for snippets and templates
 */

import { Copy, X } from 'lucide-react';
import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle
} from '../ui/dialog';
import { useScratchPadStore } from '../../stores/scratchpad-store';

export function ContentPreviewModal() {
  const { isPreviewModalOpen, previewContent, closePreviewModal } = useScratchPadStore();

  const handleCopy = async () => {
    if (previewContent?.content) {
      await navigator.clipboard.writeText(previewContent.content);
    }
  };

  return (
    <Dialog open={isPreviewModalOpen} onOpenChange={closePreviewModal}>
      <DialogContent className="max-w-4xl max-h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="pr-8">{previewContent?.title || 'Preview'}</DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-auto">
          <pre className="whitespace-pre-wrap font-mono text-sm bg-muted/30 p-4 rounded-md border border-border">
            {previewContent?.content || ''}
          </pre>
        </div>

        <div className="flex justify-end gap-2 pt-4 border-t border-border">
          <Button variant="outline" onClick={handleCopy}>
            <Copy className="h-4 w-4 mr-2" />
            Copy
          </Button>
          <Button variant="outline" onClick={closePreviewModal}>
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
