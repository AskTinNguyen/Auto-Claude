/**
 * LanQRDialog - QR code dialog for mobile device connection
 *
 * Displays QR codes for both LAN and Tailscale connections, allowing mobile
 * devices to connect to the Auto Claude server with PIN authentication.
 *
 * Features:
 * - Tab-based switching between LAN and Tailscale QR codes
 * - QR code display using qrcode.react (QRCodeSVG)
 * - Text URL display for manual entry
 * - Graceful handling of null URLs (shows unavailable message)
 * - White background for QR code (for camera readability)
 * - Responsive design (mobile-friendly)
 *
 * @example
 * ```tsx
 * <LanQRDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   lanUrl="http://192.168.1.100:3000?pin=1234"
 *   tailscaleUrl="http://100.64.0.1:3000?pin=1234"
 * />
 * ```
 */
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { QRCodeSVG } from 'qrcode.react';
import { Smartphone, AlertCircle, Wifi, Globe } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle
} from '../../renderer/components/ui/dialog';

/**
 * Props for the LanQRDialog component
 */
export interface LanQRDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when the dialog is closed */
  onClose: () => void;
  /** LAN URL with PIN embedded (null if not available) */
  lanUrl?: string | null;
  /** Tailscale URL with PIN embedded (null if not available) */
  tailscaleUrl?: string | null;
  /** @deprecated Use lanUrl instead - kept for backwards compatibility */
  url?: string | null;
  /** Optional custom title (uses default i18n if not provided) */
  title?: string;
  /** Optional custom description (uses default i18n if not provided) */
  description?: string;
}

type NetworkType = 'lan' | 'tailscale';

export function LanQRDialog({
  open,
  onClose,
  lanUrl,
  tailscaleUrl,
  url, // backwards compatibility
  title,
  description
}: LanQRDialogProps) {
  const { t } = useTranslation('dialogs');

  // Backwards compatibility: if only url is provided, use it as lanUrl
  const effectiveLanUrl = lanUrl ?? url ?? null;
  const effectiveTailscaleUrl = tailscaleUrl ?? null;

  // Determine which tabs are available
  const hasLan = !!effectiveLanUrl;
  const hasTailscale = !!effectiveTailscaleUrl;
  const hasBoth = hasLan && hasTailscale;

  // Default to tailscale if only tailscale is available, otherwise LAN
  const defaultTab: NetworkType = !hasLan && hasTailscale ? 'tailscale' : 'lan';
  const [activeTab, setActiveTab] = useState<NetworkType>(defaultTab);

  // Get the URL for the active tab
  const activeUrl = activeTab === 'tailscale' ? effectiveTailscaleUrl : effectiveLanUrl;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-foreground">
            <Smartphone className="h-5 w-5" />
            {title || t('lanQR.title')}
          </DialogTitle>
          <DialogDescription>
            {description || t('lanQR.description')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Network Type Tabs (only show if both are available) */}
          {hasBoth && (
            <div className="flex rounded-lg bg-muted p-1">
              <button
                onClick={() => setActiveTab('lan')}
                className={`flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'lan'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Wifi className="h-4 w-4" />
                {t('lanQR.tabLan', 'Local Network')}
              </button>
              <button
                onClick={() => setActiveTab('tailscale')}
                className={`flex-1 flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === 'tailscale'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Globe className="h-4 w-4" />
                {t('lanQR.tabTailscale', 'Tailscale')}
              </button>
            </div>
          )}

          {/* Single network indicator (when only one is available) */}
          {!hasBoth && (hasLan || hasTailscale) && (
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              {hasLan ? (
                <>
                  <Wifi className="h-4 w-4" />
                  {t('lanQR.networkLan', 'Local Network')}
                </>
              ) : (
                <>
                  <Globe className="h-4 w-4" />
                  {t('lanQR.networkTailscale', 'Tailscale')}
                </>
              )}
            </div>
          )}

          {/* QR Code Display */}
          {activeUrl ? (
            <>
              {/* QR Code with white background for camera readability */}
              <div className="flex justify-center">
                <div className="bg-white p-4 rounded-lg inline-block">
                  <QRCodeSVG
                    value={activeUrl}
                    size={256}
                    level="M"
                    includeMargin={false}
                    bgColor="#ffffff"
                    fgColor="#000000"
                  />
                </div>
              </div>

              {/* URL Text for manual entry */}
              <div className="space-y-2">
                <p className="text-sm font-medium text-foreground">
                  {t('lanQR.manualEntry')}
                </p>
                <div className="bg-muted rounded-lg p-3 border border-border">
                  <code className="text-xs text-foreground break-all font-mono">
                    {activeUrl}
                  </code>
                </div>
              </div>

              {/* Network-specific instructions */}
              <div className="bg-accent/50 rounded-lg p-4 border border-accent">
                <p className="text-sm text-muted-foreground">
                  {activeTab === 'tailscale'
                    ? t('lanQR.instructionsTailscale', 'Scan this QR code with your mobile device. Both devices must be connected to your Tailscale network.')
                    : t('lanQR.instructions', 'Scan this QR code with your mobile device. Both devices must be on the same local network.')}
                </p>
              </div>
            </>
          ) : (
            /* Not Available Message */
            <div className="flex flex-col items-center justify-center gap-4 py-8">
              <div className="rounded-full bg-destructive/10 p-4">
                <AlertCircle className="h-8 w-8 text-destructive" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-sm font-medium text-foreground">
                  {t('lanQR.notAvailable')}
                </p>
                <p className="text-sm text-muted-foreground">
                  {activeTab === 'tailscale'
                    ? t('lanQR.notAvailableTailscale', 'Tailscale is not detected on this device. Make sure Tailscale is installed and connected.')
                    : t('lanQR.notAvailableDescription')}
                </p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
