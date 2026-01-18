/**
 * Monitoring handlers - Cost tracking and heartbeat status
 *
 * Provides IPC handlers for reading monitoring data from the backend:
 * - cost_report.json - Token usage and API costs
 * - .heartbeat - Build liveness and activity tracking
 */

import { ipcMain } from 'electron';
import { IPC_CHANNELS, getSpecsDir } from '../../shared/constants';
import type { IPCResult } from '../../shared/types';
import path from 'path';
import { existsSync, readFileSync } from 'fs';
import { projectStore } from '../project-store';

export interface CostMetrics {
  totalCost: number;
  inputTokens: number;
  outputTokens: number;
  cacheCreationTokens: number;
  cacheReadTokens: number;
  currency: string;
  sessions: SessionCost[];
  createdAt: string;
  lastUpdated: string;
}

export interface SessionCost {
  sessionId: number;
  subtaskId: string | null;
  phase: string;
  model: string;
  timestamp: string;
  inputTokens: number;
  outputTokens: number;
  cacheCreationInputTokens: number;
  cacheReadInputTokens: number;
  costUsd: number;
}

export interface HeartbeatData {
  timestamp: string;
  sessionId: number;
  subtaskId: string | null;
  phase: string;
  activity: string;
  pid: number;
}

export type HeartbeatStatus = 'healthy' | 'degraded' | 'down' | 'unknown';

export interface HeartbeatStatusResult {
  status: HeartbeatStatus;
  data?: HeartbeatData;
  timeSinceHeartbeatSeconds?: number;
  stalled?: boolean;
}

// Consider build stalled after 30 minutes of no updates
const STALL_THRESHOLD_SECONDS = 30 * 60;

/**
 * Register monitoring handlers
 */
export function registerMonitoringHandlers(): void {
  /**
   * Get cost metrics for a task
   */
  ipcMain.handle(
    IPC_CHANNELS.MONITORING_GET_COST_METRICS,
    async (_, projectId: string, specId: string): Promise<IPCResult<CostMetrics>> => {
      console.warn('[IPC] MONITORING_GET_COST_METRICS called:', { projectId, specId });

      const project = projectStore.getProject(projectId);
      if (!project) {
        return { success: false, error: 'Project not found' };
      }

      // Find the spec directory
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir = path.join(project.path, specsBaseDir, specId);

      if (!existsSync(specDir)) {
        return { success: false, error: 'Spec directory not found' };
      }

      // Read cost_report.json
      const costReportPath = path.join(specDir, 'cost_report.json');
      if (!existsSync(costReportPath)) {
        // No cost report yet - return zero metrics
        return {
          success: true,
          data: {
            totalCost: 0,
            inputTokens: 0,
            outputTokens: 0,
            cacheCreationTokens: 0,
            cacheReadTokens: 0,
            currency: 'USD',
            sessions: [],
            createdAt: new Date().toISOString(),
            lastUpdated: new Date().toISOString(),
          },
        };
      }

      try {
        const costReportData = JSON.parse(readFileSync(costReportPath, 'utf-8'));

        const metrics: CostMetrics = {
          totalCost: costReportData.total_cost_usd || 0,
          inputTokens: costReportData.total_input_tokens || 0,
          outputTokens: costReportData.total_output_tokens || 0,
          cacheCreationTokens: costReportData.total_cache_creation_tokens || 0,
          cacheReadTokens: costReportData.total_cache_read_tokens || 0,
          currency: 'USD',
          sessions: (costReportData.sessions || []).map((s: any) => ({
            sessionId: s.session_id,
            subtaskId: s.subtask_id,
            phase: s.phase,
            model: s.model,
            timestamp: s.timestamp,
            inputTokens: s.input_tokens,
            outputTokens: s.output_tokens,
            cacheCreationInputTokens: s.cache_creation_input_tokens,
            cacheReadInputTokens: s.cache_read_input_tokens,
            costUsd: s.cost_usd,
          })),
          createdAt: costReportData.created_at || new Date().toISOString(),
          lastUpdated: costReportData.last_updated || new Date().toISOString(),
        };

        console.warn('[IPC] Cost metrics loaded:', {
          totalCost: metrics.totalCost,
          totalTokens: metrics.inputTokens + metrics.outputTokens,
          sessions: metrics.sessions.length,
        });

        return { success: true, data: metrics };
      } catch (error) {
        console.error('[IPC] Failed to parse cost_report.json:', error);
        return {
          success: false,
          error: `Failed to parse cost report: ${error instanceof Error ? error.message : 'Unknown error'}`,
        };
      }
    }
  );

  /**
   * Check heartbeat status for a task
   */
  ipcMain.handle(
    IPC_CHANNELS.MONITORING_CHECK_HEARTBEAT,
    async (_, projectId: string, specId: string): Promise<IPCResult<HeartbeatStatusResult>> => {
      console.warn('[IPC] MONITORING_CHECK_HEARTBEAT called:', { projectId, specId });

      const project = projectStore.getProject(projectId);
      if (!project) {
        return { success: false, error: 'Project not found' };
      }

      // Find the spec directory
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir = path.join(project.path, specsBaseDir, specId);

      if (!existsSync(specDir)) {
        return { success: false, error: 'Spec directory not found' };
      }

      // Read .heartbeat file
      const heartbeatPath = path.join(specDir, '.heartbeat');
      if (!existsSync(heartbeatPath)) {
        // No heartbeat file - status unknown
        return {
          success: true,
          data: {
            status: 'unknown',
          },
        };
      }

      try {
        const heartbeatData: HeartbeatData = JSON.parse(readFileSync(heartbeatPath, 'utf-8'));

        // Calculate time since last heartbeat
        const lastHeartbeat = new Date(heartbeatData.timestamp);
        const timeSinceHeartbeatSeconds = (Date.now() - lastHeartbeat.getTime()) / 1000;

        // Determine status
        let status: HeartbeatStatus;
        let stalled = false;

        if (timeSinceHeartbeatSeconds > STALL_THRESHOLD_SECONDS) {
          status = 'down';
          stalled = true;
        } else if (timeSinceHeartbeatSeconds > STALL_THRESHOLD_SECONDS / 2) {
          // Degraded if more than 15 minutes since last heartbeat
          status = 'degraded';
        } else {
          status = 'healthy';
        }

        console.warn('[IPC] Heartbeat status:', {
          status,
          timeSinceHeartbeatSeconds,
          stalled,
          activity: heartbeatData.activity,
        });

        return {
          success: true,
          data: {
            status,
            data: heartbeatData,
            timeSinceHeartbeatSeconds,
            stalled,
          },
        };
      } catch (error) {
        console.error('[IPC] Failed to parse .heartbeat:', error);
        return {
          success: false,
          error: `Failed to parse heartbeat: ${error instanceof Error ? error.message : 'Unknown error'}`,
        };
      }
    }
  );
}
