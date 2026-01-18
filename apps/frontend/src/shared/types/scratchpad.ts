/**
 * ScratchPad Types
 *
 * Types for Notes, Snippets, and Templates features
 */

// ============================================
// Snippet Types
// ============================================

export interface Snippet {
  name: string;
  content: string;
  createdAt: Date;
  updatedAt: Date;
  preview: string; // First 80-150 chars
}

export interface SnippetListItem {
  name: string;
  preview: string;
  createdAt: Date;
  updatedAt: Date;
}

// ============================================
// Template Types
// ============================================

export type TemplateCategory = 'development' | 'planning' | 'review' | 'custom';

export interface FileTemplate {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  trigger: string; // e.g., "/code-review"
  content: string;
  isSystem: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface SystemTemplate {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  trigger: string;
  content: string;
  isSystem: true;
  createdAt: string; // ISO string for JSON storage
  updatedAt: string;
}

export interface TemplateListItem {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  trigger: string;
  isSystem: boolean;
}

// ============================================
// Request/Response Types
// ============================================

export interface LoadNotesRequest {
  // Notes are global (per user), not per project
}

export interface SaveNotesRequest {
  content: string;
}

export interface ListSnippetsRequest {
  projectPath: string;
}

export interface CreateSnippetRequest {
  projectPath: string;
  name: string;
  content: string;
}

export interface DeleteSnippetRequest {
  projectPath: string;
  name: string;
}

export interface GetSnippetRequest {
  projectPath: string;
  name: string;
}

export interface ListTemplatesRequest {
  projectPath: string;
}

export interface CreateTemplateRequest {
  projectPath: string;
  name: string;
  description: string;
  category: TemplateCategory;
  trigger: string;
  content: string;
  isSystem?: boolean; // Only for internal use when cloning system templates
}

export interface UpdateTemplateRequest {
  projectPath: string;
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  trigger: string;
  content: string;
}

export interface DeleteTemplateRequest {
  projectPath: string;
  id: string;
}

export interface CloneTemplateRequest {
  projectPath: string;
  sourceId: string; // System template ID to clone
  newTrigger: string;
  newName?: string;
  newDescription?: string;
}

export interface GetTemplateRequest {
  projectPath: string;
  id: string;
}

// ============================================
// Utility Types
// ============================================

/**
 * Sanitize filename to be filesystem-safe
 */
export function sanitizeFilename(name: string): string {
  return name.toLowerCase()
    .replace(/[^a-z0-9-_]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Validate trigger format (/[a-z0-9-]+)
 */
export function isValidTrigger(trigger: string): boolean {
  return /^\/[a-z0-9-]+$/.test(trigger);
}

/**
 * Generate preview text (first 80-150 chars)
 */
export function generatePreview(content: string, maxLength: number = 150): string {
  const stripped = content.replace(/\s+/g, ' ').trim();
  if (stripped.length <= maxLength) {
    return stripped;
  }
  return stripped.slice(0, maxLength) + '...';
}
