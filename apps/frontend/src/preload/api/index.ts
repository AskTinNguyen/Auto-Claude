import { ProjectAPI, createProjectAPI } from './project-api';
import { TerminalAPI, createTerminalAPI } from './terminal-api';
import { TaskAPI, createTaskAPI } from './task-api';
import { SettingsAPI, createSettingsAPI } from './settings-api';
import { FileAPI, createFileAPI } from './file-api';
import { AgentAPI, createAgentAPI } from './agent-api';
import type { IdeationAPI } from './modules/ideation-api';
import type { InsightsAPI } from './modules/insights-api';
import { AppUpdateAPI, createAppUpdateAPI } from './app-update-api';
import { GitHubAPI, createGitHubAPI } from './modules/github-api';
import type { GitLabAPI } from './modules/gitlab-api';
import { DebugAPI, createDebugAPI } from './modules/debug-api';
import { ClaudeCodeAPI, createClaudeCodeAPI } from './modules/claude-code-api';
import { McpAPI, createMcpAPI } from './modules/mcp-api';
import { ProfileAPI, createProfileAPI } from './profile-api';
import { LanAPI, createLanAPI } from './lan-api';
import { ScratchPadAPI, createScratchPadAPI } from './scratchpad-api';
import { RalphAPI, createRalphAPI } from './ralph-api';
import { TTSAPI, createTTSAPI } from './tts-api';
import { MonitoringAPI, createMonitoringAPI } from './monitoring-api';

export interface ElectronAPI extends
  ProjectAPI,
  TerminalAPI,
  TaskAPI,
  SettingsAPI,
  FileAPI,
  AgentAPI,
  IdeationAPI,
  InsightsAPI,
  AppUpdateAPI,
  GitLabAPI,
  DebugAPI,
  ClaudeCodeAPI,
  McpAPI,
  ProfileAPI,
  LanAPI,
  ScratchPadAPI,
  RalphAPI,
  TTSAPI,
  MonitoringAPI {
  github: GitHubAPI;
}

export const createElectronAPI = (): ElectronAPI => ({
  ...createProjectAPI(),
  ...createTerminalAPI(),
  ...createTaskAPI(),
  ...createSettingsAPI(),
  ...createFileAPI(),
  ...createAgentAPI(),  // Includes: Roadmap, Ideation, Insights, Changelog, Linear, GitHub, GitLab, Shell
  ...createAppUpdateAPI(),
  ...createDebugAPI(),
  ...createClaudeCodeAPI(),
  ...createMcpAPI(),
  ...createProfileAPI(),
  ...createLanAPI(),
  ...createScratchPadAPI(),
  ...createRalphAPI(),
  ...createTTSAPI(),
  ...createMonitoringAPI(),
  github: createGitHubAPI()
});

// Export individual API creators for potential use in tests or specialized contexts
// Note: IdeationAPI, InsightsAPI, and GitLabAPI are included in AgentAPI
export {
  createProjectAPI,
  createTerminalAPI,
  createTaskAPI,
  createSettingsAPI,
  createFileAPI,
  createAgentAPI,
  createAppUpdateAPI,
  createProfileAPI,
  createGitHubAPI,
  createDebugAPI,
  createClaudeCodeAPI,
  createMcpAPI,
  createLanAPI,
  createScratchPadAPI,
  createRalphAPI,
  createTTSAPI,
  createMonitoringAPI
};

export type {
  ProjectAPI,
  TerminalAPI,
  TaskAPI,
  SettingsAPI,
  FileAPI,
  AgentAPI,
  IdeationAPI,
  InsightsAPI,
  AppUpdateAPI,
  ProfileAPI,
  GitHubAPI,
  GitLabAPI,
  DebugAPI,
  ClaudeCodeAPI,
  McpAPI,
  LanAPI,
  ScratchPadAPI,
  RalphAPI,
  TTSAPI,
  MonitoringAPI
};
