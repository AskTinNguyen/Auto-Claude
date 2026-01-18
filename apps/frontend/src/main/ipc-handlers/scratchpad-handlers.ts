/**
 * ScratchPad IPC Handlers
 *
 * Handles IPC communication for Notes, Snippets, and Templates
 */

import { ipcMain } from 'electron';
import { existsSync, mkdirSync, writeFileSync, readFileSync, readdirSync, unlinkSync, statSync } from 'fs';
import path from 'path';
import { app } from 'electron';
import { IPC_CHANNELS } from '../../shared/constants';
import type {
  IPCResult,
  Snippet,
  SnippetListItem,
  FileTemplate,
  TemplateListItem,
  CreateSnippetRequest,
  DeleteSnippetRequest,
  GetSnippetRequest,
  ListSnippetsRequest,
  SaveNotesRequest,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  DeleteTemplateRequest,
  CloneTemplateRequest,
  GetTemplateRequest,
  ListTemplatesRequest,
  sanitizeFilename,
  generatePreview,
  isValidTrigger
} from '../../shared/types';
import {
  loadSystemTemplates,
  getSystemTemplateById,
  initializeSystemTemplates
} from '../scratchpad/init-system-templates';

// ============================================
// Path Helpers
// ============================================

/**
 * Get the path to the scratchpad notes file
 */
function getNotesPath(): string {
  const autoClaudeDir = path.join(app.getPath('home'), '.auto-claude');
  return path.join(autoClaudeDir, 'scratchpad.md');
}

/**
 * Get the snippets directory for a project
 */
function getSnippetsDir(projectPath: string): string {
  return path.join(projectPath, '.claude', 'snippets');
}

/**
 * Get the templates directory for a project
 */
function getTemplatesDir(projectPath: string): string {
  return path.join(projectPath, '.claude', 'templates');
}

/**
 * Ensure a directory exists
 */
function ensureDir(dirPath: string): void {
  if (!existsSync(dirPath)) {
    mkdirSync(dirPath, { recursive: true });
  }
}

// ============================================
// Notes Handlers
// ============================================

/**
 * Load notes from global scratchpad file
 */
function handleLoadNotes(): IPCResult<string> {
  try {
    const notesPath = getNotesPath();
    const autoClaudeDir = path.dirname(notesPath);

    // Ensure directory exists
    ensureDir(autoClaudeDir);

    // Create empty file if it doesn't exist
    if (!existsSync(notesPath)) {
      writeFileSync(notesPath, '', 'utf-8');
      return { success: true, data: '' };
    }

    const content = readFileSync(notesPath, 'utf-8');
    return { success: true, data: content };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to load notes'
    };
  }
}

/**
 * Save notes to global scratchpad file
 */
function handleSaveNotes(request: SaveNotesRequest): IPCResult<void> {
  try {
    const notesPath = getNotesPath();
    const autoClaudeDir = path.dirname(notesPath);

    // Ensure directory exists
    ensureDir(autoClaudeDir);

    // Atomic write: write to temp file first, then rename
    const tempPath = `${notesPath}.tmp`;
    writeFileSync(tempPath, request.content, 'utf-8');

    // Rename temp file to actual file (atomic on POSIX systems)
    if (existsSync(notesPath)) {
      unlinkSync(notesPath);
    }
    writeFileSync(notesPath, request.content, 'utf-8');

    // Clean up temp file
    if (existsSync(tempPath)) {
      unlinkSync(tempPath);
    }

    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to save notes'
    };
  }
}

// ============================================
// Snippets Handlers
// ============================================

/**
 * List all snippets in a project
 */
function handleListSnippets(request: ListSnippetsRequest): IPCResult<SnippetListItem[]> {
  try {
    const snippetsDir = getSnippetsDir(request.projectPath);

    if (!existsSync(snippetsDir)) {
      return { success: true, data: [] };
    }

    const files = readdirSync(snippetsDir);
    const snippets: SnippetListItem[] = [];

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const filePath = path.join(snippetsDir, file);
      const stats = statSync(filePath);
      const content = readFileSync(filePath, 'utf-8');
      const name = file.replace(/\.md$/, '');

      snippets.push({
        name,
        preview: generatePreview(content, 150),
        createdAt: stats.birthtime,
        updatedAt: stats.mtime
      });
    }

    // Sort by updated date (newest first)
    snippets.sort((a, b) => b.updatedAt.getTime() - a.updatedAt.getTime());

    return { success: true, data: snippets };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list snippets'
    };
  }
}

