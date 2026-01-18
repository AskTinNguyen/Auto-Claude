# Ralph CLI ↔ Kanban Real-Time Synchronization

**How tasks triggered or modified by Ralph CLI get visually updated in the Electron App's Kanban board.**

---

## Architecture Overview

The synchronization between Ralph CLI and the Kanban UI uses a **file-watching + IPC event** architecture:

```
Ralph CLI modifies files
         ↓
File System (.auto-claude/specs/*/implementation_plan.json)
         ↓
Chokidar FileWatcher (Main Process)
         ↓
IPC Events (Main → Renderer)
         ↓
Batched Updates (useIpc hook)
         ↓
Zustand Task Store
         ↓
React Re-render (Kanban UI updates)
```

**Key Principle:** The Electron app watches spec files on disk. When Ralph CLI modifies them, the UI updates automatically within ~300ms.

---

## Component Breakdown

### 1. File Watcher (Main Process)

**Location:** `apps/frontend/src/main/file-watcher.ts`

**Purpose:** Watch `implementation_plan.json` files for changes using chokidar.

```typescript
export class FileWatcher extends EventEmitter {
  private watchers: Map<string, WatcherInfo> = new Map();

  async watch(taskId: string, specDir: string): Promise<void> {
    const planPath = path.join(specDir, 'implementation_plan.json');

    // Create watcher with debouncing
    const watcher = chokidar.watch(planPath, {
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 300,  // Wait 300ms after last write
        pollInterval: 100         // Poll every 100ms
      }
    });

    // Emit 'progress' event when file changes
    watcher.on('change', () => {
      const content = readFileSync(planPath, 'utf-8');
      const plan: ImplementationPlan = JSON.parse(content);
      this.emit('progress', taskId, plan);  // → Triggers IPC event
    });

    this.watchers.set(taskId, { taskId, watcher, planPath });
  }
}
```

**Key Features:**
- **Debouncing:** Waits 300ms after last write to avoid partial reads
- **Singleton:** One global `fileWatcher` instance shared across all tasks
- **EventEmitter:** Emits `progress` events that trigger IPC messages

### 2. IPC Event Bridge (Main Process)

**Location:** `apps/frontend/src/main/ipc-handlers/agent-events-handlers.ts`

**Purpose:** Forward file change events to the renderer process.

```typescript
export function registerAgenteventsHandlers(
  agentManager: AgentManager,
  getMainWindow: () => BrowserWindow | null
): void {
  // Listen to FileWatcher events
  fileWatcher.on("progress", (taskId: string, plan: ImplementationPlan) => {
    const { project } = findTaskAndProject(taskId);

    // Send IPC message to renderer
    safeSendToRenderer(
      getMainWindow,
      IPC_CHANNELS.TASK_PROGRESS,  // 'task:progress'
      taskId,
      plan,
      project?.id
    );
  });

  fileWatcher.on("error", (taskId: string, error: string) => {
    const { project } = findTaskAndProject(taskId);
    safeSendToRenderer(
      getMainWindow,
      IPC_CHANNELS.TASK_ERROR,
      taskId,
      error,
      project?.id
    );
  });
}
```

**IPC Channels:**
- `task:progress` - Plan/subtask updates
- `task:error` - Error notifications
- `task:status` - Status changes
- `task:log` - Log line appends

### 3. Preload API (Preload Script)

**Location:** `apps/frontend/src/preload/api/task-api.ts`

**Purpose:** Expose IPC listeners to the renderer process.

```typescript
export const createTaskAPI = (): TaskAPI => ({
  // ... other methods ...

  onTaskProgress: (
    callback: (taskId: string, plan: ImplementationPlan, projectId?: string) => void
  ): (() => void) => {
    const handler = (
      _event: IpcRendererEvent,
      taskId: string,
      plan: ImplementationPlan,
      projectId?: string
    ): void => {
      callback(taskId, plan, projectId);
    };

    ipcRenderer.on(IPC_CHANNELS.TASK_PROGRESS, handler);

    // Return cleanup function
    return () => {
      ipcRenderer.removeListener(IPC_CHANNELS.TASK_PROGRESS, handler);
    };
  },

  onTaskError: (
    callback: (taskId: string, error: string, projectId?: string) => void
  ): (() => void) => {
    // Similar pattern for error events
    // ...
  }
});
```

