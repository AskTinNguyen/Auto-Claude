/**
 * Ralph CLI IPC Handlers
 *
 * Handles Ralph CLI operations from the renderer process:
 * - Environment diagnostics (doctor)
 * - Stats and metrics
 * - Budget management
 * - Cost estimation
 * - Stream/worktree management
 * - TTS control
 * - Quality review
 */

import { ipcMain } from 'electron';
import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

// Import logger if available
let logger = {
  info: console.log,
  error: console.error,
  warn: console.warn,
};

// IPC channel prefix for Ralph
const RALPH_CHANNELS = {
  // Environment
  DOCTOR: 'ralph:doctor',
  PING: 'ralph:ping',

  // Stats & Budget
  STATS: 'ralph:stats',
  BUDGET_GET: 'ralph:budget:get',
  BUDGET_SET: 'ralph:budget:set',
  BUDGET_CLEAR: 'ralph:budget:clear',

  // Estimation
  ESTIMATE: 'ralph:estimate',

  // Stream/Worktree
  STREAM_LIST: 'ralph:stream:list',
  STREAM_NEW: 'ralph:stream:new',
  STREAM_STATUS: 'ralph:stream:status',
  STREAM_MERGE: 'ralph:stream:merge',
  STREAM_CLEANUP: 'ralph:stream:cleanup',

  // TTS
  SPEAK: 'ralph:speak',
  SPEAK_STATUS: 'ralph:speak:status',

  // Review
  REVIEW: 'ralph:review',

  // Config
  CONFIG_GET: 'ralph:config:get',
  CONFIG_SAVE: 'ralph:config:save',
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

/**
 * Run a Ralph CLI command and return the result
 */
async function runRalphCommand<T = unknown>(
  projectDir: string,
  args: string[]
): Promise<RalphResult<T>> {
  return new Promise((resolve) => {
    const pythonPath = process.platform === 'win32' ? 'python' : 'python3';
    const ralphModule = 'ralph_cli.main';

    const fullArgs = ['-m', ralphModule, '--project', projectDir, ...args, '--json'];

    logger.info(`Running Ralph command: ${pythonPath} ${fullArgs.join(' ')}`);

    const proc = spawn(pythonPath, fullArgs, {
      cwd: path.join(projectDir, 'apps', 'backend'),
      env: { ...process.env },
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code === 0) {
        try {
          // Try to parse JSON output
          const jsonMatch = stdout.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
          if (jsonMatch) {
            const data = JSON.parse(jsonMatch[0]);
            resolve({ success: true, data });
          } else {
            resolve({ success: true, data: stdout.trim() });
          }
        } catch {
          resolve({ success: true, data: stdout.trim() });
        }
      } else {
        resolve({
          success: false,
          error: stderr || stdout || `Command failed with code ${code}`,
        });
      }
    });

    proc.on('error', (error) => {
      resolve({
        success: false,
        error: error.message,
      });
    });
  });
}

/**
 * Load budget config directly from file
 */
function loadBudgetConfig(projectDir: string): BudgetResult {
  const budgetFile = path.join(projectDir, '.auto-claude', 'budget.json');
  let config: BudgetResult = {
    globalBudgetUsd: null,
    totalSpentUsd: 0,
    remainingUsd: null,
    specBudgets: {},
    warningThreshold: 0.8,
  };

  try {
    if (fs.existsSync(budgetFile)) {
      const data = JSON.parse(fs.readFileSync(budgetFile, 'utf-8'));
      config.globalBudgetUsd = data.global_limit_usd ?? null;
      config.specBudgets = data.spec_budgets ?? {};
      config.warningThreshold = data.warning_threshold ?? 0.8;
    }
  } catch (error) {
    logger.warn('Could not load budget config:', error);
  }

  // Calculate total spent from cost reports
  const specsDir = path.join(projectDir, '.auto-claude', 'specs');
  if (fs.existsSync(specsDir)) {
    for (const spec of fs.readdirSync(specsDir)) {
      const costFile = path.join(specsDir, spec, 'cost_report.json');
      if (fs.existsSync(costFile)) {
        try {
          const costData = JSON.parse(fs.readFileSync(costFile, 'utf-8'));
          config.totalSpentUsd += costData.total_cost_usd ?? 0;
        } catch {
          // Skip invalid files
        }
      }
    }
  }

  if (config.globalBudgetUsd !== null) {
    config.remainingUsd = config.globalBudgetUsd - config.totalSpentUsd;
  }

  return config;
}

