/**
 * Documentation Generation Types
 */

/**
 * Type of documentation that can be generated
 */
export type DocumentationType =
  | 'docstring'      // Function/class docstring
  | 'jsdoc'          // JSDoc comment
  | 'readme'         // README section
  | 'changelog'      // Changelog entry
  | 'api-docs';      // API documentation

/**
 * Programming language for documentation
 */
export type DocumentationLanguage = 'python' | 'typescript' | 'javascript' | 'markdown';

/**
 * Status of documentation generation
 */
export type DocumentationStatus =
  | 'pending'        // Queued for generation
  | 'generating'     // AI is generating
  | 'generated'      // Generated but not reviewed
  | 'edited'         // User has edited the generated docs
  | 'applied'        // Applied to the file
  | 'error';         // Generation failed

/**
 * Target for documentation (what is being documented)
 */
export interface DocumentationTarget {
  /** File path relative to project root */
  filePath: string;
  /** Function or class name being documented */
  name: string;
  /** Line number in the file */
  lineNumber?: number;
  /** Existing documentation if any */
  existingDoc?: string;
}

/**
 * Generated documentation item
 */
export interface DocumentationItem {
  /** Unique identifier */
  id: string;
  /** Type of documentation */
  type: DocumentationType;
  /** Programming language */
  language: DocumentationLanguage;
  /** Status of generation */
  status: DocumentationStatus;
  /** What is being documented */
  target: DocumentationTarget;
  /** AI-generated documentation content */
  generatedContent: string;
  /** User-edited content (if edited) */
  editedContent?: string;
  /** Error message if generation failed */
  error?: string;
  /** When this was created */
  createdAt: Date;
  /** When this was last updated */
  updatedAt: Date;
}

/**
 * Documentation generation request
 */
export interface DocumentationGenerationRequest {
  /** Type of documentation to generate */
  type: DocumentationType;
  /** File path to document */
  filePath: string;
  /** Target name (function/class) */
  targetName?: string;
  /** Line number if applicable */
  lineNumber?: number;
  /** Additional context for generation */
  context?: string;
}

/**
 * Documentation generation result
 */
export interface DocumentationGenerationResult {
  /** Whether generation succeeded */
  success: boolean;
  /** Generated documentation if successful */
  content?: string;
  /** Error message if failed */
  error?: string;
}

/**
 * Documentation validation result
 */
export interface DocumentationValidationResult {
  /** Whether documentation is valid */
  valid: boolean;
  /** Validation issues found */
  issues: string[];
  /** Suggestions for improvement */
  suggestions?: string[];
}