**Exposed via:** `window.electronAPI.onTaskProgress(...)`

### 4. IPC Hook (Renderer Process)

**Location:** `apps/frontend/src/renderer/hooks/useIpc.ts`

**Purpose:** Listen to IPC events and batch updates to prevent excessive re-renders.

```typescript
export function useIpc(): void {
  const { updateTaskFromPlan, updateTaskStatus, updateExecutionProgress, batchAppendLogs } = useTaskStore();

  useEffect(() => {
    // Listen for plan updates from file watcher
    const cleanupProgress = window.electronAPI.onTaskProgress(
      (taskId: string, plan: ImplementationPlan, projectId?: string) => {
        // Filter by current project
        if (!isTaskForCurrentProject(projectId)) return;

        // Queue update (batched to prevent excessive re-renders)
        queueUpdate(taskId, { plan });
      }
    );

    const cleanupStatus = window.electronAPI.onTaskStatusChange(
      (taskId: string, status: TaskStatus, projectId?: string) => {
        if (!isTaskForCurrentProject(projectId)) return;
        queueUpdate(taskId, { status });
      }
    );

    const cleanupLog = window.electronAPI.onTaskLog(
      (taskId: string, log: string, projectId?: string) => {
        if (!isTaskForCurrentProject(projectId)) return;
        queueUpdate(taskId, { logs: [log] });
      }
    );

    // Cleanup on unmount
    return () => {
      cleanupProgress();
      cleanupStatus();
      cleanupLog();
    };
  }, []);
}
```

**Batching Mechanism:**

```typescript
// Batch queue collects updates within 16ms window (one frame)
const batchQueue = new Map<string, BatchedUpdate>();
let batchTimeout: NodeJS.Timeout | null = null;

function queueUpdate(taskId: string, update: BatchedUpdate): void {
  const existing = batchQueue.get(taskId) || {};

  // Merge updates (accumulate logs, overwrite status/progress)
  batchQueue.set(taskId, {
    status: update.status || existing.status,
    progress: update.progress || existing.progress,
    plan: update.plan || existing.plan,
    logs: [...(existing.logs || []), ...(update.logs || [])]
  });

  // Schedule flush in 16ms if not already scheduled
  if (!batchTimeout) {
    batchTimeout = setTimeout(flushBatch, 16);
  }
}

function flushBatch(): void {
  // Apply all queued updates in one React batch
  unstable_batchedUpdates(() => {
    batchQueue.forEach((updates, taskId) => {
      if (updates.plan) {
        updateTaskFromPlan(taskId, updates.plan);
      }
      if (updates.status) {
        updateTaskStatus(taskId, updates.status);
      }
      if (updates.logs?.length > 0) {
        batchAppendLogs(taskId, updates.logs);
      }
    });
  });

  batchQueue.clear();
  batchTimeout = null;
}
```

**Why Batching?**
- Auto-Claude agents can generate 100+ log lines per second
- Without batching: 100+ React re-renders per second = UI freezes
- With batching: Updates grouped into 1 re-render per 16ms = smooth 60fps

### 5. Task Store (Renderer Process)

**Location:** `apps/frontend/src/renderer/stores/task-store.ts`

**Purpose:** Zustand store that holds task state and triggers React re-renders.

```typescript
export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  selectedTaskId: null,

  // Called when implementation_plan.json changes
  updateTaskFromPlan: (taskId: string, plan: ImplementationPlan) => {
    const tasks = get().tasks;
    const index = findTaskIndex(tasks, taskId);

    if (index === -1) return; // Task not found

    // Update task with new plan data
    const updatedTask = {
      ...tasks[index],
      implementationPlan: plan,
      // Update status based on plan completion
      status: calculateStatusFromPlan(plan),
      totalSubtasks: plan.totalSubtasks,
      completedSubtasks: plan.completedSubtasks
    };

    const newTasks = [...tasks];
    newTasks[index] = updatedTask;

    set({ tasks: newTasks });  // → Triggers React re-render
  },

  updateTaskStatus: (taskId: string, status: TaskStatus) => {
    // Similar pattern...
  }
}));
```