/**
 * Save budget config directly to file
 */
function saveBudgetConfig(
  projectDir: string,
  updates: Partial<{
    globalLimitUsd: number | null;
    specBudgets: Record<string, number>;
    warningThreshold: number;
  }>
): void {
  const budgetFile = path.join(projectDir, '.auto-claude', 'budget.json');
  const autoClaudeDir = path.dirname(budgetFile);

  // Ensure directory exists
  if (!fs.existsSync(autoClaudeDir)) {
    fs.mkdirSync(autoClaudeDir, { recursive: true });
  }

  // Load existing config
  let config: Record<string, unknown> = {};
  if (fs.existsSync(budgetFile)) {
    try {
      config = JSON.parse(fs.readFileSync(budgetFile, 'utf-8'));
    } catch {
      // Start fresh
    }
  }

  // Apply updates
  if (updates.globalLimitUsd !== undefined) {
    config.global_limit_usd = updates.globalLimitUsd;
  }
  if (updates.specBudgets !== undefined) {
    config.spec_budgets = updates.specBudgets;
  }
  if (updates.warningThreshold !== undefined) {
    config.warning_threshold = updates.warningThreshold;
  }

  fs.writeFileSync(budgetFile, JSON.stringify(config, null, 2));
}

/**
 * Load stats from spec directories
 */
function loadStats(projectDir: string): StatsResult {
  const stats: StatsResult = {
    totalSpecs: 0,
    totalSessions: 0,
    totalCostUsd: 0,
    avgCostPerSpec: 0,
    successRate: 0,
    totalInputTokens: 0,
    totalOutputTokens: 0,
  };

  const specsDir = path.join(projectDir, '.auto-claude', 'specs');
  if (!fs.existsSync(specsDir)) {
    return stats;
  }

  const specs = fs.readdirSync(specsDir).filter((name) => {
    return fs.statSync(path.join(specsDir, name)).isDirectory();
  });

  stats.totalSpecs = specs.length;

  let qaPassedCount = 0;
  let qaTotal = 0;

  for (const spec of specs) {
    const specDir = path.join(specsDir, spec);

    // Load cost report
    const costFile = path.join(specDir, 'cost_report.json');
    if (fs.existsSync(costFile)) {
      try {
        const costData = JSON.parse(fs.readFileSync(costFile, 'utf-8'));
        stats.totalCostUsd += costData.total_cost_usd ?? 0;
        stats.totalInputTokens += costData.total_input_tokens ?? 0;
        stats.totalOutputTokens += costData.total_output_tokens ?? 0;
        stats.totalSessions += (costData.sessions ?? []).length;
      } catch {
        // Skip invalid files
      }
    }

    // Check QA report
    const qaFile = path.join(specDir, 'qa_report.md');
    if (fs.existsSync(qaFile)) {
      qaTotal++;
      const content = fs.readFileSync(qaFile, 'utf-8');
      if (content.includes('APPROVED') || content.includes('✓')) {
        qaPassedCount++;
      }
    }
  }

  if (stats.totalSpecs > 0) {
    stats.avgCostPerSpec = stats.totalCostUsd / stats.totalSpecs;
  }

  if (qaTotal > 0) {
    stats.successRate = (qaPassedCount / qaTotal) * 100;
  }

  return stats;
}

/**
 * List all worktrees/streams
 */
