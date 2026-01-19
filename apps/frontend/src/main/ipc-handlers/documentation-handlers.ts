/**
 * Documentation IPC Handlers
 *
 * Handles documentation generation, application, and validation operations
 * between the renderer process and the main process.
 */

import { ipcMain } from 'electron';
import type { BrowserWindow } from 'electron';
import path from 'path';
import { existsSync, readFileSync, writeFileSync, mkdirSync } from 'fs';
import { IPC_CHANNELS, getSpecsDir } from '../../shared/constants';
import type {
  IPCResult,
  DocumentationItem,
  DocumentationType,
  DocumentationLanguage,
  DocumentationGenerationRequest,
} from '../../shared/types';
import { projectStore } from '../project-store';
import { safeSendToRenderer } from './utils';

/**
 * Documentation storage file name within project's .auto-claude directory
 */
const DOCUMENTATION_FILE = 'documentation-items.json';

/**
 * Get documentation storage path for a project
 */
function getDocumentationStoragePath(projectPath: string, autoBuildPath?: string): string {
  const baseDir = autoBuildPath
    ? path.join(projectPath, autoBuildPath)
    : path.join(projectPath, '.auto-claude');
  return path.join(baseDir, DOCUMENTATION_FILE);
}

/**
 * Load documentation items from storage
 */
function loadDocumentationItems(projectPath: string, autoBuildPath?: string): DocumentationItem[] {
  const storagePath = getDocumentationStoragePath(projectPath, autoBuildPath);

  if (!existsSync(storagePath)) {
    return [];
  }

  try {
    const content = readFileSync(storagePath, 'utf-8');
    return JSON.parse(content);
  } catch (error) {
    console.error('[Documentation] Failed to load items:', error);
    return [];
  }
}

/**
 * Save documentation items to storage
 */
function saveDocumentationItems(
  projectPath: string,
  items: DocumentationItem[],
  autoBuildPath?: string
): void {
  const storagePath = getDocumentationStoragePath(projectPath, autoBuildPath);
  const dir = path.dirname(storagePath);

  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(storagePath, JSON.stringify(items, null, 2), 'utf-8');
}

/**
 * Generate a unique ID for documentation items
 */
function generateId(): string {
  return `doc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Detect language from file extension
 */
function detectLanguage(filePath: string): DocumentationLanguage {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case '.py':
      return 'python';
    case '.ts':
    case '.tsx':
      return 'typescript';
    case '.js':
    case '.jsx':
      return 'javascript';
    case '.go':
      return 'go';
    case '.rs':
      return 'rust';
    case '.java':
      return 'java';
    default:
      return 'markdown';
  }
}

/**
 * Generate documentation content based on type and language
 */
function generateDocumentationContent(
  request: DocumentationGenerationRequest,
  language: DocumentationLanguage
): string {
  const { type, targetName, context } = request;

  // Generate template-based documentation
  switch (type) {
    case 'docstring':
      if (language === 'python') {
        return `"""
${targetName || 'Function'} - ${context || 'Description goes here.'}

Args:
    param1: Description of parameter 1
    param2: Description of parameter 2

Returns:
    Description of return value

Raises:
    Exception: Description of when this exception is raised
"""`;
      } else {
        // TypeScript/JavaScript JSDoc style
        return `/**
 * ${targetName || 'Function'} - ${context || 'Description goes here.'}
 *
 * @param param1 - Description of parameter 1
 * @param param2 - Description of parameter 2
 * @returns Description of return value
 * @throws {Error} Description of when this error is thrown
 */`;
      }

    case 'jsdoc':
      return `/**
 * ${targetName || 'Function'} - ${context || 'Description goes here.'}
 *
 * @param {string} param1 - Description of parameter 1
 * @param {number} param2 - Description of parameter 2
 * @returns {ReturnType} Description of return value
 * @example
 * // Example usage
 * ${targetName || 'functionName'}(arg1, arg2);
 */`;

    case 'readme':
      return `# ${targetName || 'Project Name'}

${context || 'Project description goes here.'}

## Installation

\`\`\`bash
npm install
\`\`\`

## Usage

\`\`\`typescript
// Example usage code
\`\`\`

## API Reference

### Functions

- \`functionName(param1, param2)\` - Description

## License

MIT
`;

    case 'changelog':
      const date = new Date().toISOString().split('T')[0];
      return `# Changelog

## [Unreleased]

### Added
- ${context || 'New feature description'}

### Changed
- Description of changes

### Fixed
- Description of bug fixes

## [1.0.0] - ${date}

### Added
- Initial release
`;

    case 'api-docs':
      return `# API Documentation

## ${targetName || 'Endpoint'}

${context || 'Endpoint description goes here.'}

### Request

\`\`\`http
GET /api/endpoint
\`\`\`

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| param1 | string | Yes | Description |
| param2 | number | No | Description |

### Response

\`\`\`json
{
  "success": true,
  "data": {}
}
\`\`\`

### Errors

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 404 | Not Found |
`;

    default:
      return `# ${targetName || 'Documentation'}

${context || 'Add your documentation content here.'}
`;
  }
}