### 6. Kanban UI (Renderer Process)

**Location:** `apps/frontend/src/renderer/components/KanbanBoard.tsx`

**Purpose:** React component that displays tasks from the store.

```typescript
export function KanbanBoard() {
  // Subscribe to task store (re-renders when tasks change)
  const tasks = useTaskStore((state) => state.tasks);

  // Group tasks by status for columns
  const tasksByStatus = useMemo(() => {
    return {
      spec_creation: tasks.filter(t => t.status === 'spec_creation'),
      planning: tasks.filter(t => t.status === 'planning'),
      coding: tasks.filter(t => t.status === 'coding'),
      qa_review: tasks.filter(t => t.status === 'qa_review'),
      complete: tasks.filter(t => t.status === 'complete')
    };
  }, [tasks]);

  return (
    <div className="kanban-board">
      <KanbanColumn status="spec_creation" tasks={tasksByStatus.spec_creation} />
      <KanbanColumn status="planning" tasks={tasksByStatus.planning} />
      <KanbanColumn status="coding" tasks={tasksByStatus.coding} />
      <KanbanColumn status="qa_review" tasks={tasksByStatus.qa_review} />
      <KanbanColumn status="complete" tasks={tasksByStatus.complete} />
    </div>
  );
}
```

**When store updates → Kanban re-renders automatically** (Zustand reactivity)

---

## Workflow Example: Ralph CLI Modifies Spec

### Scenario: User runs `ralph stream build 001-feature` in terminal

```bash
# Terminal 1: User runs Ralph build
$ ralph stream build 001-feature
Building spec: 001-feature
Running planner agent...
```

**Step 1: Auto-Claude Planner Creates Plan**
```python
# In planner.py
def create_implementation_plan(spec_dir):
    plan = {
        "phases": [
            {
                "phase": "planning",
                "subtasks": [
                    {"id": 1, "description": "Analyze requirements", "status": "pending"},
                    {"id": 2, "description": "Design architecture", "status": "pending"}
                ]
            }
        ],
        "totalSubtasks": 2,
        "completedSubtasks": 0
    }

    # Write to disk
    with open(f"{spec_dir}/implementation_plan.json", "w") as f:
        json.dump(plan, f, indent=2)
```

**File written:** `.auto-claude/specs/001-feature/implementation_plan.json`

**Step 2: FileWatcher Detects Change (Main Process)**
```
[FileWatcher] File changed: .auto-claude/specs/001-feature/implementation_plan.json
[FileWatcher] Waiting 300ms for write to stabilize...
[FileWatcher] Emitting 'progress' event for task 001-feature
```

**Step 3: IPC Event Sent to Renderer**
```typescript
// In agent-events-handlers.ts
fileWatcher.on('progress', (taskId, plan) => {
  // taskId = '001-feature'
  // plan = { phases: [...], totalSubtasks: 2, completedSubtasks: 0 }

  safeSendToRenderer(
    getMainWindow,
    'task:progress',
    '001-feature',
    plan,
    'project-123'
  );
});
```

**Step 4: Renderer Receives Event (Batched)**
```typescript
// In useIpc.ts
window.electronAPI.onTaskProgress((taskId, plan, projectId) => {
  // Filter: Only update if task belongs to current project
  if (projectId === currentProjectId) {
    queueUpdate('001-feature', { plan });
    // Will flush in 16ms or next event, whichever comes first
  }
});
```

**Step 5: Store Updates (After Batch Flush)**
```typescript
// In task-store.ts
updateTaskFromPlan('001-feature', plan);
// → Finds task in tasks array
// → Updates task.implementationPlan = plan
// → Updates task.totalSubtasks = 2
// → Updates task.completedSubtasks = 0
// → Triggers re-render
```

