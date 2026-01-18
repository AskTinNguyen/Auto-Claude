import { QualityScoreCard } from './QualityScoreCard';
import { MonitoringPanel } from './MonitoringPanel';
import type { QualityScoreData } from './QualityScoreCard';

/**
 * Demo page showing all analytics components
 * This is for development/testing purposes only
 *
 * To use this demo:
 * 1. Import in your router or main app
 * 2. Navigate to the demo route
 * 3. See all components with mock data
 */
export function AnalyticsDemoPage() {
  // Mock quality score data for demonstration
  const mockQualityData: QualityScoreData = {
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
        message: 'Potential XSS vulnerability in user input handling at src/components/Form.tsx:45',
      },
      {
        severity: 'medium',
        category: 'performance',
        message: 'Large bundle size detected (1.2MB). Consider code splitting.',
      },
      {
        severity: 'low',
        category: 'maintainability',
        message: 'Function complexity exceeds threshold in src/utils/parser.ts:120',
      },
    ],
    recommendations: [
      {
        category: 'documentation',
        message: 'Add JSDoc comments to public API functions for better IntelliSense',
      },
      {
        category: 'testing',
        message: 'Increase test coverage for edge cases in authentication module',
      },
      {
        category: 'performance',
        message: 'Consider lazy-loading images to improve initial page load time',
      },
    ],
  };

  // Mock high-quality score for comparison
  const mockHighQualityData: QualityScoreData = {
    overallScore: 95,
    grade: 'A',
    categories: [
      { name: 'security', score: 98, weight: 0.3 },
      { name: 'performance', score: 95, weight: 0.2 },
      { name: 'maintainability', score: 92, weight: 0.3 },
      { name: 'documentation', score: 94, weight: 0.1 },
      { name: 'testing', score: 96, weight: 0.1 },
    ],
    issues: [],
    recommendations: [
      {
        category: 'performance',
        message: 'Consider implementing service workers for offline support',
      },
    ],
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Ralph Analytics Components Demo</h1>
          <p className="text-muted-foreground">
            Demonstration of quality score, TTS controls, and monitoring components
          </p>
        </div>

        <div className="space-y-8">
          {/* Quality Score Examples */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Quality Score Cards</h2>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  Standard Project (Grade B)
                </h3>
                <QualityScoreCard data={mockQualityData} />
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-2">
                  High Quality Project (Grade A)
                </h3>
                <QualityScoreCard data={mockHighQualityData} />
              </div>
            </div>
          </section>

          {/* Monitoring Panel */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">Monitoring Panel</h2>
            <MonitoringPanel />
          </section>

          {/* TTS Controls Info */}
          <section>
            <h2 className="text-2xl font-semibold mb-4">TTS Controls</h2>
            <div className="rounded-lg border border-border bg-card p-6">
              <p className="text-sm text-muted-foreground mb-4">
                TTS controls are integrated into the Settings dialog.
                Open Settings → Text-to-Speech to configure voice synthesis.
              </p>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>Toggle TTS on/off</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>Select provider (Piper, macOS, System)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>Choose voice from available voices</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-muted-foreground">•</span>
                  <span>Test voice with sample text</span>
                </div>
              </div>
            </div>
          </section>

          {/* Component Documentation */}
          <section className="border-t border-border pt-8">
            <h2 className="text-2xl font-semibold mb-4">Component Documentation</h2>
            <div className="space-y-4 text-sm">
              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="font-semibold mb-2">QualityScoreCard</h3>
                <p className="text-muted-foreground mb-2">
                  Location: <code className="text-xs bg-muted px-1 py-0.5 rounded">
                    components/analytics/QualityScoreCard.tsx
                  </code>
                </p>
                <p className="text-muted-foreground">
                  Displays code quality metrics with category breakdown, issues, and recommendations.
                  Supports grades A-F with color-coded scoring.
                </p>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="font-semibold mb-2">MonitoringPanel</h3>
                <p className="text-muted-foreground mb-2">
                  Location: <code className="text-xs bg-muted px-1 py-0.5 rounded">
                    components/analytics/MonitoringPanel.tsx
                  </code>
                </p>
                <p className="text-muted-foreground">
                  Shows cost tracking, heartbeat status, and recent events. Auto-refreshes
                  heartbeat every 30 seconds.
                </p>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="font-semibold mb-2">TTSControls</h3>
                <p className="text-muted-foreground mb-2">
                  Location: <code className="text-xs bg-muted px-1 py-0.5 rounded">
                    components/settings/TTSControls.tsx
                  </code>
                </p>
                <p className="text-muted-foreground">
                  Settings panel for text-to-speech configuration. Integrated into main
                  Settings dialog under "Text-to-Speech" section.
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