function listStreams(projectDir: string): StreamInfo[] {
  const streams: StreamInfo[] = [];

  // Check new location
  const worktreesDir = path.join(projectDir, '.auto-claude', 'worktrees', 'tasks');
  if (fs.existsSync(worktreesDir)) {
    for (const name of fs.readdirSync(worktreesDir)) {
      const worktreePath = path.join(worktreesDir, name);
      if (fs.statSync(worktreePath).isDirectory()) {
        streams.push({
          specName: name,
          branch: `auto-claude/${name}`,
          path: worktreePath,
          commitCount: 0,
          filesChanged: 0,
          additions: 0,
          deletions: 0,
          daysSinceLastCommit: null,
        });
      }
    }
  }

  // Check legacy location
  const legacyDir = path.join(projectDir, '.worktrees');
  if (fs.existsSync(legacyDir)) {
    for (const name of fs.readdirSync(legacyDir)) {
      const worktreePath = path.join(legacyDir, name);
      if (
        fs.statSync(worktreePath).isDirectory() &&
        !streams.find((s) => s.specName === name)
      ) {
        streams.push({
          specName: name,
          branch: `auto-claude/${name}`,
          path: worktreePath,
          commitCount: 0,
          filesChanged: 0,
          additions: 0,
          deletions: 0,
          daysSinceLastCommit: null,
        });
      }
    }
  }

  return streams;
}

/**
 * Register Ralph CLI IPC handlers
 */
