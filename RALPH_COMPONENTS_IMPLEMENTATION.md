# Ralph Integration - Frontend Components Implementation

This document describes the React/TypeScript components created for Ralph integration features in Auto-Claude.

## Created Components

### 1. QualityScoreCard Component
**Location:** `apps/frontend/src/renderer/components/analytics/QualityScoreCard.tsx`

A comprehensive quality score display component that shows:
- Overall quality score (0-100) and letter grade (A-F)
- Category breakdown with progress bars (Security, Performance, Maintainability, Documentation, Testing)
- List of issues with severity badges (high, medium, low)
- Recommendations for improvement

**Features:**
- Color-coded scores (green for A, blue for B, yellow for C, red for D/F)
- Responsive layout
- i18n support with translation keys
- Uses shadcn/ui components (Card, Badge, Progress)

**Props:**
```typescript
interface QualityScoreData {
  overallScore: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  categories: QualityCategory[];
  issues: QualityIssue[];
  recommendations: QualityRecommendation[];
}
```

### 2. TTSControls Component
**Location:** `apps/frontend/src/renderer/components/settings/TTSControls.tsx`

Settings panel for text-to-speech configuration:
- Toggle TTS on/off
- Select TTS provider (Piper, macOS, System)
- Select voice from available voices
- Test voice button

**Features:**
- Integrated with Zustand store for state management
- Auto-loads voices when provider changes
- Disabled state when no voices available
- Uses shadcn/ui components (Switch, Select, Button)

**Integration:** Added to Settings dialog under "Text-to-Speech" section

### 3. MonitoringPanel Component
**Location:** `apps/frontend/src/renderer/components/analytics/MonitoringPanel.tsx`

Monitoring dashboard displaying:
- Cost tracking (total cost, input/output tokens)
- Heartbeat status with badge indicator
- Cost trends chart (last 7 days)
- Recent events list (errors, warnings, info)

**Features:**
- Auto-refresh heartbeat every 30 seconds
- Color-coded status badges
- Simple bar chart for cost trends
- Responsive grid layout
- Tabbed view for different time periods

### 4. TTS Store
**Location:** `apps/frontend/src/renderer/stores/tts-store.ts`

Zustand store for TTS state management:
```typescript
interface TTSState {
  enabled: boolean;
  provider: TTSProvider;
  selectedVoice: string | null;
  availableVoices: TTSVoice[];
  isLoading: boolean;
  isTesting: boolean;
  // Actions...
}
```

**Actions:**
- `setEnabled(enabled: boolean)` - Toggle TTS
- `setProvider(provider: TTSProvider)` - Change provider and reload voices
- `setSelectedVoice(voiceId: string)` - Select voice
- `testVoice()` - Test selected voice
- `loadVoices()` - Load available voices for current provider

### 5. Monitoring Store
**Location:** `apps/frontend/src/renderer/stores/monitoring-store.ts`

Zustand store for monitoring data:
```typescript
interface MonitoringState {
  heartbeatStatus: HeartbeatStatus;
  costMetrics: CostMetrics;
  recentEvents: MonitoringEvent[];
  costTrends: CostTrendData[];
  // Actions...
}
```

**Actions:**
- `loadMonitoringData()` - Fetch cost metrics and trends
- `refreshHeartbeat()` - Check system health
- `addEvent(event)` - Add monitoring event
- `clearEvents()` - Clear event history

## Translation Files

### English
**Location:** `apps/frontend/src/shared/i18n/locales/en/analytics.json`

Includes translations for:
- Quality score UI (`qualityScore.*`)
- TTS controls (`tts.*`)
- Monitoring panel (`monitoring.*`)

### French
**Location:** `apps/frontend/src/shared/i18n/locales/fr/analytics.json`

Complete French translations for all analytics features.

### Settings Integration
Updated both English and French `settings.json` to add TTS section:
```json
{
  "sections": {
    "tts": {
      "title": "Text-to-Speech",
      "description": "Voice synthesis settings"
    }
  }
}
```

## Settings Dialog Integration

**Modified:** `apps/frontend/src/renderer/components/settings/AppSettings.tsx`

Changes:
1. Added `'tts'` to `AppSection` type
2. Imported `TTSControls` component
3. Added `Volume2` icon from lucide-react
4. Added TTS navigation item to `appNavItemsConfig`
5. Added TTS section rendering in `renderAppSection()`

**Navigation Order:**
- Appearance
- Display
- Language
- Developer Tools
- Agent Settings
- Paths
- Integrations
- API Profiles
- Updates
- Notifications
- **Text-to-Speech** ← NEW
- Debug & Logs

## Design Principles

