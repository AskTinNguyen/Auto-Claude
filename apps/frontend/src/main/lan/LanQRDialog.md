# LanQRDialog Component

A React component that displays a QR code for mobile device connection to the Auto Claude LAN server.

## Features

- **QR Code Display**: Renders a scannable QR code using `qrcode.react` (QRCodeSVG)
- **Manual URL Entry**: Shows the connection URL as text for manual entry
- **Graceful Error Handling**: Displays a helpful message when URL is not available
- **Camera-Ready**: White background on QR code for optimal camera readability
- **Responsive Design**: Mobile-friendly layout
- **Internationalization**: Full i18n support (English and French)
- **Design System**: Matches existing Auto Claude UI patterns

## Installation

The component requires the `qrcode.react` package:

```bash
npm install qrcode.react
```

## Props

```typescript
interface LanQRDialogProps {
  open: boolean              // Whether the dialog is open
  onClose: () => void        // Callback when the dialog is closed
  url: string | null         // URL with PIN embedded (null if not available)
  title?: string            // Optional custom title
  description?: string      // Optional custom description
}
```

## Usage

### Basic Example

```tsx
import { useState } from 'react';
import { LanQRDialog } from './main/lan/LanQRDialog';

function MyComponent() {
  const [showQR, setShowQR] = useState(false);
  const [url, setUrl] = useState<string | null>(null);

  return (
    <>
      <button onClick={() => setShowQR(true)}>
        Show QR Code
      </button>

      <LanQRDialog
        open={showQR}
        onClose={() => setShowQR(false)}
        url={url}
      />
    </>
  );
}
```

### With LAN Module Integration

```tsx
import { useState } from 'react';
import { LanQRDialog } from './main/lan/LanQRDialog';
import { getLanAccessModule } from './main/lan/lan-module';

function LanConnectionButton() {
  const [showQR, setShowQR] = useState(false);
  const [connectionUrl, setConnectionUrl] = useState<string | null>(null);

  const handleShowQR = () => {
    const lanModule = getLanAccessModule();
    const urls = lanModule.getAllUrls();

    // Use LAN URL with PIN if available, fallback to Tailscale
    setConnectionUrl(urls.lanWithPin || urls.tailscaleWithPin);
    setShowQR(true);
  };

  return (
    <>
      <button onClick={handleShowQR}>
        Connect Mobile Device
      </button>

      <LanQRDialog
        open={showQR}
        onClose={() => setShowQR(false)}
        url={connectionUrl}
      />
    </>
  );
}
```

### Custom Title and Description

```tsx
<LanQRDialog
  open={showQR}
  onClose={() => setShowQR(false)}
  url="http://192.168.1.100:8080?pin=1234"
  title="Connect via Tailscale"
  description="Scan this QR code with your Tailscale-connected device"
/>
```

## Visual States

### With Valid URL

When a valid URL is provided, the dialog displays:
- Dialog header with smartphone icon and title
- QR code centered with white background (256x256px)
- Manual entry section showing the full URL in a code block
- Instructions section explaining how to use the QR code

### With Null URL

When `url` is `null`, the dialog displays:
- Dialog header with smartphone icon and title
- Alert icon with "Connection URL Not Available" message
- Helpful description explaining why the URL might not be available

## Translations

The component uses the `dialogs` namespace with the following keys:

### English (`en/dialogs.json`)

```json
{
  "lanQR": {
    "title": "Connect Mobile Device",
    "description": "Scan the QR code with your mobile device to connect to Auto Claude",
    "manualEntry": "Or enter this URL manually:",
    "instructions": "Open your mobile browser and scan the QR code or enter the URL above to access Auto Claude on your mobile device.",
    "notAvailable": "Connection URL Not Available",
    "notAvailableDescription": "Unable to generate a connection URL. Make sure the LAN server is running and you're connected to a network."
  }
}
```

### French (`fr/dialogs.json`)

```json
{
  "lanQR": {
    "title": "Connecter un appareil mobile",
    "description": "Scannez le code QR avec votre appareil mobile pour vous connecter à Auto Claude",
    "manualEntry": "Ou entrez cette URL manuellement :",
    "instructions": "Ouvrez votre navigateur mobile et scannez le code QR ou entrez l'URL ci-dessus pour accéder à Auto Claude sur votre appareil mobile.",
    "notAvailable": "URL de connexion non disponible",
    "notAvailableDescription": "Impossible de générer une URL de connexion. Assurez-vous que le serveur LAN est en cours d'exécution et que vous êtes connecté à un réseau."
  }
}
```

## QR Code Configuration

The QR code is generated with the following settings:

- **Size**: 256x256 pixels
- **Error Correction Level**: Medium (M)
- **Background Color**: White (`#ffffff`)
- **Foreground Color**: Black (`#000000`)
- **Include Margin**: false (handled by padding)

These settings ensure optimal scanability across different mobile camera qualities.

## Design System Integration

The component uses:

- **Radix UI Dialog**: For modal functionality
- **Lucide React Icons**: `Smartphone` and `AlertCircle`
- **Tailwind CSS**: For styling
- **Design Tokens**: `text-foreground`, `bg-muted`, `border-border`, etc.

## Accessibility

- Dialog follows ARIA best practices via Radix UI
- Proper focus management
- Keyboard navigation support
- Screen reader compatible
- Code blocks use monospace font for clarity

## File Location

```
apps/frontend/src/main/lan/
├── LanQRDialog.tsx          # Main component
├── LanQRDialog.example.tsx  # Usage examples
├── LanQRDialog.md           # This documentation
└── __tests__/
    └── LanQRDialog.test.tsx # Unit tests
```

## Testing

Run tests with:

```bash
cd apps/frontend
npm test LanQRDialog
```

## Dependencies

- `react` and `react-dom`
- `react-i18next` (internationalization)
- `qrcode.react` (QR code generation)
- `lucide-react` (icons)
- `@radix-ui/react-dialog` (dialog component)
- Tailwind CSS (styling)