**Step 6: Kanban UI Re-renders**
```
┌─────────────────┬─────────────────┬─────────────────┐
│  Spec Creation  │    Planning     │     Coding      │
├─────────────────┼─────────────────┼─────────────────┤
│                 │ □ 001-feature   │                 │  ← Card moves here!
│                 │   0/2 subtasks  │                 │  ← Subtask count appears!
│                 │   In progress   │                 │  ← Badge updates!
└─────────────────┴─────────────────┴─────────────────┘
```

**Step 7: Coder Agent Completes Subtasks**
```python
# In coder.py
def complete_subtask(spec_dir, subtask_id):
    plan = json.load(open(f"{spec_dir}/implementation_plan.json"))

    # Update subtask status
    for phase in plan["phases"]:
        for subtask in phase["subtasks"]:
            if subtask["id"] == subtask_id:
                subtask["status"] = "completed"  # ← Change here

    # Update counts
    plan["completedSubtasks"] += 1  # 0 → 1

    # Write back to disk
    json.dump(plan, open(f"{spec_dir}/implementation_plan.json", "w"), indent=2)
```

**File written again** → FileWatcher detects → IPC event → UI updates to "1/2 subtasks"

**Step 8: All Subtasks Complete**
```python
# After coder completes all subtasks
plan["completedSubtasks"] = 2  # All done!
json.dump(plan, open(f"{spec_dir}/implementation_plan.json", "w"), indent=2)
```

**FileWatcher detects → IPC → Store calculates new status:**
```typescript
function calculateStatusFromPlan(plan: ImplementationPlan): TaskStatus {
  if (plan.completedSubtasks === plan.totalSubtasks) {
    return 'qa_review';  // Move to QA column!
  }
  return 'coding';
}
```

**Step 9: Kanban Auto-Updates Again**
```
┌─────────────────┬─────────────────┬─────────────────┐
│     Coding      │   QA Review     │    Complete     │
├─────────────────┼─────────────────┼─────────────────┤
│                 │ □ 001-feature   │                 │  ← Card moves to QA!
│                 │   2/2 subtasks  │                 │  ← Shows complete!
│                 │   ✓ Ready for QA│                 │  ← Badge changes!
└─────────────────┴─────────────────┴─────────────────┘
```

---

## Timing & Performance

### Update Latency

```
Ralph writes file → FileWatcher detects → IPC event → Batched update → UI re-render
     ~0ms                ~300ms             ~1ms         ~16ms         ~5ms

Total: ~322ms from file write to visual update
```

**Why 300ms?**
- FileWatcher waits for file write to stabilize
- Prevents reading partial/corrupt JSON mid-write
- Configurable via `awaitWriteFinish.stabilityThreshold`

### Batching Performance

**Without batching (before optimization):**
```
100 log events in 1 second
→ 100 IPC messages
→ 100 store updates
→ 100 React re-renders
→ UI freezes, drops to ~10fps
```

**With batching (current implementation):**
```
100 log events in 1 second
→ 100 IPC messages (still fast, no bottleneck)
→ ~60 batched store updates (16ms intervals)
→ ~60 React re-renders
→ Smooth 60fps
```

### Multi-Project Filtering

**Problem:** Opening multiple projects could cause cross-project updates.

**Solution:** Filter by `projectId` in IPC listeners:
```typescript
window.electronAPI.onTaskProgress((taskId, plan, projectId) => {
  // Only update if task belongs to current project
  if (projectId !== currentProjectId) return;

  queueUpdate(taskId, { plan });
});
```

---

## Initial Load vs. Real-Time Updates

### Initial Load (Project Switch)

When switching projects, tasks are loaded via IPC call (not file watching):

```typescript
// In App.tsx
useEffect(() => {
  if (currentProjectId) {
    loadTasks(currentProjectId);  // ← Explicit load via IPC
  }
}, [currentProjectId]);

// In task-store.ts
export async function loadTasks(projectId: string): Promise<void> {
  // IPC call to main process to read all spec files
  const result = await window.electronAPI.getTasksForProject(projectId);

  if (result.success) {
    useTaskStore.getState().setTasks(result.data);
  }
}
```