/**
 * Validate documentation content
 */
function validateDocumentationContent(
  content: string,
  type: DocumentationType,
  language: DocumentationLanguage
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!content || content.trim().length === 0) {
    errors.push('Documentation content is empty');
    return { valid: false, errors };
  }

  // Type-specific validation
  switch (type) {
    case 'docstring':
      if (language === 'python') {
        if (!content.includes('"""') && !content.includes("'''")) {
          errors.push('Python docstring should be enclosed in triple quotes');
        }
      } else if (!content.includes('/**') || !content.includes('*/')) {
        errors.push('JSDoc-style docstring should be enclosed in /** */');
      }
      break;

    case 'jsdoc':
      if (!content.includes('/**') || !content.includes('*/')) {
        errors.push('JSDoc should be enclosed in /** */');
      }
      if (!content.includes('@')) {
        errors.push('JSDoc should contain at least one @tag');
      }
      break;

    case 'readme':
    case 'changelog':
    case 'api-docs':
      if (!content.includes('#')) {
        errors.push('Markdown documentation should contain at least one heading');
      }
      break;
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Apply documentation to a file
 */
function applyDocumentationToFile(
  projectPath: string,
  filePath: string,
  content: string,
  targetName?: string,
  lineNumber?: number
): { success: boolean; error?: string } {
  const fullPath = path.isAbsolute(filePath)
    ? filePath
    : path.join(projectPath, filePath);

  if (!existsSync(fullPath)) {
    return { success: false, error: `File not found: ${filePath}` };
  }

  try {
    const fileContent = readFileSync(fullPath, 'utf-8');
    const lines = fileContent.split('\n');

    // If line number is specified, insert at that location
    if (lineNumber !== undefined && lineNumber > 0 && lineNumber <= lines.length) {
      // Insert documentation before the specified line
      lines.splice(lineNumber - 1, 0, content);
      writeFileSync(fullPath, lines.join('\n'), 'utf-8');
      return { success: true };
    }

    // If target name is specified, try to find and update existing documentation
    if (targetName) {
      // Look for function/class definition
      const targetPattern = new RegExp(
        `(def\\s+${targetName}|function\\s+${targetName}|class\\s+${targetName}|const\\s+${targetName}|let\\s+${targetName})`,
        'g'
      );

      let match;
      while ((match = targetPattern.exec(fileContent)) !== null) {
        const lineIndex = fileContent.substring(0, match.index).split('\n').length - 1;
        // Insert documentation before the target
        lines.splice(lineIndex, 0, content);
        writeFileSync(fullPath, lines.join('\n'), 'utf-8');
        return { success: true };
      }
    }

    // Default: prepend to file (for README, etc.)
    writeFileSync(fullPath, content + '\n\n' + fileContent, 'utf-8');
    return { success: true };
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    return { success: false, error: `Failed to apply documentation: ${errorMsg}` };
  }
}

/**
 * Register all documentation-related IPC handlers
 */
export function registerDocumentationHandlers(
  getMainWindow: () => BrowserWindow | null
): void {
  console.warn('[Documentation] Registering documentation handlers');

  // ============================================
  // Documentation List Handler
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.DOCUMENTATION_LIST,
    async (_, { projectId }: { projectId: string }): Promise<IPCResult<{ items: DocumentationItem[] }>> => {
      const project = projectStore.getProject(projectId);
      if (!project) {
        return { success: false, error: 'Project not found' };
      }

      try {
        const items = loadDocumentationItems(project.path, project.autoBuildPath);
        return { success: true, items };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        return { success: false, error: `Failed to load documentation: ${errorMsg}` };
      }
    }
  );

  // ============================================
  // Documentation Generate Handler
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.DOCUMENTATION_GENERATE,
    async (
      _,
      request: DocumentationGenerationRequest
    ): Promise<IPCResult<{ content: string }>> => {
      const { type, filePath, targetName, context } = request;

      try {
        // Detect language from file path
        const language = detectLanguage(filePath);

        // Generate documentation content
        const content = generateDocumentationContent(request, language);

        // Send progress event
        const mainWindow = getMainWindow();
        if (mainWindow) {
          safeSendToRenderer(
            getMainWindow,
            IPC_CHANNELS.DOCUMENTATION_GENERATION_PROGRESS,
            { progress: 100, message: 'Documentation generated' }
          );
        }

        return { success: true, content };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';

        // Send error event
        safeSendToRenderer(
          getMainWindow,
          IPC_CHANNELS.DOCUMENTATION_ERROR,
          errorMsg
        );

        return { success: false, error: `Failed to generate documentation: ${errorMsg}` };
      }
    }
  );

  // ============================================
  // Documentation Apply Handler
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.DOCUMENTATION_APPLY,
    async (
      _,
      {
        filePath,
        targetName,
        lineNumber,
        content,
        type,
      }: {
        filePath: string;
        targetName?: string;
        lineNumber?: number;
        content: string;
        type: DocumentationType;
      }
    ): Promise<IPCResult<void>> => {
      // Find project by file path
      const projects = projectStore.listProjects();
      const project = projects.find((p) =>
        filePath.startsWith(p.path) || !path.isAbsolute(filePath)
      );

      if (!project) {
        return { success: false, error: 'Project not found for file' };
      }

      try {
        const result = applyDocumentationToFile(
          project.path,
          filePath,
          content,
          targetName,
          lineNumber
        );

        if (!result.success) {
          return { success: false, error: result.error };
        }

        // Update stored documentation items
        const items = loadDocumentationItems(project.path, project.autoBuildPath);
        const existingIndex = items.findIndex(
          (item) =>
            item.target.filePath === filePath &&
            item.target.name === targetName
        );

        if (existingIndex >= 0) {
          items[existingIndex].status = 'applied';
          items[existingIndex].updatedAt = new Date().toISOString();
        }

        saveDocumentationItems(project.path, items, project.autoBuildPath);

        return { success: true };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        return { success: false, error: `Failed to apply documentation: ${errorMsg}` };
      }
    }
  );

  // ============================================
  // Documentation Validate Handler
  // ============================================

  ipcMain.handle(
    IPC_CHANNELS.DOCUMENTATION_VALIDATE,
    async (
      _,
      {
        content,
        type,
        language,
      }: {
        content: string;
        type: DocumentationType;
        language: DocumentationLanguage;
      }
    ): Promise<IPCResult<{ valid: boolean; errors: string[] }>> => {
      try {
        const result = validateDocumentationContent(content, type, language);
        return { success: true, valid: result.valid, errors: result.errors };
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        return { success: false, error: `Failed to validate documentation: ${errorMsg}` };
      }
    }
  );

  console.warn('[Documentation] Documentation handlers registered');
}
