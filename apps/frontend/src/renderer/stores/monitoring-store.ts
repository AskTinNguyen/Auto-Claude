import { create } from 'zustand';

export type HeartbeatStatus = 'healthy' | 'degraded' | 'down' | 'unknown';

export interface CostMetrics {
  totalCost: number;
  inputTokens: number;
  outputTokens: number;
  currency: string;
}

export interface MonitoringEvent {
  id: string;
  timestamp: Date;
  type: 'info' | 'warning' | 'error';
  message: string;
  details?: string;
}

export interface CostTrendData {
  date: string;
  cost: number;
  tokens: number;
}

interface MonitoringState {
  heartbeatStatus: HeartbeatStatus;
  costMetrics: CostMetrics;
  recentEvents: MonitoringEvent[];
  costTrends: CostTrendData[];
  isLoading: boolean;

  // Actions
  setHeartbeatStatus: (status: HeartbeatStatus) => void;
  setCostMetrics: (metrics: CostMetrics) => void;
  addEvent: (event: Omit<MonitoringEvent, 'id' | 'timestamp'>) => void;
  clearEvents: () => void;
  setCostTrends: (trends: CostTrendData[]) => void;
  setLoading: (loading: boolean) => void;
  loadMonitoringData: (projectId?: string, specId?: string) => Promise<void>;
  refreshHeartbeat: (projectId?: string, specId?: string) => Promise<void>;
}

export const useMonitoringStore = create<MonitoringState>((set, get) => ({
  heartbeatStatus: 'unknown',
  costMetrics: {
    totalCost: 0,
    inputTokens: 0,
    outputTokens: 0,
    currency: 'USD',
  },
  recentEvents: [],
  costTrends: [],
  isLoading: false,

  setHeartbeatStatus: (status) => set({ heartbeatStatus: status }),

  setCostMetrics: (metrics) => set({ costMetrics: metrics }),

  addEvent: (event) => {
    const newEvent: MonitoringEvent = {
      ...event,
      id: `${Date.now()}-${Math.random()}`,
      timestamp: new Date(),
    };

    set((state) => ({
      recentEvents: [newEvent, ...state.recentEvents].slice(0, 50), // Keep last 50 events
    }));
  },

  clearEvents: () => set({ recentEvents: [] }),

  setCostTrends: (trends) => set({ costTrends: trends }),

  setLoading: (loading) => set({ isLoading: loading }),

  loadMonitoringData: async (projectId?: string, specId?: string) => {
    set({ isLoading: true });

    try {
      // If no project/spec provided, keep existing data or show empty state
      if (!projectId || !specId) {
        set({ isLoading: false });
        return;
      }

      // Call Electron IPC to load monitoring data
      const result = await window.electronAPI.getCostMetrics(projectId, specId);

      if (result.success && result.data) {
        const data = result.data;

        // Calculate trends from session data
        const sessionsByDate = new Map<string, { cost: number; tokens: number }>();

        data.sessions.forEach(session => {
          const date = new Date(session.timestamp).toISOString().split('T')[0];
          const existing = sessionsByDate.get(date) || { cost: 0, tokens: 0 };
          sessionsByDate.set(date, {
            cost: existing.cost + session.costUsd,
            tokens: existing.tokens + session.inputTokens + session.outputTokens
          });
        });

        const costTrends: CostTrendData[] = Array.from(sessionsByDate.entries()).map(([date, { cost, tokens }]) => ({
          date,
          cost,
          tokens
        })).sort((a, b) => a.date.localeCompare(b.date));

        const costMetrics: CostMetrics = {
          totalCost: data.totalCost,
          inputTokens: data.inputTokens,
          outputTokens: data.outputTokens,
          currency: data.currency,
        };

        set({
          costMetrics,
          costTrends,
        });
      } else {
        // No data available - set to zero
        set({
          costMetrics: {
            totalCost: 0,
            inputTokens: 0,
            outputTokens: 0,
            currency: 'USD',
          },
          costTrends: [],
        });
      }
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
      get().addEvent({
        type: 'error',
        message: 'Failed to load monitoring data',
        details: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      set({ isLoading: false });
    }
  },

  refreshHeartbeat: async (projectId?: string, specId?: string) => {
    try {
      // If no project/spec provided, set to unknown
      if (!projectId || !specId) {
        set({ heartbeatStatus: 'unknown' });
        return;
      }

      // Call Electron IPC to check heartbeat
      const result = await window.electronAPI.checkHeartbeat(projectId, specId);

      if (result.success && result.data) {
        set({ heartbeatStatus: result.data.status });

        // Add event if stalled
        if (result.data.stalled) {
          get().addEvent({
            type: 'warning',
            message: 'Build appears to be stalled',
            details: `Last activity: ${result.data.data?.activity || 'unknown'}`,
          });
        }
      } else {
        set({ heartbeatStatus: 'unknown' });
      }
    } catch (error) {
      console.error('Failed to refresh heartbeat:', error);
      set({ heartbeatStatus: 'down' });
      get().addEvent({
        type: 'error',
        message: 'Heartbeat check failed',
        details: error instanceof Error ? error.message : 'Unknown error',
      });
    }
  },
}));

// Note: loadMonitoringData and refreshHeartbeat should be called
// with projectId and specId when needed (e.g., when viewing a task)
