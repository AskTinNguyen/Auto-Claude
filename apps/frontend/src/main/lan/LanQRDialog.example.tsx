/**
 * LanQRDialog Usage Example
 *
 * This file demonstrates how to use the LanQRDialog component
 * in a typical application scenario.
 */
import { useState } from 'react';
import { Button } from '../../renderer/components/ui/button';
import { LanQRDialog } from './LanQRDialog';
import { getLanAccessModule } from './lan-module';

/**
 * Example component showing LanQRDialog integration
 */
export function LanQRDialogExample() {
  const [showQRDialog, setShowQRDialog] = useState(false);
  const [connectionUrl, setConnectionUrl] = useState<string | null>(null);

  // Function to generate LAN URL with PIN
  const generateConnectionUrl = async () => {
    try {
      const lanModule = getLanAccessModule();
      if (!lanModule) {
        console.error('LAN module not initialized');
        return null;
      }

      const urls = lanModule.getAllUrls();

      // Use LAN URL with PIN if available, fallback to Tailscale
      return urls.lanWithPin || urls.tailscaleWithPin;
    } catch (error) {
      console.error('Failed to generate connection URL:', error);
      return null;
    }
  };

  // Handle button click
  const handleShowQR = async () => {
    const url = await generateConnectionUrl();
    setConnectionUrl(url);
    setShowQRDialog(true);
  };

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-semibold">LAN Connection</h2>

      <Button onClick={handleShowQR}>
        Show QR Code for Mobile Connection
      </Button>

      <LanQRDialog
        open={showQRDialog}
        onClose={() => setShowQRDialog(false)}
        url={connectionUrl}
      />
    </div>
  );
}

/**
 * Example with custom title and description
 */
export function LanQRDialogCustomExample() {
  const [showQRDialog, setShowQRDialog] = useState(false);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-semibold">Custom LAN Connection</h2>

      <Button onClick={() => setShowQRDialog(true)}>
        Connect Tailscale Device
      </Button>

      <LanQRDialog
        open={showQRDialog}
        onClose={() => setShowQRDialog(false)}
        url="http://100.64.1.100:8080?pin=abcd1234"
        title="Connect via Tailscale"
        description="Scan this QR code with your Tailscale-connected device"
      />
    </div>
  );
}

/**
 * Example handling null URL (server not running)
 */
export function LanQRDialogNullUrlExample() {
  const [showQRDialog, setShowQRDialog] = useState(false);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-semibold">Server Not Running Example</h2>

      <Button onClick={() => setShowQRDialog(true)}>
        Try to Connect (Server Offline)
      </Button>

      <LanQRDialog
        open={showQRDialog}
        onClose={() => setShowQRDialog(false)}
        url={null}
      />
    </div>
  );
}
