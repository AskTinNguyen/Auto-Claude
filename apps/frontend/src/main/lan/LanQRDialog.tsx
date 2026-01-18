/**
 * LanQRDialog - QR code dialog for mobile device connection
 *
 * Displays a QR code that mobile devices can scan to connect to the
 * Auto Claude LAN server with PIN authentication.
 *
 * Features:
 * - QR code display using qrcode.react (QRCodeSVG)
 * - Text URL display for manual entry
 * - Graceful handling of null URL (shows unavailable message)
 * - White background for QR code (for camera readability)
 * - Responsive design (mobile-friendly)
 *
 * @example
 * ```tsx
 * <LanQRDialog
 *   open={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   url="http://192.168.1.100:8080?pin=123456"
 *   title="Connect Mobile Device"
 *   description="Scan this QR code with your mobile device"
 * />
 * ```
 */
import { useTranslation } from 'react-i18next';
import { QRCodeSVG } from 'qrcode.react';
import { Smartphone, AlertCircle } from 'lucide-react';
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
  /** URL with PIN embedded (null if not available) */
  url: string | null;
  /** Optional custom title (uses default i18n if not provided) */
  title?: string;
  /** Optional custom description (uses default i18n if not provided) */
  description?: string;
}

export function LanQRDialog({
  open,
  onClose,
  url,
  title,
  description
}: LanQRDialogProps) {
  const { t } = useTranslation('dialogs');

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
          {/* QR Code Display */}
          {url ? (
            <>
              {/* QR Code with white background for camera readability */}
              <div className="flex justify-center">
                <div className="bg-white p-4 rounded-lg inline-block">
                  <QRCodeSVG
                    value={url}
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
                    {url}
                  </code>
                </div>
              </div>

              {/* Instructions */}
              <div className="bg-accent/50 rounded-lg p-4 border border-accent">
                <p className="text-sm text-muted-foreground">
                  {t('lanQR.instructions')}
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
                  {t('lanQR.notAvailableDescription')}
                </p>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