/**
 * Create a new snippet
 */
function handleCreateSnippet(request: CreateSnippetRequest): IPCResult<void> {
  try {
    if (!request.name || !request.name.trim()) {
      return { success: false, error: 'Snippet name cannot be empty' };
    }

    const snippetsDir = getSnippetsDir(request.projectPath);
    ensureDir(snippetsDir);

    const filename = `${sanitizeFilename(request.name)}.md`;
    const filePath = path.join(snippetsDir, filename);

    if (existsSync(filePath)) {
      return { success: false, error: 'A snippet with this name already exists' };
    }

    writeFileSync(filePath, request.content, 'utf-8');
    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create snippet'
    };
  }
}

/**
 * Get a snippet by name
 */
function handleGetSnippet(request: GetSnippetRequest): IPCResult<Snippet> {
  try {
    const snippetsDir = getSnippetsDir(request.projectPath);
    const filename = `${sanitizeFilename(request.name)}.md`;
    const filePath = path.join(snippetsDir, filename);

    if (!existsSync(filePath)) {
      return { success: false, error: 'Snippet not found' };
    }

    const stats = statSync(filePath);
    const content = readFileSync(filePath, 'utf-8');

    const snippet: Snippet = {
      name: request.name,
      content,
      preview: generatePreview(content, 150),
      createdAt: stats.birthtime,
      updatedAt: stats.mtime
    };

    return { success: true, data: snippet };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get snippet'
    };
  }
}

/**
 * Delete a snippet
 */
function handleDeleteSnippet(request: DeleteSnippetRequest): IPCResult<void> {
  try {
    const snippetsDir = getSnippetsDir(request.projectPath);
    const filename = `${sanitizeFilename(request.name)}.md`;
    const filePath = path.join(snippetsDir, filename);

    if (!existsSync(filePath)) {
      return { success: false, error: 'Snippet not found' };
    }

    unlinkSync(filePath);
    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete snippet'
    };
  }
}

// ============================================
// Templates Handlers
// ============================================

/**
 * List all templates (system + user templates)
 */
function handleListTemplates(request: ListTemplatesRequest): IPCResult<TemplateListItem[]> {
  try {
    const templates: TemplateListItem[] = [];

    // Load system templates
    const systemTemplates = loadSystemTemplates();
    for (const tpl of systemTemplates) {
      templates.push({
        id: tpl.id,
        name: tpl.name,
        description: tpl.description,
        category: tpl.category,
        trigger: tpl.trigger,
        isSystem: true
      });
    }

    // Load user templates from project
    const templatesDir = getTemplatesDir(request.projectPath);
    if (existsSync(templatesDir)) {
      const files = readdirSync(templatesDir);

      for (const file of files) {
        if (!file.endsWith('.md')) continue;

        const filePath = path.join(templatesDir, file);
        try {
          const content = readFileSync(filePath, 'utf-8');

          // Parse frontmatter (simple parsing)
          const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
          if (!frontmatterMatch) continue;

          const frontmatter = frontmatterMatch[1];
          const lines = frontmatter.split('\n');
          const metadata: Record<string, string> = {};

          for (const line of lines) {
            const match = line.match(/^(\w+):\s*(.+)$/);
            if (match) {
              metadata[match[1]] = match[2].trim();
            }
          }

          templates.push({
            id: metadata.id || file.replace(/\.md$/, ''),
            name: metadata.name || file.replace(/\.md$/, ''),
            description: metadata.description || '',
            category: (metadata.category as any) || 'custom',
            trigger: metadata.trigger || '',
            isSystem: false
          });
        } catch (err) {
          console.warn(`Failed to parse template ${file}:`, err);
        }
      }
    }

    return { success: true, data: templates };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to list templates'
    };
  }
}

/**
 * Create a new template
 */
