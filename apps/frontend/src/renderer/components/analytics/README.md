# Ralph Integration Analytics Components

React/TypeScript components for displaying quality scores, TTS controls, and monitoring analytics.

## Components

### QualityScoreCard

Displays code quality metrics with breakdown by category, issues, and recommendations.

**Usage:**

```tsx
import { QualityScoreCard, type QualityScoreData } from './analytics';

const data: QualityScoreData = {
  overallScore: 85,
  grade: 'B',
  categories: [
    { name: 'security', score: 90, weight: 0.3 },
    { name: 'performance', score: 80, weight: 0.2 },
    { name: 'maintainability', score: 85, weight: 0.3 },
    { name: 'documentation', score: 75, weight: 0.1 },
    { name: 'testing', score: 88, weight: 0.1 },
  ],
  issues: [
    {
      severity: 'high',
      category: 'security',
      message: 'Potential XSS vulnerability in user input handling',
    },
    {
      severity: 'medium',
      category: 'performance',
      message: 'Large bundle size detected (>1MB)',
    },
  ],
  recommendations: [
    {
      category: 'documentation',
      message: 'Add JSDoc comments to public API functions',
    },
  ],
};

<QualityScoreCard data={data} />;
```

### TTSControls

Settings component for configuring text-to-speech features.

**Usage:**

```tsx
import { TTSControls } from './settings/TTSControls';

// In Settings dialog
<TTSControls />;
```

The component uses Zustand store (`useTTSStore`) for state management. Settings are automatically saved.

### MonitoringPanel

Displays cost tracking, heartbeat status, and recent events.

**Usage:**

```tsx
import { MonitoringPanel } from './analytics';

<MonitoringPanel />;
```

The component uses Zustand store (`useMonitoringStore`) for state management and automatically refreshes data.

## State Management

### TTS Store

Located at `stores/tts-store.ts`:

```tsx
import { useTTSStore } from '@/stores/tts-store';

const { enabled, provider, selectedVoice, setEnabled, testVoice } = useTTSStore();
```

### Monitoring Store

Located at `stores/monitoring-store.ts`:

```tsx
import { useMonitoringStore } from '@/stores/monitoring-store';

const { costMetrics, heartbeatStatus, addEvent } = useMonitoringStore();
```

## Integration with Backend

These components are ready for backend integration. Add Electron IPC handlers for:

**TTS:**
- `window.electronAPI.getTTSVoices(provider)` - Get available voices
- `window.electronAPI.testTTSVoice(provider, voiceId)` - Test voice playback

**Monitoring:**
- `window.electronAPI.getMonitoringData()` - Get cost metrics and trends
- `window.electronAPI.checkHeartbeat()` - Check system status

## Translation Keys

All user-facing text uses i18n translation keys from `analytics.json`:

**English:** `apps/frontend/src/shared/i18n/locales/en/analytics.json`
**French:** `apps/frontend/src/shared/i18n/locales/fr/analytics.json`

Add translations for other languages as needed.

## Styling

Components use shadcn/ui design system and Auto-Claude's existing theme system. They automatically adapt to:
- Light/dark mode
- User-configured UI scale
- Theme colors

## Example Integration

To integrate these components into a project dashboard:

```tsx
import { QualityScoreCard, MonitoringPanel } from '@/components/analytics';
import type { QualityScoreData } from '@/components/analytics';

function ProjectDashboard() {
  const [qualityData, setQualityData] = useState<QualityScoreData | null>(null);

  useEffect(() => {
    // Load quality data from backend
    window.electronAPI.getQualityScore().then(setQualityData);
  }, []);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      {qualityData && <QualityScoreCard data={qualityData} />}
      <MonitoringPanel />
    </div>
  );
}
```