### 1. Consistent UI/UX
- All components use shadcn/ui primitives (Card, Badge, Button, Switch, Select, Progress)
- Follow Auto-Claude's existing design patterns
- Responsive layouts with grid/flexbox
- Color-coded status indicators

### 2. Internationalization
- All user-facing text uses i18n translation keys
- No hardcoded strings in components
- Support for English and French (extensible to other languages)

### 3. State Management
- Zustand stores for centralized state
- Separation of concerns (TTS state vs Monitoring state)
- Mock data for development (ready for backend integration)

### 4. Accessibility
- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Color contrast compliance

### 5. Performance
- Efficient re-renders with Zustand
- Auto-refresh with cleanup
- Lazy loading of voices
- Event list limited to 50 items

## Backend Integration Points

### TTS Backend APIs (TODO)
```typescript
// Add to window.electronAPI in preload.ts
interface ElectronAPI {
  getTTSVoices(provider: TTSProvider): Promise<TTSVoice[]>;
  testTTSVoice(provider: TTSProvider, voiceId: string): Promise<void>;
  saveTTSSettings(settings: TTSSettings): Promise<void>;
}
```

### Monitoring Backend APIs (TODO)
```typescript
interface ElectronAPI {
  getMonitoringData(): Promise<MonitoringData>;
  checkHeartbeat(): Promise<HeartbeatStatus>;
  getQualityScore(projectPath: string): Promise<QualityScoreData>;
}
```

## File Structure

```
apps/frontend/src/
├── renderer/
│   ├── components/
│   │   ├── analytics/
│   │   │   ├── QualityScoreCard.tsx       # Quality score display
│   │   │   ├── MonitoringPanel.tsx        # Monitoring dashboard
│   │   │   ├── index.tsx                  # Barrel exports
│   │   │   └── README.md                  # Component documentation
│   │   └── settings/
│   │       ├── TTSControls.tsx            # TTS settings panel
│   │       └── AppSettings.tsx            # Updated settings dialog
│   └── stores/
│       ├── tts-store.ts                   # TTS state management
│       └── monitoring-store.ts            # Monitoring state management
└── shared/
    └── i18n/
        └── locales/
            ├── en/
            │   ├── analytics.json         # English translations
            │   └── settings.json          # Updated with TTS section
            └── fr/
                ├── analytics.json         # French translations
                └── settings.json          # Updated with TTS section
```

## Usage Examples

### Quality Score Card
```tsx
import { QualityScoreCard } from '@/components/analytics';

const qualityData = {
  overallScore: 85,
  grade: 'B',
  categories: [
    { name: 'security', score: 90, weight: 0.3 },
    // ...
  ],
  issues: [
    { severity: 'high', category: 'security', message: 'XSS vulnerability' },
  ],
  recommendations: [
    { category: 'documentation', message: 'Add JSDoc comments' },
  ],
};

<QualityScoreCard data={qualityData} />
```

### Monitoring Panel
```tsx
import { MonitoringPanel } from '@/components/analytics';

// Automatically loads and refreshes data
<MonitoringPanel />
```

### TTS Controls (in Settings)
The TTS controls are automatically available in Settings → Text-to-Speech section.

## Testing Checklist

- [x] TypeScript compilation passes
- [x] i18n translation keys added for English and French
- [x] Components use shadcn/ui design system
- [x] State management with Zustand
- [x] Settings integration complete
- [ ] Backend IPC integration (pending)
- [ ] E2E tests (pending)
- [ ] Visual regression tests (pending)

## Next Steps

1. **Backend Integration:**
   - Add IPC handlers for TTS voice discovery and testing
   - Implement monitoring data collection endpoints
   - Add quality score calculation logic (Ralph integration)

2. **Enhanced Features:**
   - Real-time cost tracking during agent sessions
   - Quality score trends over time
   - TTS voice preview samples
   - Export monitoring data to CSV/JSON

3. **Testing:**
   - Unit tests for Zustand stores
   - Component tests with React Testing Library
   - Integration tests for Settings dialog
   - E2E tests for TTS functionality

4. **Documentation:**
   - Add JSDoc comments to all components
   - Create Storybook stories for visual documentation
   - Update main README with Ralph features

## Notes

- All components are fully typed with TypeScript
- Mock data is used for development; stores are ready for backend integration
- Charts use CSS-based rendering (no external chart library required)
- Components follow Auto-Claude's existing patterns and conventions
- Responsive design works on all screen sizes

## Related Files

- Ralph backend integration: `apps/backend/integrations/ralph/` (not yet created)
- Electron IPC handlers: `apps/frontend/src/main/ipc/` (to be updated)
- Type definitions: `apps/frontend/src/shared/types.ts` (to be updated)
