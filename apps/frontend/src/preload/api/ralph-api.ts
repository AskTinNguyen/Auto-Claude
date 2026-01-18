/**
 * Ralph CLI API
 *
 * Provides access to Ralph CLI functionality from the renderer process.
 */

import { ipcRenderer } from 'electron';

// IPC channel constants (must match ralph-handlers.ts)
const RALPH_CHANNELS = {
  DOCTOR: 'ralph:doctor',
  PING: 'ralph:ping',
  STATS: 'ralph:stats',
  BUDGET_GET: 'ralph:budget:get',
  BUDGET_SET: 'ralph:budget:set',
  BUDGET_CLEAR: 'ralph:budget:clear',
  ESTIMATE: 'ralph:estimate',
  STREAM_LIST: 'ralph:stream:list',
  STREAM_NEW: 'ralph:stream:new',
  STREAM_STATUS: 'ralph:stream:status',
  STREAM_MERGE: 'ralph:stream:merge',
  STREAM_CLEANUP: 'ralph:stream:cleanup',
  SPEAK: 'ralph:speak',
  SPEAK_STATUS: 'ralph:speak:status',
  REVIEW: 'ralph:review',
  INIT: 'ralph:init',
} as const;

export interface RalphResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface DoctorCheck {
  name: string;
  passed: boolean;
  info: string;
}

export interface DoctorResult {
  passed: boolean;
  checks: DoctorCheck[];
}

export interface StatsResult {
  totalSpecs: number;
  totalSessions: number;
  totalCostUsd: number;
  avgCostPerSpec: number;
  successRate: number;
  totalInputTokens: number;
  totalOutputTokens: number;
}

export interface BudgetResult {
  globalBudgetUsd: number | null;
  totalSpentUsd: number;
  remainingUsd: number | null;
  specBudgets: Record<string, number>;
  warningThreshold: number;
}

export interface EstimateResult {
  specId: string;
  estimatedInputTokens: number;
  estimatedOutputTokens: number;
  estimatedTotalTokens: number;
  estimatedCostUsd: number;
  model: string;
  confidence: 'low' | 'medium' | 'high';
}

export interface StreamInfo {
  specName: string;
  branch: string;
  path: string;
  commitCount: number;
  filesChanged: number;
  additions: number;
  deletions: number;
  daysSinceLastCommit: number | null;
}

export interface TTSStatus {
  enabled: boolean;
  activeProvider: string | null;
  availableProviders: string[];
}

export interface ReviewResult {
  specName: string;
  score: number;
  grade: string;
  issues: string[];
  checks: Array<{ name: string; passed: boolean; details: string }>;
}

export interface RalphAPI {
  ralph: {
    /**
     * Run environment diagnostics
     */
    doctor: (projectDir: string) => Promise<RalphResult<DoctorResult>>;

    /**
     * Quick health check
     */
    ping: (projectDir: string) => Promise<RalphResult>;

    /**
     * Get performance statistics
     */
    stats: (projectDir: string) => Promise<RalphResult<StatsResult>>;

    /**
     * Get current budget configuration
     */
    budgetGet: (projectDir: string) => Promise<RalphResult<BudgetResult>>;

    /**
     * Set budget limit
     */
    budgetSet: (
      projectDir: string,
      amount: number,
      specName?: string
    ) => Promise<RalphResult>;

    /**
     * Clear budget limit
     */
    budgetClear: (projectDir: string, specName?: string) => Promise<RalphResult>;

    /**
     * Estimate cost for a spec
     */
    estimate: (
      projectDir: string,
      specName: string
    ) => Promise<RalphResult<EstimateResult>>;

    /**
     * List all streams (worktrees)
     */
    streamList: (projectDir: string) => Promise<RalphResult<StreamInfo[]>>;

    /**
     * Create a new stream
     */
    streamNew: (projectDir: string, name: string) => Promise<RalphResult>;

    /**
     * Get stream status
     */
    streamStatus: (projectDir: string, name?: string) => Promise<RalphResult>;

    /**
     * Merge a stream to base branch
     */
    streamMerge: (
      projectDir: string,
      name: string,
      deleteAfter?: boolean
    ) => Promise<RalphResult>;

    /**
     * Remove a stream
     */
    streamCleanup: (projectDir: string, name: string) => Promise<RalphResult>;

    /**
     * Speak text using TTS
     */
    speak: (projectDir: string, text: string) => Promise<RalphResult>;

    /**
     * Get TTS status
     */
    speakStatus: (projectDir: string) => Promise<RalphResult<TTSStatus>>;

    /**
     * Run quality review on a spec
     */
    review: (
      projectDir: string,
      specName: string
    ) => Promise<RalphResult<ReviewResult[]>>;

    /**
     * Initialize Ralph configuration
     */
    init: (projectDir: string) => Promise<RalphResult>;
  };
}

export const createRalphAPI = (): RalphAPI => ({
  ralph: {
    doctor: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.DOCTOR, projectDir),

    ping: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.PING, projectDir),

    stats: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STATS, projectDir),

    budgetGet: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.BUDGET_GET, projectDir),

    budgetSet: (projectDir: string, amount: number, specName?: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.BUDGET_SET, projectDir, amount, specName),

    budgetClear: (projectDir: string, specName?: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.BUDGET_CLEAR, projectDir, specName),

    estimate: (projectDir: string, specName: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.ESTIMATE, projectDir, specName),

    streamList: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STREAM_LIST, projectDir),

    streamNew: (projectDir: string, name: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STREAM_NEW, projectDir, name),

    streamStatus: (projectDir: string, name?: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STREAM_STATUS, projectDir, name),

    streamMerge: (projectDir: string, name: string, deleteAfter = false) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STREAM_MERGE, projectDir, name, deleteAfter),

    streamCleanup: (projectDir: string, name: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.STREAM_CLEANUP, projectDir, name),

    speak: (projectDir: string, text: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.SPEAK, projectDir, text),

    speakStatus: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.SPEAK_STATUS, projectDir),

    review: (projectDir: string, specName: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.REVIEW, projectDir, specName),

    init: (projectDir: string) =>
      ipcRenderer.invoke(RALPH_CHANNELS.INIT, projectDir),
  },
});

export type { RalphResult as RalphAPIResult };
