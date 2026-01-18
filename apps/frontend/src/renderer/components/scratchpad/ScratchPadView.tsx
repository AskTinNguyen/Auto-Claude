/**
 * ScratchPadView - Main layout for Notes, Snippets, and Templates
 *
 * Three-column layout with unified search, project selector, and keyboard shortcuts
 */

import { useEffect } from 'react';
import { FileText, Code2, FileCode2, Command } from 'lucide-react';
import { cn } from '../../lib/utils';
import { useScratchPadStore } from '../../stores/scratchpad-store';
import { useScratchpadKeyboard, getKeyboardShortcuts } from '../../hooks/useScratchpadKeyboard';
import { NotesTab } from './NotesTab';
import { SavedSnippetsTab } from './SavedSnippetsTab';
import { TemplatesTab } from './TemplatesTab';
import { ContentPreviewModal } from './ContentPreviewModal';
import { AddSnippetDialog } from './AddSnippetDialog';
import { AddTemplateDialog } from './AddTemplateDialog';
import { useProjectStore } from '../../stores/project-store';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select';

export function ScratchPadView() {
  const {
    activeColumn,
    setActiveColumn,
    selectedProjectPath,
    setSelectedProjectPath,
    openAddSnippetDialog,
    openAddTemplateDialog
  } = useScratchPadStore();

  const { projects } = useProjectStore();

  // Set default project if not set
  useEffect(() => {
    if (!selectedProjectPath && projects.length > 0) {
      setSelectedProjectPath(projects[0].path);
    }
  }, [selectedProjectPath, projects, setSelectedProjectPath]);

  // Keyboard shortcuts
  useScratchpadKeyboard(
    {
      onAddSnippet: openAddSnippetDialog,
      onAddTemplate: openAddTemplateDialog
    },
    true
  );

  const shortcuts = getKeyboardShortcuts();

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-2xl font-semibold">ScratchPad</h1>

          {/* Project Selector */}
          {projects.length > 0 && (
            <Select
              value={selectedProjectPath || undefined}
              onValueChange={setSelectedProjectPath}
            >
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select project..." />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.path}>
                    {project.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Column Tabs */}
        <div className="flex items-center gap-1">
          <ColumnTab
            icon={FileText}
            label="Notes"
            column="notes"
            active={activeColumn === 'notes'}
            accentColor="text-emerald-500"
            onClick={() => setActiveColumn('notes')}
          />
          <ColumnTab
            icon={Code2}
            label="Snippets"
            column="snippets"
            active={activeColumn === 'snippets'}
            accentColor="text-cyan-500"
            onClick={() => setActiveColumn('snippets')}
          />
          <ColumnTab
            icon={FileCode2}
            label="Templates"
            column="templates"
            active={activeColumn === 'templates'}
            accentColor="text-yellow-500"
            onClick={() => setActiveColumn('templates')}
          />
        </div>
      </div>

      {/* Main Content - Three Columns */}
      <div className="flex-1 grid grid-cols-3 gap-px bg-border overflow-hidden">
        {/* Notes Column */}
        <div
          className={cn(
            'bg-background p-6 overflow-hidden',
            activeColumn !== 'notes' && 'opacity-50'
          )}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="h-1 w-1 rounded-full bg-emerald-500" />
            <h2 className="text-sm font-semibold text-emerald-500">Notes</h2>
            <kbd className="ml-auto px-1.5 py-0.5 text-xs bg-muted rounded border border-border">
              1
            </kbd>
          </div>
          <div className="h-[calc(100%-3rem)]">
            <NotesTab />
          </div>
        </div>

        {/* Snippets Column */}
        <div
          className={cn(
            'bg-background p-6 overflow-hidden',
            activeColumn !== 'snippets' && 'opacity-50'
          )}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="h-1 w-1 rounded-full bg-cyan-500" />
            <h2 className="text-sm font-semibold text-cyan-500">Snippets</h2>
            <kbd className="ml-auto px-1.5 py-0.5 text-xs bg-muted rounded border border-border">
              2
            </kbd>
          </div>
          <div className="h-[calc(100%-3rem)]">
            <SavedSnippetsTab />
          </div>
        </div>

        {/* Templates Column */}
        <div
          className={cn(
            'bg-background p-6 overflow-hidden',
            activeColumn !== 'templates' && 'opacity-50'
          )}
        >
          <div className="flex items-center gap-2 mb-4">
            <div className="h-1 w-1 rounded-full bg-yellow-500" />
            <h2 className="text-sm font-semibold text-yellow-500">Templates</h2>
            <kbd className="ml-auto px-1.5 py-0.5 text-xs bg-muted rounded border border-border">
              3
            </kbd>
          </div>
          <div className="h-[calc(100%-3rem)]">
            <TemplatesTab />
          </div>
        </div>
      </div>

      {/* Footer - Keyboard Shortcuts */}
      <div className="border-t border-border px-6 py-2 bg-muted/30">
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1">
            <Command className="h-3 w-3" />
            <span className="font-medium">Shortcuts:</span>
          </div>
          {Object.entries(shortcuts)
            .slice(0, 6)
            .map(([key, description]) => (
              <div key={key} className="flex items-center gap-1">
                <kbd className="px-1 py-0.5 bg-background rounded border border-border text-[10px]">
                  {key}
                </kbd>
                <span>{description}</span>
              </div>
            ))}
        </div>
      </div>

      {/* Modals */}
      <ContentPreviewModal />
      <AddSnippetDialog />
      <AddTemplateDialog />
    </div>
  );
}

// Column Tab Component
interface ColumnTabProps {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  column: 'notes' | 'snippets' | 'templates';
  active: boolean;
  accentColor: string;
  onClick: () => void;
}

function ColumnTab({ icon: Icon, label, active, accentColor, onClick }: ColumnTabProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-2 px-4 py-2 rounded-md transition-colors',
        'hover:bg-accent',
        active && 'bg-accent'
      )}
    >
      <Icon className={cn('h-4 w-4', active ? accentColor : 'text-muted-foreground')} />
      <span className={cn('text-sm font-medium', active ? 'text-foreground' : 'text-muted-foreground')}>
        {label}
      </span>
    </button>
  );
}
