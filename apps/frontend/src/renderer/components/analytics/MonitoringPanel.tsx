import { useTranslation } from 'react-i18next';
import { useEffect } from 'react';
import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Activity, DollarSign, RefreshCw, TrendingUp } from 'lucide-react';
import { useMonitoringStore, type HeartbeatStatus } from '../../stores/monitoring-store';
import { useTaskStore } from '../../stores/task-store';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

interface MonitoringPanelProps {
  projectId: string;
  className?: string;
}

/**
 * Monitoring Panel component
 * - Display cost tracking (tokens, costs)
 * - Show heartbeat status
 * - List recent events
 * - Cost trends chart
 */
export function MonitoringPanel({ projectId, className }: MonitoringPanelProps) {
  const { t } = useTranslation(['analytics', 'common']);
  const {
    heartbeatStatus,
    costMetrics,
    recentEvents,
    costTrends,
    isLoading,
    loadMonitoringData,
    refreshHeartbeat,
  } = useMonitoringStore();

  const tasks = useTaskStore((state) => state.tasks);
  const projectTasks = tasks.filter(task => task.projectId === projectId && task.status !== 'archived');
  const [selectedTaskId, setSelectedTaskId] = React.useState<string | null>(
    projectTasks.length > 0 ? projectTasks[0].specId : null
  );

  useEffect(() => {
    // Auto-select first task if none selected
    if (!selectedTaskId && projectTasks.length > 0) {
      setSelectedTaskId(projectTasks[0].specId);
    }
  }, [projectTasks, selectedTaskId]);

  useEffect(() => {
    if (selectedTaskId) {
      loadMonitoringData(projectId, selectedTaskId);
      const interval = setInterval(() => {
        refreshHeartbeat(projectId, selectedTaskId);
      }, 30000); // Refresh heartbeat every 30 seconds

      return () => clearInterval(interval);
    }
  }, [projectId, selectedTaskId, loadMonitoringData, refreshHeartbeat]);

  const getStatusVariant = (
    status: HeartbeatStatus
  ): 'success' | 'warning' | 'destructive' | 'muted' => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'destructive';
      default:
        return 'muted';
    }
  };

  const getStatusLabel = (status: HeartbeatStatus): string => {
    return t(`monitoring.status.${status}`);
  };

  const formatCurrency = (amount: number, currency: string): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
    }).format(amount);
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const maxCost = Math.max(...costTrends.map((d) => d.cost), 1);

  if (projectTasks.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            {t('monitoring.title')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center text-sm text-muted-foreground py-8">
            No tasks available for monitoring. Create a task to view analytics.
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              {t('monitoring.title')}
            </CardTitle>
            <CardDescription className="flex items-center gap-2 mt-2">
              {t('monitoring.heartbeat')}:{' '}
              <Badge variant={getStatusVariant(heartbeatStatus)}>
                {getStatusLabel(heartbeatStatus)}
              </Badge>
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Select
              value={selectedTaskId || undefined}
              onValueChange={setSelectedTaskId}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select task" />
              </SelectTrigger>
              <SelectContent>
                {projectTasks.map((task) => (
                  <SelectItem key={task.id} value={task.specId}>
                    {task.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                if (selectedTaskId) {
                  loadMonitoringData(projectId, selectedTaskId);
                  refreshHeartbeat(projectId, selectedTaskId);
                }
              }}
              disabled={isLoading || !selectedTaskId}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              {t('common:buttons.refresh')}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Cost Tracking */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            {t('monitoring.costTracking')}
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-md border border-border bg-card p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t('monitoring.totalCost')}
              </div>
              <div className="text-2xl font-bold">
                {formatCurrency(costMetrics.totalCost, costMetrics.currency)}
              </div>
            </div>

            <div className="rounded-md border border-border bg-card p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t('monitoring.inputTokens')}
              </div>
              <div className="text-2xl font-bold">{formatNumber(costMetrics.inputTokens)}</div>
            </div>

            <div className="rounded-md border border-border bg-card p-4">
              <div className="text-sm text-muted-foreground mb-1">
                {t('monitoring.outputTokens')}
              </div>
              <div className="text-2xl font-bold">{formatNumber(costMetrics.outputTokens)}</div>
            </div>
          </div>
        </div>

        {/* Cost Trends Chart */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            {t('monitoring.costTrends')}
          </h4>

          <Tabs defaultValue="7days" className="w-full">
            <TabsList>
              <TabsTrigger value="7days">{t('monitoring.last7Days')}</TabsTrigger>
              <TabsTrigger value="30days">{t('monitoring.last30Days')}</TabsTrigger>
            </TabsList>

            <TabsContent value="7days" className="mt-4">
              {/* Simple Bar Chart */}
              <div className="space-y-2">
                {costTrends.map((data, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="text-xs text-muted-foreground w-20 text-right">
                      {new Date(data.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })}
                    </div>
                    <div className="flex-1 h-8 relative">
                      <div
                        className="absolute left-0 top-0 h-full bg-primary/20 hover:bg-primary/30 transition-colors rounded-sm flex items-center justify-end pr-2"
                        style={{
                          width: `${(data.cost / maxCost) * 100}%`,
                        }}
                      >
                        <span className="text-xs font-medium">
                          {formatCurrency(data.cost, costMetrics.currency)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="30days" className="mt-4">
              <div className="text-center text-sm text-muted-foreground py-8">
                30-day trends coming soon
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Recent Events */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold">{t('monitoring.recentEvents')}</h4>

          {recentEvents.length === 0 ? (
            <div className="text-center text-sm text-muted-foreground py-8 rounded-md border border-border bg-card">
              {t('monitoring.noEvents')}
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {recentEvents.slice(0, 10).map((event) => (
                <div
                  key={event.id}
                  className="flex items-start gap-2 rounded-md border border-border bg-card p-3"
                >
                  <Badge
                    variant={
                      event.type === 'error'
                        ? 'destructive'
                        : event.type === 'warning'
                        ? 'warning'
                        : 'info'
                    }
                    className="mt-0.5"
                  >
                    {event.type}
                  </Badge>
                  <div className="flex-1">
                    <div className="text-sm">{event.message}</div>
                    {event.details && (
                      <div className="text-xs text-muted-foreground mt-1">{event.details}</div>
                    )}
                    <div className="text-xs text-muted-foreground mt-1">
                      {event.timestamp.toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
