import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PinEntryModal } from '../PinEntryModal';
import { useLanAuthStore } from '../../../stores/lan-auth-store';

// Mock the store
vi.mock('../../../stores/lan-auth-store', () => ({
  useLanAuthStore: vi.fn(),
}));

// Mock i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'auth:pin.title': 'Enter PIN',
        'auth:pin.instruction': 'Enter the 4-digit PIN shown on the daemon console',
        'auth:pin.digit1': 'First digit',
        'auth:pin.digit2': 'Second digit',
        'auth:pin.digit3': 'Third digit',
        'auth:pin.digit4': 'Fourth digit',
        'auth:pin.submit': 'Submit',
        'auth:pin.submitting': 'Authenticating...',
        'auth:pin.invalidPin': 'Invalid PIN. Please try again.',
        'auth:pin.tooManyAttempts': 'Too many failed attempts. Please check the daemon console.',
        'auth:pin.networkError': 'Network error. Please ensure the daemon is running.',
        'auth:pin.pasteInstructions': 'You can paste a 4-digit code',
      };
      return translations[key] || key;
    },
  }),
}));

describe('PinEntryModal', () => {
  const mockClearAuth = vi.fn();
  const mockIncrementFailedAttempts = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
    (useLanAuthStore as any).mockReturnValue({
      needsAuth: true,
      clearAuth: mockClearAuth,
      failedAttempts: 0,
      incrementFailedAttempts: mockIncrementFailedAttempts,
    });
  });

  it('should not render when needsAuth is false', () => {
    (useLanAuthStore as any).mockReturnValue({
      needsAuth: false,
      clearAuth: mockClearAuth,
      failedAttempts: 0,
      incrementFailedAttempts: mockIncrementFailedAttempts,
    });

    const { container } = render(<PinEntryModal />);
    expect(container.firstChild).toBeNull();
  });

  it('should render when needsAuth is true', () => {
    render(<PinEntryModal />);
    expect(screen.getByText('Enter PIN')).toBeInTheDocument();
    expect(screen.getByText('Enter the 4-digit PIN shown on the daemon console')).toBeInTheDocument();
  });

  it('should render 4 input fields', () => {
    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');
    expect(inputs).toHaveLength(4);
  });

  it('should auto-advance to next field when digit is entered', async () => {
    const user = userEvent.setup();
    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '1');
    expect(inputs[1]).toHaveFocus();

    await user.type(inputs[1], '2');
    expect(inputs[2]).toHaveFocus();

    await user.type(inputs[2], '3');
    expect(inputs[3]).toHaveFocus();
  });

  it('should move to previous field on backspace in empty field', async () => {
    const user = userEvent.setup();
    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '1');
    await user.type(inputs[1], '2');

    // Now at input[2], backspace should go to input[1]
    await user.keyboard('{Backspace}');
    expect(inputs[1]).toHaveFocus();
  });

  it('should handle paste of 4-digit code', async () => {
    const user = userEvent.setup();
    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];

    await user.click(inputs[0]);
    await user.paste('1234');

    expect(inputs[0]).toHaveValue('1');
    expect(inputs[1]).toHaveValue('2');
    expect(inputs[2]).toHaveValue('3');
    expect(inputs[3]).toHaveValue('4');
  });

  it('should disable submit button when PIN is incomplete', () => {
    render(<PinEntryModal />);
    const submitButton = screen.getByRole('button', { name: /submit/i });
    expect(submitButton).toBeDisabled();
  });

  it('should enable submit button when all 4 digits are entered', async () => {
    const user = userEvent.setup();
    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');
    const submitButton = screen.getByRole('button', { name: /submit/i });

    await user.type(inputs[0], '1');
    await user.type(inputs[1], '2');
    await user.type(inputs[2], '3');
    await user.type(inputs[3], '4');

    expect(submitButton).not.toBeDisabled();
  });

  it('should submit PIN and call clearAuth on success', async () => {
    const user = userEvent.setup();
    const mockReload = vi.fn();
    Object.defineProperty(window, 'location', {
      value: { reload: mockReload },
      writable: true,
    });

    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
    });

    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '1');
    await user.type(inputs[1], '2');
    await user.type(inputs[2], '3');
    await user.type(inputs[3], '4');

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8080/auth?pin=1234',
        expect.objectContaining({
          method: 'GET',
          credentials: 'include',
        })
      );
      expect(mockClearAuth).toHaveBeenCalled();
    });
  });

  it('should show error message on failed authentication', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
    });

    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '9');
    await user.type(inputs[1], '9');
    await user.type(inputs[2], '9');
    await user.type(inputs[3], '9');

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid PIN. Please try again.')).toBeInTheDocument();
      expect(mockIncrementFailedAttempts).toHaveBeenCalled();
    });
  });

  it('should show network error message on fetch failure', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '1');
    await user.type(inputs[1], '2');
    await user.type(inputs[2], '3');
    await user.type(inputs[3], '4');

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Network error. Please ensure the daemon is running.')).toBeInTheDocument();
      expect(mockIncrementFailedAttempts).toHaveBeenCalled();
    });
  });

  it('should show "too many attempts" message after 3 failed attempts', async () => {
    (useLanAuthStore as any).mockReturnValue({
      needsAuth: true,
      clearAuth: mockClearAuth,
      failedAttempts: 3,
      incrementFailedAttempts: mockIncrementFailedAttempts,
    });

    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
    });

    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox');

    await user.type(inputs[0], '9');
    await user.type(inputs[1], '9');
    await user.type(inputs[2], '9');
    await user.type(inputs[3], '9');

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Too many failed attempts. Please check the daemon console.')).toBeInTheDocument();
    });
  });

  it('should clear PIN fields after failed attempt', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValueOnce({
      ok: false,
    });

    render(<PinEntryModal />);
    const inputs = screen.getAllByRole('textbox') as HTMLInputElement[];

    await user.type(inputs[0], '1');
    await user.type(inputs[1], '2');
    await user.type(inputs[2], '3');
    await user.type(inputs[3], '4');

    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(inputs[0]).toHaveValue('');
      expect(inputs[1]).toHaveValue('');
      expect(inputs[2]).toHaveValue('');
      expect(inputs[3]).toHaveValue('');
    });
  });
});