function handleCreateTemplate(request: CreateTemplateRequest): IPCResult<void> {
  try {
    if (!request.name || !request.name.trim()) {
      return { success: false, error: 'Template name cannot be empty' };
    }

    if (!isValidTrigger(request.trigger)) {
      return { success: false, error: 'Invalid trigger format. Use /[a-z0-9-]+' };
    }

    const templatesDir = getTemplatesDir(request.projectPath);
    ensureDir(templatesDir);

    const filename = `${sanitizeFilename(request.name)}.md`;
    const filePath = path.join(templatesDir, filename);

    if (existsSync(filePath)) {
      return { success: false, error: 'A template with this name already exists' };
    }

    // Check trigger uniqueness
    const existing = handleListTemplates({ projectPath: request.projectPath });
    if (existing.success && existing.data) {
      const duplicate = existing.data.find(t => t.trigger === request.trigger);
      if (duplicate) {
        return { success: false, error: `Trigger ${request.trigger} is already used by "${duplicate.name}"` };
      }
    }

    const id = `tmpl_user_${Date.now()}`;
    const now = new Date().toISOString();

    const fileContent = `---
id: ${id}
name: ${request.name}
description: ${request.description}
category: ${request.category}
trigger: ${request.trigger}
createdAt: ${now}
updatedAt: ${now}
---

${request.content}`;

    writeFileSync(filePath, fileContent, 'utf-8');
    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to create template'
    };
  }
}

/**
 * Update an existing template
 */
function handleUpdateTemplate(request: UpdateTemplateRequest): IPCResult<void> {
  try {
    // Check if it's a system template
    const systemTemplate = getSystemTemplateById(request.id);
    if (systemTemplate) {
      return { success: false, error: 'Cannot modify system templates. Clone it first.' };
    }

    if (!isValidTrigger(request.trigger)) {
      return { success: false, error: 'Invalid trigger format. Use /[a-z0-9-]+' };
    }

    const templatesDir = getTemplatesDir(request.projectPath);

    // Find the template file by ID
    const files = readdirSync(templatesDir);
    let targetFile: string | null = null;

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const filePath = path.join(templatesDir, file);
      const content = readFileSync(filePath, 'utf-8');
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

      if (frontmatterMatch) {
        const idMatch = frontmatterMatch[1].match(/^id:\s*(.+)$/m);
        if (idMatch && idMatch[1].trim() === request.id) {
          targetFile = filePath;
          break;
        }
      }
    }

    if (!targetFile) {
      return { success: false, error: 'Template not found' };
    }

    // Check trigger uniqueness (excluding current template)
    const existing = handleListTemplates({ projectPath: request.projectPath });
    if (existing.success && existing.data) {
      const duplicate = existing.data.find(
        t => t.trigger === request.trigger && t.id !== request.id
      );
      if (duplicate) {
        return { success: false, error: `Trigger ${request.trigger} is already used by "${duplicate.name}"` };
      }
    }

    // Read original to get createdAt
    const original = readFileSync(targetFile, 'utf-8');
    const createdAtMatch = original.match(/^createdAt:\s*(.+)$/m);
    const createdAt = createdAtMatch ? createdAtMatch[1].trim() : new Date().toISOString();

    const fileContent = `---
id: ${request.id}
name: ${request.name}
description: ${request.description}
category: ${request.category}
trigger: ${request.trigger}
createdAt: ${createdAt}
updatedAt: ${new Date().toISOString()}
---

${request.content}`;

    writeFileSync(targetFile, fileContent, 'utf-8');
    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to update template'
    };
  }
}

/**
 * Delete a template
 */
function handleDeleteTemplate(request: DeleteTemplateRequest): IPCResult<void> {
  try {
    // Check if it's a system template
    const systemTemplate = getSystemTemplateById(request.id);
    if (systemTemplate) {
      return { success: false, error: 'Cannot delete system templates' };
    }

    const templatesDir = getTemplatesDir(request.projectPath);

    // Find the template file by ID
    const files = readdirSync(templatesDir);
    let targetFile: string | null = null;

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const filePath = path.join(templatesDir, file);
      const content = readFileSync(filePath, 'utf-8');
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);

      if (frontmatterMatch) {
        const idMatch = frontmatterMatch[1].match(/^id:\s*(.+)$/m);
        if (idMatch && idMatch[1].trim() === request.id) {
          targetFile = filePath;
          break;
        }
      }
    }

    if (!targetFile) {
      return { success: false, error: 'Template not found' };
    }

    unlinkSync(targetFile);
    return { success: true, data: undefined };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to delete template'
    };
  }
}

/**
 * Clone a system template to user template
 */
