import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import {
  Stethoscope,
  DollarSign,
  BarChart3,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
} from 'lucide-react';
import { SettingsSection } from './SettingsSection';
import { useProjectStore } from '../../stores/project-store';

interface RalphSettingsProps {
  className?: string;
}

interface DoctorCheck {
  name: string;
  passed: boolean;
  info: string;
}

interface StatsData {
  totalSpecs: number;
  totalSessions: number;
  totalCostUsd: number;
  avgCostPerSpec: number;
  successRate: number;
}

interface BudgetData {
  globalBudgetUsd: number | null;
  totalSpentUsd: number;
  remainingUsd: number | null;
  warningThreshold: number;
}

/**
 * Ralph Settings component
 * - Environment diagnostics (doctor)
 * - Budget management
 * - Stats overview
 */
export function RalphSettings({ className }: RalphSettingsProps) {
  const { t } = useTranslation(['settings', 'common']);
  const projects = useProjectStore((state) => state.projects);
  const selectedProjectId = useProjectStore((state) => state.selectedProjectId);
  const activeProject = projects.find((p) => p.id === selectedProjectId);

  const [doctorResults, setDoctorResults] = useState<DoctorCheck[]>([]);
  const [isRunningDoctor, setIsRunningDoctor] = useState(false);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [budget, setBudget] = useState<BudgetData | null>(null);
  const [newBudgetAmount, setNewBudgetAmount] = useState('');
  const [isSavingBudget, setIsSavingBudget] = useState(false);

  const projectDir = activeProject?.path;

  // Load stats and budget on mount
  useEffect(() => {
    if (projectDir) {
      loadStats();
      loadBudget();
    }
  }, [projectDir]);

  const loadStats = useCallback(async () => {
    if (!projectDir) return;
    try {
      const result = await window.electronAPI.ralph.stats(projectDir);
      if (result.success && result.data) {
        setStats(result.data as StatsData);
      }
    } catch (error) {
      console.error('Failed to load Ralph stats:', error);
    }
  }, [projectDir]);

  const loadBudget = useCallback(async () => {
    if (!projectDir) return;
    try {
      const result = await window.electronAPI.ralph.budgetGet(projectDir);
      if (result.success && result.data) {
        setBudget(result.data as BudgetData);
        if (result.data.globalBudgetUsd !== null) {
          setNewBudgetAmount(result.data.globalBudgetUsd.toString());
        }
      }
    } catch (error) {
      console.error('Failed to load Ralph budget:', error);
    }
  }, [projectDir]);

  const runDoctor = async () => {
    if (!projectDir) return;
    setIsRunningDoctor(true);
    try {
      const result = await window.electronAPI.ralph.doctor(projectDir);
      if (result.success && result.data) {
        setDoctorResults((result.data as { checks: DoctorCheck[] }).checks || []);
      }
    } catch (error) {
      console.error('Failed to run Ralph doctor:', error);
    } finally {
      setIsRunningDoctor(false);
    }
  };

  const saveBudget = async () => {
    if (!projectDir) return;
    setIsSavingBudget(true);
    try {
      const amount = parseFloat(newBudgetAmount);
      if (!isNaN(amount) && amount > 0) {
        await window.electronAPI.ralph.budgetSet(projectDir, amount);
        await loadBudget();
      }
    } catch (error) {
      console.error('Failed to save budget:', error);
    } finally {
      setIsSavingBudget(false);
    }
  };

  const clearBudget = async () => {
    if (!projectDir) return;
    setIsSavingBudget(true);
    try {
      await window.electronAPI.ralph.budgetClear(projectDir);
      setNewBudgetAmount('');
      await loadBudget();
    } catch (error) {
      console.error('Failed to clear budget:', error);
    } finally {
      setIsSavingBudget(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const getBudgetUsagePercent = () => {
    if (!budget || budget.globalBudgetUsd === null) return 0;
    return (budget.totalSpentUsd / budget.globalBudgetUsd) * 100;
  };

  const getBudgetStatusColor = () => {
    const usage = getBudgetUsagePercent();
    if (usage >= 100) return 'text-red-500';
    if (usage >= (budget?.warningThreshold || 0.8) * 100) return 'text-yellow-500';
    return 'text-green-500';
  };

  if (!projectDir) {
    return (
      <SettingsSection
        title={t('settings:ralph.title', 'Ralph CLI')}
        description={t('settings:ralph.noProject', 'Select a project to configure Ralph settings.')}
        className={className}
      >
        <div className="text-sm text-muted-foreground">
          {t('settings:ralph.noProjectSelected', 'No project selected')}
        </div>
      </SettingsSection>
    );
  }

  return (
    <SettingsSection
      title={t('settings:ralph.title', 'Ralph CLI')}
      description={t('settings:ralph.description', 'Manage Ralph workflow automation settings.')}
      className={className}
    >
      <div className="space-y-8">
        {/* Environment Diagnostics */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="flex items-center gap-2">
                <Stethoscope className="h-4 w-4" />
                {t('settings:ralph.doctor.title', 'Environment Diagnostics')}
              </Label>
              <p className="text-sm text-muted-foreground">
                {t('settings:ralph.doctor.description', 'Check your Auto-Claude environment setup.')}
              </p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={runDoctor}
              disabled={isRunningDoctor}
            >
              {isRunningDoctor ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  {t('common:labels.loading', 'Loading...')}
                </>
              ) : (
                <>
                  <Stethoscope className="h-4 w-4 mr-2" />
                  {t('settings:ralph.doctor.runButton', 'Run Diagnostics')}
                </>
              )}
            </Button>
          </div>

          {/* Doctor Results */}
          {doctorResults.length > 0 && (
            <div className="border rounded-lg p-4 space-y-2">
              {doctorResults.map((check, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2">
                    {check.passed ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    {check.name}
                  </span>
                  <span className="text-muted-foreground">{check.info}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Budget Management */}
        <div className="space-y-4">
          <div className="space-y-0.5">
            <Label className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              {t('settings:ralph.budget.title', 'Budget Management')}
            </Label>
            <p className="text-sm text-muted-foreground">
              {t('settings:ralph.budget.description', 'Set spending limits to prevent runaway costs.')}
            </p>
          </div>

          {/* Current Budget Status */}
          {budget && (
            <div className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">{t('settings:ralph.budget.spent', 'Spent')}</span>
                <span className="font-mono">{formatCurrency(budget.totalSpentUsd)}</span>
              </div>
              {budget.globalBudgetUsd !== null && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{t('settings:ralph.budget.limit', 'Limit')}</span>
                    <span className="font-mono">{formatCurrency(budget.globalBudgetUsd)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{t('settings:ralph.budget.remaining', 'Remaining')}</span>
                    <span className={`font-mono ${getBudgetStatusColor()}`}>
                      {formatCurrency(budget.remainingUsd || 0)}
                    </span>
                  </div>
                  {/* Progress Bar */}
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${
                        getBudgetUsagePercent() >= 100
                          ? 'bg-red-500'
                          : getBudgetUsagePercent() >= (budget.warningThreshold || 0.8) * 100
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(getBudgetUsagePercent(), 100)}%` }}
                    />
                  </div>
                </>
              )}
            </div>
          )}

          {/* Set Budget */}
          <div className="flex items-center gap-2">
            <Input
              type="number"
              step="0.01"
              min="0"
              placeholder={t('settings:ralph.budget.placeholder', 'Enter budget (USD)')}
              value={newBudgetAmount}
              onChange={(e) => setNewBudgetAmount(e.target.value)}
              className="flex-1"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={saveBudget}
              disabled={isSavingBudget || !newBudgetAmount}
            >
              {t('settings:ralph.budget.setButton', 'Set')}
            </Button>
            {budget?.globalBudgetUsd !== null && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearBudget}
                disabled={isSavingBudget}
              >
                {t('settings:ralph.budget.clearButton', 'Clear')}
              </Button>
            )}
          </div>
        </div>

        {/* Stats Overview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                {t('settings:ralph.stats.title', 'Statistics')}
              </Label>
              <p className="text-sm text-muted-foreground">
                {t('settings:ralph.stats.description', 'Overview of your build performance.')}
              </p>
            </div>
            <Button variant="ghost" size="sm" onClick={loadStats}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>

          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="border rounded-lg p-3 text-center">
                <div className="text-2xl font-bold">{stats.totalSpecs}</div>
                <div className="text-xs text-muted-foreground">
                  {t('settings:ralph.stats.specs', 'Specs')}
                </div>
              </div>
              <div className="border rounded-lg p-3 text-center">
                <div className="text-2xl font-bold">{stats.totalSessions}</div>
                <div className="text-xs text-muted-foreground">
                  {t('settings:ralph.stats.sessions', 'Sessions')}
                </div>
              </div>
              <div className="border rounded-lg p-3 text-center">
                <div className="text-2xl font-bold">{formatCurrency(stats.totalCostUsd)}</div>
                <div className="text-xs text-muted-foreground">
                  {t('settings:ralph.stats.totalCost', 'Total Cost')}
                </div>
              </div>
              <div className="border rounded-lg p-3 text-center">
                <div className="text-2xl font-bold">{stats.successRate.toFixed(0)}%</div>
                <div className="text-xs text-muted-foreground">
                  {t('settings:ralph.stats.successRate', 'Success Rate')}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </SettingsSection>
  );
}
