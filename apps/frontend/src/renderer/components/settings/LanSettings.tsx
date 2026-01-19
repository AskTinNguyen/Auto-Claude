import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { QrCode, Copy, Check, AlertTriangle } from 'lucide-react';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { SettingsSection } from './SettingsSection';
import { LanQRDialog } from '../../../main/lan/LanQRDialog';
import type { AppSettings } from '../../../shared/types';

interface LanSettingsProps {
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
}

interface LanUrls {
  lan: string | null;
  lanWithPin: string | null;
  tailscale: string | null;
  tailscaleWithPin: string | null;
}

/**
 * LAN Access Settings Component
 *
 * Allows users to:
 * - Enable/disable LAN access
 * - Configure a static 4-digit PIN (or leave empty for random)
 * - View current PIN
 * - View LAN URLs (local and Tailscale if available)
 * - Show QR code for mobile device connection
 */
export function LanSettings({ settings, onSettingsChange }: LanSettingsProps) {
  const { t } = useTranslation(['settings', 'common']);

  const [showQRDialog, setShowQRDialog] = useState(false);
  const [lanUrls, setLanUrls] = useState<LanUrls | null>(null);
  const [currentPin, setCurrentPin] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);

  // Fetch LAN URLs and PIN when LAN access is enabled
  useEffect(() => {
    if (settings.allowLan) {
      // Fetch LAN URLs
      window.electronAPI.getLanUrls()
        .then((urls: LanUrls | null) => {
          setLanUrls(urls);
        })
        .catch((err) => {
          console.error('[LanSettings] Failed to fetch LAN URLs:', err);
          setLanUrls(null);
        });

      // Fetch current PIN
      window.electronAPI.getLanPin()
        .then((pin: string | null) => {
          setCurrentPin(pin);
        })
        .catch((err) => {
          console.error('[LanSettings] Failed to fetch PIN:', err);
          setCurrentPin(null);
        });
    } else {
      setLanUrls(null);
      setCurrentPin(null);
    }
  }, [settings.allowLan]);

  const handleAllowLanChange = async (checked: boolean) => {
    // Update local settings
    onSettingsChange({ ...settings, allowLan: checked });

    // Restart server with new settings
    try {
      await window.electronAPI.restartLanServer({ ...settings, allowLan: checked });
    } catch (err) {
      console.error('[LanSettings] Failed to restart server:', err);
    }
  };

  const handlePinChange = (value: string) => {
    // Only allow digits, max 4 characters
    const sanitized = value.replace(/[^0-9]/g, '').slice(0, 4);
    onSettingsChange({ ...settings, lanPin: sanitized || null });
  };

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(url);
    setTimeout(() => setCopiedUrl(null), 2000);
  };

  return (
    <SettingsSection
      title={t('settings:sections.lan.title')}
      description={t('settings:sections.lan.description')}
    >
      <div className="space-y-6">
        {/* Enable LAN Access Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label htmlFor="allow-lan">{t('settings:lan.enableLan')}</Label>
            <p className="text-sm text-muted-foreground">
              {t('settings:lan.enableLanDescription')}
            </p>
          </div>
          <Switch
            id="allow-lan"
            checked={settings.allowLan ?? false}
            onCheckedChange={handleAllowLanChange}
          />
        </div>

        {/* LAN Settings (shown when enabled) */}
        {settings.allowLan && (
          <>
            {/* Security Warning */}
            <div className="rounded-lg bg-warning/10 border border-warning/30 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-warning mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <p className="text-sm font-medium text-warning">
                    {t('settings:lan.securityWarning')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t('settings:lan.securityWarningDescription')}
                  </p>
                </div>
              </div>
            </div>

            {/* Static PIN Input */}
            <div className="space-y-2">
              <Label htmlFor="lan-pin">{t('settings:lan.staticPin')}</Label>
              <Input
                id="lan-pin"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{4}"
                maxLength={4}
                value={settings.lanPin || ''}
                onChange={(e) => handlePinChange(e.target.value)}
                placeholder={t('settings:lan.pinPlaceholder')}
                className="max-w-xs"
              />
              <p className="text-xs text-muted-foreground">
                {t('settings:lan.pinHint')}
              </p>
            </div>

            {/* Current PIN Display */}
            {currentPin && (
              <div className="rounded-lg bg-muted/50 border border-border p-4">
                <div className="space-y-1">
                  <p className="text-sm font-medium">{t('settings:lan.currentPin')}</p>
                  <p className="text-2xl font-mono font-bold tracking-wider text-foreground">
                    {currentPin}
                  </p>
                </div>
              </div>
            )}

            {/* LAN URLs Display */}
            {lanUrls && (
              <div className="space-y-4">
                {/* Local Network URL */}
                {lanUrls.lan && (
                  <div className="space-y-2">
                    <Label>{t('settings:lan.localUrl')}</Label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded-lg bg-muted px-3 py-2 text-sm font-mono text-foreground break-all">
                        {lanUrls.lan}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyUrl(lanUrls.lan!)}
                      >
                        {copiedUrl === lanUrls.lan ? (
                          <Check className="h-4 w-4" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Tailscale URL (if available) */}
                {lanUrls.tailscale && (
                  <div className="space-y-2">
                    <Label>{t('settings:lan.tailscaleUrl')}</Label>
                    <div className="flex items-center gap-2">
                      <code className="flex-1 rounded-lg bg-muted px-3 py-2 text-sm font-mono text-foreground break-all">
                        {lanUrls.tailscale}
                      </code>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCopyUrl(lanUrls.tailscale!)}
                      >
                        {copiedUrl === lanUrls.tailscale ? (
                          <Check className="h-4 w-4" />
                        ) : (
                          <Copy className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Show QR Code Button */}
                <Button
                  variant="secondary"
                  onClick={() => setShowQRDialog(true)}
                  className="w-full sm:w-auto"
                >
                  <QrCode className="mr-2 h-4 w-4" />
                  {t('settings:lan.showQrCode')}
                </Button>
              </div>
            )}
          </>
        )}

        {/* QR Code Dialog */}
        {showQRDialog && lanUrls && (
          <LanQRDialog
            open={showQRDialog}
            onClose={() => setShowQRDialog(false)}
            lanUrl={lanUrls.lanWithPin || lanUrls.lan}
            tailscaleUrl={lanUrls.tailscaleWithPin || lanUrls.tailscale}
          />
        )}
      </div>
    </SettingsSection>
  );
}
