import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  GitMerge,
  Loader2,
  CheckCircle2,
  XCircle,
  FileText,
  AlertTriangle,
  Sparkles,
  GitBranch,
  Clock
} from 'lucide-react';
import { Badge } from '../ui/badge';
import { ScrollArea } from '../ui/scroll-area';
import { cn } from '../../lib/utils';
import type { Task, MergeHistoryRecord } from '../../../shared/types';

interface MergeHistoryProps {
  task: Task;
}

// Helper to format timestamp
function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return timestamp;
  }
}

// Helper to format duration
function formatDuration(seconds: number | null | undefined, t: (key: string) => string): string {
  if (!seconds) return t('mergeHistory.notAvailable');
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes}m ${remainingSeconds}s`;
}

// Helper to get strategy badge color
function getStrategyColor(strategy: MergeHistoryRecord['merge_strategy']): string {
  switch (strategy) {
    case 'fast-forward':
      return 'text-green-500 bg-green-500/10 border-green-500/30';
    case '3-way':
      return 'text-blue-500 bg-blue-500/10 border-blue-500/30';
    case 'ai-assisted':
      return 'text-purple-500 bg-purple-500/10 border-purple-500/30';
    case 'manual':
      return 'text-amber-500 bg-amber-500/10 border-amber-500/30';
    default:
      return 'text-muted-foreground bg-muted border-border';
  }
}

export function MergeHistory({ task }: MergeHistoryProps) {
  const { t } = useTranslation(['tasks']);
  const [mergeHistory, setMergeHistory] = useState<MergeHistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load merge history for this task
  const loadMergeHistory = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await window.electronAPI.getMergeHistory(task.specId);
      if (result.success && result.data) {
        setMergeHistory(result.data);
      } else {
        throw new Error(result.error || t('mergeHistory.errorLoading'));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t('mergeHistory.unknownError'));
    } finally {
      setIsLoading(false);
    }
  }, [task.specId, t]);

  // Load on mount
  useEffect(() => {
    loadMergeHistory();
  }, [loadMergeHistory]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <AlertTriangle className="h-8 w-8 text-warning mb-2" />
        <p className="text-sm text-muted-foreground">{error}</p>
      </div>
    );
  }

  // Empty state
  if (mergeHistory.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-8 text-center">
        <GitMerge className="h-8 w-8 text-muted-foreground/50 mb-2" />
        <p className="text-sm text-muted-foreground">
          {t('mergeHistory.noMerges', 'No merge history yet')}
        </p>
        <p className="text-xs text-muted-foreground/70 mt-1">
          {t('mergeHistory.noMergesHint', 'Merge events will appear here after merging this task')}
        </p>
      </div>
    );
  }

  // Display merge history
  return (
    <ScrollArea className="h-full">
      <div className="p-4 space-y-3">
        {mergeHistory.map((record) => (
          <div
            key={record.merge_id}
            className={cn(
              'border rounded-lg p-4 space-y-3',
              record.success
                ? 'bg-card border-border'
                : 'bg-destructive/5 border-destructive/30'
            )}
          >
            {/* Header: Status, Timestamp, Duration */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                {record.success ? (
                  <CheckCircle2 className="h-5 w-5 text-success flex-shrink-0" />
                ) : (
                  <XCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                )}
                <div className="flex flex-col">
                  <span className="text-sm font-medium">
                    {record.success
                      ? t('mergeHistory.mergeSuccessful', 'Merge Successful')
                      : t('mergeHistory.mergeFailed', 'Merge Failed')}
                  </span>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {formatTimestamp(record.timestamp)}
                  </div>
                </div>
              </div>

              {/* Duration badge */}
              {record.duration_seconds && (
                <Badge variant="outline" className="text-xs">
                  {formatDuration(record.duration_seconds, t)}
                </Badge>
              )}
            </div>

            {/* Error message if failed */}
            {!record.success && record.error_message && (
              <div className="flex items-start gap-2 text-xs text-destructive">
                <AlertTriangle className="h-3 w-3 flex-shrink-0 mt-0.5" />
                <span>{record.error_message}</span>
              </div>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Files Changed */}
              <div className="flex items-center gap-2 text-sm">
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">
                  {t('mergeHistory.filesChanged', 'Files:')}
                </span>
                <span className="font-medium">{record.resolved_files.length}</span>
              </div>

              {/* Conflicts Resolved */}
              <div className="flex items-center gap-2 text-sm">
                <AlertTriangle className="h-4 w-4 text-warning" />
                <span className="text-muted-foreground">
                  {t('mergeHistory.conflictsResolved', 'Conflicts:')}
                </span>
                <span className="font-medium">{record.conflicts_resolved}</span>
              </div>

              {/* AI Assisted */}
              <div className="flex items-center gap-2 text-sm">
                <Sparkles className="h-4 w-4 text-purple-500" />
                <span className="text-muted-foreground">
                  {t('mergeHistory.aiAssisted', 'AI Assisted:')}
                </span>
                <span className="font-medium">{record.ai_assisted_count}</span>
              </div>

              {/* Auto Merged */}
              <div className="flex items-center gap-2 text-sm">
                <GitBranch className="h-4 w-4 text-info" />
                <span className="text-muted-foreground">
                  {t('mergeHistory.autoMerged', 'Auto Merged:')}
                </span>
                <span className="font-medium">{record.auto_merged_count}</span>
              </div>

              {/* Git Conflicts */}
              {record.git_conflicts > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <XCircle className="h-4 w-4 text-destructive" />
                  <span className="text-muted-foreground">
                    {t('mergeHistory.gitConflicts', 'Git Conflicts:')}
                  </span>
                  <span className="font-medium">{record.git_conflicts}</span>
                </div>
              )}
            </div>

            {/* Merge Strategy Badge */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {t('mergeHistory.strategy', 'Strategy:')}
              </span>
              <Badge
                variant="outline"
                className={cn('text-xs', getStrategyColor(record.merge_strategy))}
              >
                {t(`mergeHistory.strategies.${record.merge_strategy}`, record.merge_strategy)}
              </Badge>
            </div>

            {/* File List (if not too many) */}
            {record.resolved_files.length > 0 && record.resolved_files.length <= 10 && (
              <details className="text-xs">
                <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                  {t('mergeHistory.viewFiles', 'View affected files')} ({record.resolved_files.length})
                </summary>
                <ul className="mt-2 space-y-1 ml-4">
                  {record.resolved_files.map((file, idx) => (
                    <li key={idx} className="text-muted-foreground font-mono truncate">
                      {file}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
