import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Progress } from '../ui/progress';
import { AlertCircle, CheckCircle2, Info } from 'lucide-react';

export interface QualityCategory {
  name: string;
  score: number;
  weight: number;
}

export interface QualityIssue {
  severity: 'high' | 'medium' | 'low';
  category: string;
  message: string;
}

export interface QualityRecommendation {
  category: string;
  message: string;
}

export interface QualityScoreData {
  overallScore: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  categories: QualityCategory[];
  issues: QualityIssue[];
  recommendations: QualityRecommendation[];
}

interface QualityScoreCardProps {
  data: QualityScoreData;
  className?: string;
}

/**
 * Display quality score (0-100) and grade (A-F)
 * Show breakdown by category with progress bars
 * List issues and recommendations
 */
export function QualityScoreCard({ data, className }: QualityScoreCardProps) {
  const { t } = useTranslation('analytics');

  const getGradeColor = (grade: string): string => {
    switch (grade) {
      case 'A':
        return 'text-success';
      case 'B':
        return 'text-info';
      case 'C':
        return 'text-warning';
      case 'D':
      case 'F':
        return 'text-destructive';
      default:
        return 'text-muted-foreground';
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-success';
    if (score >= 75) return 'text-info';
    if (score >= 60) return 'text-warning';
    return 'text-destructive';
  };

  const getSeverityVariant = (
    severity: QualityIssue['severity']
  ): 'destructive' | 'warning' | 'info' => {
    switch (severity) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      case 'low':
        return 'info';
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{t('qualityScore.title')}</CardTitle>
            <CardDescription>
              {t('qualityScore.grade')}: <span className={getGradeColor(data.grade)}>{data.grade}</span>
            </CardDescription>
          </div>
          <div className="text-right">
            <div className={`text-4xl font-bold ${getScoreColor(data.overallScore)}`}>
              {data.overallScore}
            </div>
            <div className="text-sm text-muted-foreground">{t('qualityScore.score')}</div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Category Breakdown */}
        <div className="space-y-4">
          <h4 className="text-sm font-semibold">{t('qualityScore.breakdown')}</h4>
          {data.categories.map((category) => (
            <div key={category.name} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {t(`qualityScore.categories.${category.name.toLowerCase()}`)}
                </span>
                <span className={getScoreColor(category.score)}>{category.score}%</span>
              </div>
              <Progress value={category.score} className="h-2" />
            </div>
          ))}
        </div>

        {/* Issues */}
        {data.issues.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-warning" />
              {t('qualityScore.issues')}
            </h4>
            <div className="space-y-2">
              {data.issues.map((issue, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 rounded-md border border-border bg-card p-3"
                >
                  <Badge variant={getSeverityVariant(issue.severity)} className="mt-0.5">
                    {issue.severity}
                  </Badge>
                  <div className="flex-1">
                    <div className="text-xs text-muted-foreground mb-1">
                      {t(`qualityScore.categories.${issue.category.toLowerCase()}`)}
                    </div>
                    <div className="text-sm">{issue.message}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.issues.length === 0 && (
          <div className="flex items-center gap-2 rounded-md border border-success/20 bg-success/5 p-3 text-sm text-success">
            <CheckCircle2 className="h-4 w-4" />
            {t('qualityScore.noIssues')}
          </div>
        )}

        {/* Recommendations */}
        {data.recommendations.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold flex items-center gap-2">
              <Info className="h-4 w-4 text-info" />
              {t('qualityScore.recommendations')}
            </h4>
            <div className="space-y-2">
              {data.recommendations.map((recommendation, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 rounded-md border border-border bg-card p-3"
                >
                  <Badge variant="info" className="mt-0.5">
                    {t(`qualityScore.categories.${recommendation.category.toLowerCase()}`)}
                  </Badge>
                  <div className="flex-1 text-sm">{recommendation.message}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.recommendations.length === 0 && data.issues.length === 0 && (
          <div className="text-center text-sm text-muted-foreground py-4">
            {t('qualityScore.noRecommendations')}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
