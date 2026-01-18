/**
 * LanQRDialog Tests
 *
 * Tests for the QR code dialog component
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LanQRDialog } from '../LanQRDialog';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'lanQR.title': 'Connect Mobile Device',
        'lanQR.description': 'Scan the QR code with your mobile device to connect to Auto Claude',
        'lanQR.manualEntry': 'Or enter this URL manually:',
        'lanQR.instructions': 'Open your mobile browser and scan the QR code or enter the URL above to access Auto Claude on your mobile device.',
        'lanQR.notAvailable': 'Connection URL Not Available',
        'lanQR.notAvailableDescription': 'Unable to generate a connection URL. Make sure the LAN server is running and you\'re connected to a network.'
      };
      return translations[key] || key;
    }
  })
}));

describe('LanQRDialog', () => {
  it('renders with valid URL', () => {
    const testUrl = 'http://192.168.1.100:8080?pin=123456';

    render(
      <LanQRDialog
        open={true}
        onClose={vi.fn()}
        url={testUrl}
      />
    );

    // Check that title and description are present
    expect(screen.getByText('Connect Mobile Device')).toBeDefined();
    expect(screen.getByText(/Scan the QR code/)).toBeDefined();

    // Check that manual entry section is present
    expect(screen.getByText('Or enter this URL manually:')).toBeDefined();

    // Check that URL is displayed
    expect(screen.getByText(testUrl)).toBeDefined();

    // Check that instructions are present
    expect(screen.getByText(/Open your mobile browser/)).toBeDefined();
  });

  it('renders not available message when URL is null', () => {
    render(
      <LanQRDialog
        open={true}
        onClose={vi.fn()}
        url={null}
      />
    );

    // Check that not available message is displayed
    expect(screen.getByText('Connection URL Not Available')).toBeDefined();
    expect(screen.getByText(/Unable to generate a connection URL/)).toBeDefined();
  });

  it('uses custom title and description when provided', () => {
    const customTitle = 'Custom Title';
    const customDescription = 'Custom Description';

    render(
      <LanQRDialog
        open={true}
        onClose={vi.fn()}
        url="http://test.com"
        title={customTitle}
        description={customDescription}
      />
    );

    expect(screen.getByText(customTitle)).toBeDefined();
    expect(screen.getByText(customDescription)).toBeDefined();
  });

  it('does not render when open is false', () => {
    const { container } = render(
      <LanQRDialog
        open={false}
        onClose={vi.fn()}
        url="http://test.com"
      />
    );

    // Dialog should not be visible when closed
    // Radix UI Dialog sets data-state="closed" when not open
    expect(container.querySelector('[data-state="open"]')).toBeNull();
  });
});