function handleCloneTemplate(request: CloneTemplateRequest): IPCResult<void> {
  try {
    const systemTemplate = getSystemTemplateById(request.sourceId);
    if (!systemTemplate) {
      return { success: false, error: 'System template not found' };
    }

    if (!isValidTrigger(request.newTrigger)) {
      return { success: false, error: 'Invalid trigger format. Use /[a-z0-9-]+' };
    }

    // Check trigger uniqueness
    const existing = handleListTemplates({ projectPath: request.projectPath });
    if (existing.success && existing.data) {
      const duplicate = existing.data.find(t => t.trigger === request.newTrigger);
      if (duplicate) {
        return { success: false, error: `Trigger ${request.newTrigger} is already used by "${duplicate.name}"` };
      }
    }

    const newName = request.newName || `${systemTemplate.name} (Copy)`;
    const newDescription = request.newDescription || systemTemplate.description;

    return handleCreateTemplate({
      projectPath: request.projectPath,
      name: newName,
      description: newDescription,
      category: systemTemplate.category,
      trigger: request.newTrigger,
      content: systemTemplate.content
    });
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to clone template'
    };
  }
}

/**
 * Get a template by ID
 */
function handleGetTemplate(request: GetTemplateRequest): IPCResult<FileTemplate> {
  try {
    // Check system templates first
    const systemTemplate = getSystemTemplateById(request.id);
    if (systemTemplate) {
      const fileTemplate: FileTemplate = {
        id: systemTemplate.id,
        name: systemTemplate.name,
        description: systemTemplate.description,
        category: systemTemplate.category,
        trigger: systemTemplate.trigger,
        content: systemTemplate.content,
        isSystem: true,
        createdAt: new Date(systemTemplate.createdAt),
        updatedAt: new Date(systemTemplate.updatedAt)
      };
      return { success: true, data: fileTemplate };
    }

    // Check user templates
    const templatesDir = getTemplatesDir(request.projectPath);
    const files = readdirSync(templatesDir);

    for (const file of files) {
      if (!file.endsWith('.md')) continue;

      const filePath = path.join(templatesDir, file);
      const content = readFileSync(filePath, 'utf-8');
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);

      if (!frontmatterMatch) continue;

      const frontmatter = frontmatterMatch[1];
      const templateContent = frontmatterMatch[2];
      const lines = frontmatter.split('\n');
      const metadata: Record<string, string> = {};

      for (const line of lines) {
        const match = line.match(/^(\w+):\s*(.+)$/);
        if (match) {
          metadata[match[1]] = match[2].trim();
        }
      }

      if (metadata.id === request.id) {
        const fileTemplate: FileTemplate = {
          id: metadata.id,
          name: metadata.name || '',
          description: metadata.description || '',
          category: (metadata.category as any) || 'custom',
          trigger: metadata.trigger || '',
          content: templateContent,
          isSystem: false,
          createdAt: new Date(metadata.createdAt || Date.now()),
          updatedAt: new Date(metadata.updatedAt || Date.now())
        };
        return { success: true, data: fileTemplate };
      }
    }

    return { success: false, error: 'Template not found' };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to get template'
    };
  }
}

// ============================================
// Register All Handlers
// ============================================

/**
 * Register all ScratchPad IPC handlers
 */
export function registerScratchpadHandlers(): void {
  // Initialize system templates on startup
  initializeSystemTemplates();

  // Notes handlers
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_NOTES_LOAD, () => handleLoadNotes());
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_NOTES_SAVE, (_, request: SaveNotesRequest) =>
    handleSaveNotes(request)
  );

  // Snippets handlers
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_LIST, (_, request: ListSnippetsRequest) =>
    handleListSnippets(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_CREATE, (_, request: CreateSnippetRequest) =>
    handleCreateSnippet(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_GET, (_, request: GetSnippetRequest) =>
    handleGetSnippet(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_DELETE, (_, request: DeleteSnippetRequest) =>
    handleDeleteSnippet(request)
  );

  // Templates handlers
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_LIST, (_, request: ListTemplatesRequest) =>
    handleListTemplates(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_CREATE, (_, request: CreateTemplateRequest) =>
    handleCreateTemplate(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_UPDATE, (_, request: UpdateTemplateRequest) =>
    handleUpdateTemplate(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_DELETE, (_, request: DeleteTemplateRequest) =>
    handleDeleteTemplate(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_CLONE, (_, request: CloneTemplateRequest) =>
    handleCloneTemplate(request)
  );
  ipcMain.handle(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_GET, (_, request: GetTemplateRequest) =>
    handleGetTemplate(request)
  );

  console.log('[ScratchPad] IPC handlers registered');
}
