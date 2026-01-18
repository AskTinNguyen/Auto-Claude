/**
 * ScratchPad API (Preload)
 *
 * Exposes ScratchPad operations to the renderer process
 */

import { ipcRenderer } from 'electron';
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
  ListTemplatesRequest
} from '../../shared/types';

export interface ScratchPadAPI {
  // Notes operations
  loadNotes: () => Promise<IPCResult<string>>;
  saveNotes: (content: string) => Promise<IPCResult<void>>;

  // Snippets operations
  listSnippets: (projectPath: string) => Promise<IPCResult<SnippetListItem[]>>;
  createSnippet: (projectPath: string, name: string, content: string) => Promise<IPCResult<void>>;
  getSnippet: (projectPath: string, name: string) => Promise<IPCResult<Snippet>>;
  deleteSnippet: (projectPath: string, name: string) => Promise<IPCResult<void>>;

  // Templates operations
  listTemplates: (projectPath: string) => Promise<IPCResult<TemplateListItem[]>>;
  createTemplate: (
    projectPath: string,
    name: string,
    description: string,
    category: import('../../shared/types').TemplateCategory,
    trigger: string,
    content: string
  ) => Promise<IPCResult<void>>;
  updateTemplate: (
    projectPath: string,
    id: string,
    name: string,
    description: string,
    category: import('../../shared/types').TemplateCategory,
    trigger: string,
    content: string
  ) => Promise<IPCResult<void>>;
  deleteTemplate: (projectPath: string, id: string) => Promise<IPCResult<void>>;
  cloneTemplate: (
    projectPath: string,
    sourceId: string,
    newTrigger: string,
    newName?: string,
    newDescription?: string
  ) => Promise<IPCResult<void>>;
  getTemplate: (projectPath: string, id: string) => Promise<IPCResult<FileTemplate>>;
}

export const createScratchPadAPI = (): ScratchPadAPI => ({
  // Notes operations
  loadNotes: (): Promise<IPCResult<string>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_NOTES_LOAD),

  saveNotes: (content: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_NOTES_SAVE, { content } as SaveNotesRequest),

  // Snippets operations
  listSnippets: (projectPath: string): Promise<IPCResult<SnippetListItem[]>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_LIST, { projectPath } as ListSnippetsRequest),

  createSnippet: (projectPath: string, name: string, content: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_CREATE, {
      projectPath,
      name,
      content
    } as CreateSnippetRequest),

  getSnippet: (projectPath: string, name: string): Promise<IPCResult<Snippet>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_GET, { projectPath, name } as GetSnippetRequest),

  deleteSnippet: (projectPath: string, name: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_SNIPPETS_DELETE, { projectPath, name } as DeleteSnippetRequest),

  // Templates operations
  listTemplates: (projectPath: string): Promise<IPCResult<TemplateListItem[]>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_LIST, { projectPath } as ListTemplatesRequest),

  createTemplate: (
    projectPath: string,
    name: string,
    description: string,
    category: import('../../shared/types').TemplateCategory,
    trigger: string,
    content: string
  ): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_CREATE, {
      projectPath,
      name,
      description,
      category,
      trigger,
      content
    } as CreateTemplateRequest),

  updateTemplate: (
    projectPath: string,
    id: string,
    name: string,
    description: string,
    category: import('../../shared/types').TemplateCategory,
    trigger: string,
    content: string
  ): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_UPDATE, {
      projectPath,
      id,
      name,
      description,
      category,
      trigger,
      content
    } as UpdateTemplateRequest),

  deleteTemplate: (projectPath: string, id: string): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_DELETE, {
      projectPath,
      id
    } as DeleteTemplateRequest),

  cloneTemplate: (
    projectPath: string,
    sourceId: string,
    newTrigger: string,
    newName?: string,
    newDescription?: string
  ): Promise<IPCResult<void>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_CLONE, {
      projectPath,
      sourceId,
      newTrigger,
      newName,
      newDescription
    } as CloneTemplateRequest),

  getTemplate: (projectPath: string, id: string): Promise<IPCResult<FileTemplate>> =>
    ipcRenderer.invoke(IPC_CHANNELS.SCRATCHPAD_TEMPLATES_GET, { projectPath, id } as GetTemplateRequest)
});
