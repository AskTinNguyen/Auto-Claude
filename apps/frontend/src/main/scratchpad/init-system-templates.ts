/**
 * System Templates Initialization
 *
 * Initializes default system templates on first launch
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import path from 'path';
import { app } from 'electron';
import type { SystemTemplate } from '../../shared/types';

/**
 * Get the path to system templates JSON file
 */
export function getSystemTemplatesPath(): string {
  const autoClaudeDir = path.join(app.getPath('home'), '.auto-claude');
  return path.join(autoClaudeDir, 'system-templates.json');
}

/**
 * Default system templates
 */
const DEFAULT_SYSTEM_TEMPLATES: SystemTemplate[] = [
  {
    id: 'tmpl_sys_code_review',
    name: 'Code Review',
    description: 'Review code for quality, security, and best practices',
    category: 'review',
    trigger: '/code-review',
    content: `Review the following code for:
- Code quality and maintainability
- Security vulnerabilities
- Performance issues
- Best practices adherence
- Potential bugs

Code to review:

{{input}}

Provide specific, actionable feedback with code examples where appropriate.`,
    isSystem: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'tmpl_sys_refactor',
    name: 'Refactor Suggestions',
    description: 'Suggest refactoring improvements for code',
    category: 'development',
    trigger: '/refactor',
    content: `Analyze the following code and suggest refactoring improvements:

{{input}}

Focus on:
- Code organization and structure
- Removing duplication
- Improving readability
- Applying design patterns
- Modernizing syntax

Provide before/after examples for each suggestion.`,
    isSystem: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'tmpl_sys_planning',
    name: 'Implementation Plan',
    description: 'Create a detailed implementation plan',
    category: 'planning',
    trigger: '/plan',
    content: `Create a detailed implementation plan for:

{{input}}

Include:
1. **Overview** - Brief summary of the feature/task
2. **Requirements** - Key requirements and constraints
3. **Architecture** - High-level architecture and design decisions
4. **Implementation Steps** - Step-by-step breakdown
5. **Testing Strategy** - How to test and validate
6. **Potential Challenges** - Risks and mitigation strategies
7. **Estimated Effort** - Time/complexity estimate`,
    isSystem: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'tmpl_sys_debug',
    name: 'Debug Assistant',
    description: 'Help debug code issues and errors',
    category: 'development',
    trigger: '/debug',
    content: `Help debug the following issue:

{{input}}

Please:
1. Identify potential root causes
2. Suggest debugging steps
3. Provide possible fixes
4. Explain the underlying problem
5. Recommend preventive measures

Be systematic and thorough in your analysis.`,
    isSystem: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  },
  {
    id: 'tmpl_sys_docs',
    name: 'Documentation Generator',
    description: 'Generate comprehensive documentation',
    category: 'development',
    trigger: '/docs',
    content: `Generate comprehensive documentation for:

{{input}}

Include:
- Overview and purpose
- Key features/functionality
- Usage examples
- API reference (if applicable)
- Configuration options
- Common use cases
- Troubleshooting tips

Use clear, concise language with code examples where helpful.`,
    isSystem: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
];

/**
 * Initialize system templates file if it doesn't exist
 */
export function initializeSystemTemplates(): void {
  const templatesPath = getSystemTemplatesPath();
  const autoClaudeDir = path.dirname(templatesPath);

  // Create ~/.auto-claude directory if it doesn't exist
  if (!existsSync(autoClaudeDir)) {
    mkdirSync(autoClaudeDir, { recursive: true });
  }

  // Create system templates file if it doesn't exist
  if (!existsSync(templatesPath)) {
    writeFileSync(
      templatesPath,
      JSON.stringify(DEFAULT_SYSTEM_TEMPLATES, null, 2),
      'utf-8'
    );
    console.log('[ScratchPad] Initialized system templates');
  }
}

/**
 * Load system templates from file
 */
export function loadSystemTemplates(): SystemTemplate[] {
  const templatesPath = getSystemTemplatesPath();

  if (!existsSync(templatesPath)) {
    initializeSystemTemplates();
  }

  try {
    const data = readFileSync(templatesPath, 'utf-8');
    return JSON.parse(data);
  } catch (error) {
    console.error('[ScratchPad] Failed to load system templates:', error);
    return DEFAULT_SYSTEM_TEMPLATES;
  }
}

/**
 * Get a system template by ID
 */
export function getSystemTemplateById(id: string): SystemTemplate | null {
  const templates = loadSystemTemplates();
  return templates.find(t => t.id === id) || null;
}
