import { ipcRenderer } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type { IPCResult } from '../../shared/types';
import type {
  CostMetrics,
  HeartbeatStatusResult
} from '../../main/ipc-handlers/monitoring-handlers';

/**
 * Monitoring API
 *
 * Provides methods for renderer process to interact with monitoring features:
 * - Get cost and token usage metrics
 * - Check build heartbeat status
 */
export interface MonitoringAPI {
  /**
   * Get cost metrics for a task
   * @param projectId - Project ID
   * @param specId - Spec ID
   * @returns Cost and token usage metrics
   */
  getCostMetrics: (projectId: string, specId: string) => Promise<IPCResult<CostMetrics>>;

  /**
   * Check heartbeat status for a task
   * @param projectId - Project ID
   * @param specId - Spec ID
   * @returns Heartbeat status and data
   */
  checkHeartbeat: (projectId: string, specId: string) => Promise<IPCResult<HeartbeatStatusResult>>;
}

export const createMonitoringAPI = (): MonitoringAPI => ({
  getCostMetrics: (projectId: string, specId: string): Promise<IPCResult<CostMetrics>> =>
    ipcRenderer.invoke(IPC_CHANNELS.MONITORING_GET_COST_METRICS, projectId, specId),

  checkHeartbeat: (projectId: string, specId: string): Promise<IPCResult<HeartbeatStatusResult>> =>
    ipcRenderer.invoke(IPC_CHANNELS.MONITORING_CHECK_HEARTBEAT, projectId, specId)
});
