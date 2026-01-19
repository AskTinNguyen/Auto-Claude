/**
 * RPC Method Implementations
 *
 * Provides the backend logic for RPC methods, abstracting access to
 * projectStore, agentManager, and other services for mobile clients.
 */

import { app } from 'electron';
import { existsSync, readFileSync, readdirSync } from 'fs';
import path from 'path';
import { projectStore } from '../project-store';
import type { AgentManager } from '../agent';
import type { Task, TaskStatus, TaskMetadata, Project } from '../../shared/types';
import { AUTO_BUILD_PATHS, getSpecsDir } from '../../shared/constants';
import { findTaskWorktree } from '../worktree-paths';
import type {
  RpcMethodName,
  RpcMethodParams,
  RpcMethodReturns,
  RpcMethodRegistry,
} from './types';
import { RPC_ERROR_CODES } from './types';

/**
 * RPC Error class for typed errors
 */
export class RpcError extends Error {
  constructor(
    public code: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'RpcError';
  }
}

/**
 * Context passed to RPC method handlers
 */
export interface RpcContext {
  agentManager: AgentManager;
}

/**
 * Create the RPC method registry with all method implementations
 */
export function createRpcMethods(context: RpcContext): RpcMethodRegistry {
  const { agentManager } = context;

  return {
    // ─────────────────────────────────────────────────────────────────────────
    // Project Methods
    // ─────────────────────────────────────────────────────────────────────────

    'project.list': async () => {
      return projectStore.getProjects();
    },

    'project.get': async (params) => {
      const project = projectStore.getProject(params.projectId);
      return project || null;
    },

    'project.getActive': async () => {
      const tabState = projectStore.getTabState();
      if (!tabState.activeProjectId) {
        return null;
      }
      return projectStore.getProject(tabState.activeProjectId) || null;
    },

    'project.setActive': async (params) => {
      const project = projectStore.getProject(params.projectId);
      if (!project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Project not found');
      }

      const tabState = projectStore.getTabState();
      tabState.activeProjectId = params.projectId;

      // Add to open projects if not already open
      if (!tabState.openProjectIds.includes(params.projectId)) {
        tabState.openProjectIds.push(params.projectId);
      }

      projectStore.saveTabState(tabState);
      return { success: true };
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Task Methods
    // ─────────────────────────────────────────────────────────────────────────

    'task.list': async (params) => {
      const project = projectStore.getProject(params.projectId);
      if (!project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Project not found');
      }

      return projectStore.getTasks(params.projectId);
    },

    'task.get': async (params) => {
      // Find task across all projects
      const projects = projectStore.getProjects();
      for (const project of projects) {
        const tasks = projectStore.getTasks(project.id);
        const task = tasks.find((t) => t.id === params.taskId);
        if (task) {
          return task;
        }
      }
      return null;
    },

    'task.create': async (params) => {
      const project = projectStore.getProject(params.projectId);
      if (!project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Project not found');
      }

      // Import title generator dynamically to avoid circular deps
      const { titleGenerator } = await import('../title-generator');

      // Auto-generate title if empty
      let finalTitle = params.title;
      if (!finalTitle || !finalTitle.trim()) {
        try {
          const generatedTitle = await titleGenerator.generateTitle(params.description);
          if (generatedTitle) {
            finalTitle = generatedTitle;
          } else {
            finalTitle = params.description.split('\n')[0].substring(0, 60);
            if (finalTitle.length === 60) finalTitle += '...';
          }
        } catch {
          finalTitle = params.description.split('\n')[0].substring(0, 60);
          if (finalTitle.length === 60) finalTitle += '...';
        }
      }

      // Generate spec ID
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specsDir = path.join(project.path, specsBaseDir);

      let specNumber = 1;
      if (existsSync(specsDir)) {
        const existingDirs = readdirSync(specsDir, { withFileTypes: true })
          .filter((d) => d.isDirectory())
          .map((d) => d.name);

        const existingNumbers = existingDirs
          .map((name) => {
            const match = name.match(/^(\d+)/);
            return match ? parseInt(match[1], 10) : 0;
          })
          .filter((n) => n > 0);

        if (existingNumbers.length > 0) {
          specNumber = Math.max(...existingNumbers) + 1;
        }
      }

      const slugifiedTitle = finalTitle
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .substring(0, 50);
      const specId = `${String(specNumber).padStart(3, '0')}-${slugifiedTitle}`;

      // Create spec directory
      const { mkdirSync, writeFileSync } = await import('fs');
      const specDir = path.join(specsDir, specId);
      mkdirSync(specDir, { recursive: true });

      // Create initial implementation_plan.json
      const now = new Date().toISOString();
      const implementationPlan = {
        feature: finalTitle,
        description: params.description,
        created_at: now,
        updated_at: now,
        status: 'pending',
        phases: [],
      };

      const planPath = path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);
      writeFileSync(planPath, JSON.stringify(implementationPlan, null, 2));

      // Save task metadata
      const taskMetadata: TaskMetadata = {
        sourceType: 'manual',
        ...params.metadata,
      };
      const metadataPath = path.join(specDir, 'task_metadata.json');
      writeFileSync(metadataPath, JSON.stringify(taskMetadata, null, 2));

      // Create requirements.json
      const requirements = {
        task_description: params.description,
        workflow_type: taskMetadata.category || 'feature',
      };
      const requirementsPath = path.join(specDir, AUTO_BUILD_PATHS.REQUIREMENTS);
      writeFileSync(requirementsPath, JSON.stringify(requirements, null, 2));

      // Invalidate cache
      projectStore.invalidateTasksCache(params.projectId);

      // Return created task
      const task: Task = {
        id: specId,
        specId: specId,
        projectId: params.projectId,
        title: finalTitle,
        description: params.description,
        status: 'backlog',
        subtasks: [],
        logs: [],
        metadata: taskMetadata,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      return task;
    },

    'task.delete': async (params) => {
      // Find task and project
      const { task, project } = findTaskAndProject(params.taskId);
      if (!task || !project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Task not found');
      }

      // Check if running
      if (agentManager.isRunning(params.taskId)) {
        throw new RpcError(
          RPC_ERROR_CODES.TASK_RUNNING,
          'Cannot delete a running task. Stop the task first.'
        );
      }

      // Delete spec directory
      const { rm } = await import('fs/promises');
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir =
        task.specsPath || path.join(project.path, specsBaseDir, task.specId);

      if (existsSync(specDir)) {
        await rm(specDir, { recursive: true, force: true });
      }

      projectStore.invalidateTasksCache(project.id);
      return { success: true };
    },

    'task.start': async (params) => {
      const { task, project } = findTaskAndProject(params.taskId);
      if (!task || !project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Task not found');
      }

      // Check if already running
      if (agentManager.isRunning(params.taskId)) {
        return { success: true, message: 'Task is already running' };
      }

      // Get spec directory
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir = path.join(project.path, specsBaseDir, task.specId);

      // Check if spec.md exists
      const specFilePath = path.join(specDir, AUTO_BUILD_PATHS.SPEC_FILE);
      const hasSpec = existsSync(specFilePath);

      const baseBranch = task.metadata?.baseBranch || project.settings?.mainBranch;

      if (!hasSpec) {
        // Start spec creation
        const taskDescription = task.description || task.title;
        agentManager.startSpecCreation(
          params.taskId,
          project.path,
          taskDescription,
          specDir,
          task.metadata,
          baseBranch
        );
        return { success: true, message: 'Started spec creation' };
      } else {
        // Start task execution
        agentManager.startTaskExecution(params.taskId, project.path, task.specId, {
          parallel: false,
          workers: 1,
          baseBranch,
          useWorktree: task.metadata?.useWorktree,
        });
        return { success: true, message: 'Started task execution' };
      }
    },

    'task.stop': async (params) => {
      agentManager.killTask(params.taskId);
      return { success: true };
    },

    'task.getStatus': async (params) => {
      const { task } = findTaskAndProject(params.taskId);
      if (!task) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Task not found');
      }

      const isRunning = agentManager.isRunning(params.taskId);
      return {
        status: task.status,
        isRunning,
      };
    },

    'task.updateStatus': async (params) => {
      const { task, project } = findTaskAndProject(params.taskId);
      if (!task || !project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Task not found');
      }

      // Update implementation_plan.json
      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir = path.join(project.path, specsBaseDir, task.specId);
      const planPath = path.join(specDir, AUTO_BUILD_PATHS.IMPLEMENTATION_PLAN);

      if (existsSync(planPath)) {
        const { writeFileSync } = await import('fs');
        const planContent = readFileSync(planPath, 'utf-8');
        const plan = JSON.parse(planContent);

        plan.status = params.status;
        plan.updated_at = new Date().toISOString();

        writeFileSync(planPath, JSON.stringify(plan, null, 2));
      }

      projectStore.invalidateTasksCache(project.id);
      return { success: true };
    },

    // ─────────────────────────────────────────────────────────────────────────
    // System Methods
    // ─────────────────────────────────────────────────────────────────────────

    'system.health': async () => {
      return {
        status: 'ok',
        timestamp: new Date().toISOString(),
      };
    },

    'system.version': async () => {
      return {
        version: app.getVersion(),
        platform: process.platform,
      };
    },

    'system.getLogs': async (params) => {
      const { task, project } = findTaskAndProject(params.taskId);
      if (!task || !project) {
        throw new RpcError(RPC_ERROR_CODES.NOT_FOUND, 'Task not found');
      }

      const specsBaseDir = getSpecsDir(project.autoBuildPath);
      const specDir = path.join(project.path, specsBaseDir, task.specId);

      // Check for worktree
      const worktreePath = findTaskWorktree(project.path, task.specId);
      const targetSpecDir = worktreePath
        ? path.join(worktreePath, specsBaseDir, task.specId)
        : specDir;

      // Read agent log file if it exists
      const logPath = path.join(targetSpecDir, 'agent.log');
      const logs: string[] = [];

      if (existsSync(logPath)) {
        const content = readFileSync(logPath, 'utf-8');
        const lines = content.split('\n').filter((line) => line.trim());
        const limit = params.limit || 100;
        logs.push(...lines.slice(-limit));
      }

      return { logs };
    },
  };
}

/**
 * Find task and project by task ID (helper function)
 */
function findTaskAndProject(taskId: string): {
  task: Task | null;
  project: Project | null;
} {
  const projects = projectStore.getProjects();

  for (const project of projects) {
    const tasks = projectStore.getTasks(project.id);
    const task = tasks.find((t) => t.id === taskId);
    if (task) {
      return { task, project };
    }
  }

  return { task: null, project: null };
}