export function registerRalphHandlers(): void {
  // Doctor - environment diagnostics
  ipcMain.handle(
    RALPH_CHANNELS.DOCTOR,
    async (_, projectDir: string): Promise<RalphResult<DoctorResult>> => {
      logger.info('Ralph doctor requested for:', projectDir);
      return runRalphCommand<DoctorResult>(projectDir, ['doctor']);
    }
  );

  // Ping - quick health check
  ipcMain.handle(
    RALPH_CHANNELS.PING,
    async (_, projectDir: string): Promise<RalphResult> => {
      logger.info('Ralph ping requested for:', projectDir);
      return runRalphCommand(projectDir, ['ping']);
    }
  );

  // Stats - performance metrics
  ipcMain.handle(
    RALPH_CHANNELS.STATS,
    async (_, projectDir: string): Promise<RalphResult<StatsResult>> => {
      logger.info('Ralph stats requested for:', projectDir);
      try {
        const stats = loadStats(projectDir);
        return { success: true, data: stats };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
  );

  // Budget - get current budget
  ipcMain.handle(
    RALPH_CHANNELS.BUDGET_GET,
    async (_, projectDir: string): Promise<RalphResult<BudgetResult>> => {
      logger.info('Ralph budget get requested for:', projectDir);
      try {
        const budget = loadBudgetConfig(projectDir);
        return { success: true, data: budget };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
  );

  // Budget - set budget
  ipcMain.handle(
    RALPH_CHANNELS.BUDGET_SET,
    async (
      _,
      projectDir: string,
      amount: number,
      specName?: string
    ): Promise<RalphResult> => {
      logger.info('Ralph budget set requested:', { projectDir, amount, specName });
      try {
        if (specName) {
          const budget = loadBudgetConfig(projectDir);
          budget.specBudgets[specName] = amount;
          saveBudgetConfig(projectDir, { specBudgets: budget.specBudgets });
        } else {
          saveBudgetConfig(projectDir, { globalLimitUsd: amount });
        }
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
  );

  // Budget - clear budget
  ipcMain.handle(
    RALPH_CHANNELS.BUDGET_CLEAR,
    async (_, projectDir: string, specName?: string): Promise<RalphResult> => {
      logger.info('Ralph budget clear requested:', { projectDir, specName });
      try {
        if (specName) {
          const budget = loadBudgetConfig(projectDir);
          delete budget.specBudgets[specName];
          saveBudgetConfig(projectDir, { specBudgets: budget.specBudgets });
        } else {
          saveBudgetConfig(projectDir, { globalLimitUsd: null });
        }
        return { success: true };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
  );

  // Estimate - cost estimation
  ipcMain.handle(
    RALPH_CHANNELS.ESTIMATE,
    async (
      _,
      projectDir: string,
      specName: string
    ): Promise<RalphResult<EstimateResult>> => {
      logger.info('Ralph estimate requested:', { projectDir, specName });
      return runRalphCommand<EstimateResult>(projectDir, ['estimate', '--spec', specName]);
    }
  );

  // Stream list
  ipcMain.handle(
    RALPH_CHANNELS.STREAM_LIST,
    async (_, projectDir: string): Promise<RalphResult<StreamInfo[]>> => {
      logger.info('Ralph stream list requested for:', projectDir);
      try {
        const streams = listStreams(projectDir);
        return { success: true, data: streams };
      } catch (error) {
        return {
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        };
      }
    }
  );

  // Stream new
  ipcMain.handle(
    RALPH_CHANNELS.STREAM_NEW,
    async (_, projectDir: string, name: string): Promise<RalphResult> => {
      logger.info('Ralph stream new requested:', { projectDir, name });
      return runRalphCommand(projectDir, ['stream', 'new', name]);
    }
  );

  // Stream status
  ipcMain.handle(
    RALPH_CHANNELS.STREAM_STATUS,
    async (_, projectDir: string, name?: string): Promise<RalphResult> => {
      logger.info('Ralph stream status requested:', { projectDir, name });
      const args = ['stream', 'status'];
      if (name) args.push(name);
      return runRalphCommand(projectDir, args);
    }
  );

  // Stream merge
  ipcMain.handle(
    RALPH_CHANNELS.STREAM_MERGE,
    async (
      _,
      projectDir: string,
      name: string,
      deleteAfter: boolean
    ): Promise<RalphResult> => {
      logger.info('Ralph stream merge requested:', { projectDir, name, deleteAfter });
      const args = ['stream', 'merge', name];
      if (deleteAfter) args.push('--delete');
      return runRalphCommand(projectDir, args);
    }
  );

  // Stream cleanup
  ipcMain.handle(
    RALPH_CHANNELS.STREAM_CLEANUP,
    async (_, projectDir: string, name: string): Promise<RalphResult> => {
      logger.info('Ralph stream cleanup requested:', { projectDir, name });
      return runRalphCommand(projectDir, ['stream', 'cleanup', name]);
    }
  );

  // Speak
  ipcMain.handle(
    RALPH_CHANNELS.SPEAK,
    async (_, projectDir: string, text: string): Promise<RalphResult> => {
      logger.info('Ralph speak requested:', { projectDir, text: text.substring(0, 50) });
      return runRalphCommand(projectDir, ['speak', text]);
    }
  );

  // Speak status
  ipcMain.handle(
    RALPH_CHANNELS.SPEAK_STATUS,
    async (_, projectDir: string): Promise<RalphResult<TTSStatus>> => {
      logger.info('Ralph speak status requested for:', projectDir);
      return runRalphCommand<TTSStatus>(projectDir, ['speak', '--status']);
    }
  );

  // Review
  ipcMain.handle(
    RALPH_CHANNELS.REVIEW,
    async (
      _,
      projectDir: string,
      specName: string
    ): Promise<RalphResult<ReviewResult[]>> => {
      logger.info('Ralph review requested:', { projectDir, specName });
      return runRalphCommand<ReviewResult[]>(projectDir, ['review', specName]);
    }
  );

  // Init - create config
  ipcMain.handle(
    RALPH_CHANNELS.INIT,
    async (_, projectDir: string): Promise<RalphResult> => {
      logger.info('Ralph init requested for:', projectDir);
      return runRalphCommand(projectDir, ['init']);
    }
  );

  logger.info('Ralph CLI IPC handlers registered');
}

export { RALPH_CHANNELS };