**Flow:**
1. User switches project in UI
2. `loadTasks(projectId)` called
3. Main process reads all `.auto-claude/specs/*/` directories
4. Returns array of tasks with latest data
5. Store sets all tasks at once
6. Kanban renders with full data

### Real-Time Updates (During Build)

After initial load, FileWatcher provides real-time updates:

```typescript
// When task starts building
window.electronAPI.startTask(taskId);
// → Main process: fileWatcher.watch(taskId, specDir)
// → Now watching implementation_plan.json for changes

// Agent modifies file → FileWatcher detects → IPC event → Store updates → UI updates
// ... build continues with live updates ...

// When task completes
window.electronAPI.stopTask(taskId);
// → Main process: fileWatcher.unwatch(taskId)
// → Stop watching (cleanup)
```

---

## Manual Refresh

Users can also manually refresh tasks via "Refresh" button:

```typescript
// In KanbanBoard.tsx
const handleRefresh = async () => {
  if (!currentProjectId) return;

  setIsRefreshing(true);
  try {
    await loadTasks(currentProjectId);  // Re-read all specs from disk
  } finally {
    setIsRefreshing(false);
  }
};
```

**When to use:**
- External changes (e.g., user manually edits spec files)
- Ralph CLI ran without app open
- Suspected stale data

---

## Summary: The Complete Flow

### Ralph CLI → Kanban Update Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Ralph CLI modifies file                                     │
│    ralph stream build 001-feature                              │
│    → Auto-Claude agents write to implementation_plan.json      │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. FileSystem                                                   │
│    .auto-claude/specs/001-feature/implementation_plan.json     │
│    { "completedSubtasks": 1, "totalSubtasks": 5, ... }         │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. FileWatcher (Main Process)                                  │
│    chokidar detects change after 300ms stabilization           │
│    fileWatcher.emit('progress', taskId, plan)                  │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. IPC Bridge (Main Process)                                   │
│    agent-events-handlers.ts listens to 'progress' event        │
│    safeSendToRenderer('task:progress', taskId, plan, projectId)│
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Preload API (Preload Script)                                │
│    window.electronAPI.onTaskProgress() receives IPC message    │
│    Calls registered callback with (taskId, plan, projectId)    │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. useIpc Hook (Renderer Process)                              │
│    Filters by projectId (ignore other projects)                │
│    queueUpdate(taskId, { plan }) → batched                     │
│    Scheduled flush in 16ms                                      │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Batch Flush (Renderer Process)                              │
│    After 16ms, flushBatch() called                             │
│    unstable_batchedUpdates(() => { updateTaskFromPlan() })     │
│    Single React render for all queued updates                  │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. Task Store (Renderer Process)                               │
│    useTaskStore updates task in tasks array                    │
│    task.implementationPlan = newPlan                           │
│    task.completedSubtasks = 1                                  │
│    Triggers Zustand subscription                               │
└───────────────────────┬─────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. Kanban UI (Renderer Process)                                │
│    const tasks = useTaskStore(state => state.tasks)            │
│    React re-renders KanbanBoard                                │
│    TaskCard shows "1/5 subtasks complete"                      │
│    Visual update appears!                                       │
└─────────────────────────────────────────────────────────────────┘
```

**Total latency: ~322ms** (mostly FileWatcher stabilization)

---

## Key Takeaways

1. **File-Based Sync:** No database, no polling - just file watching + IPC events
2. **Real-Time Updates:** UI updates within ~322ms of file changes
3. **Batched Rendering:** Prevents UI freezes during high-frequency updates
4. **Project Isolation:** Multi-project filtering prevents cross-contamination
5. **Hybrid Approach:** Initial load via IPC call, then file watching for updates
6. **Automatic Cleanup:** Watchers stopped when tasks complete to save resources

The Kanban board is **always in sync** with the file system - whether changes come from the UI, Ralph CLI, or manual file edits.
