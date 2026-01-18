import { useState, useRef, useEffect, KeyboardEvent, ClipboardEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { Lock, AlertCircle, Loader2 } from 'lucide-react';
import { useLanAuthStore } from '../../stores/lan-auth-store';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';

/**
 * PIN Entry Modal Component
 *
 * Renders a full-screen modal overlay for PIN authentication when LAN auth is required.
 * Features:
 * - 4 separate input fields for PIN digits
 * - Auto-focus on first field on mount
 * - Auto-advance to next field when digit is entered
 * - Backspace in empty field moves to previous field
 * - Paste support for 4-digit codes
 * - Submit button enabled only when all 4 digits are filled
 * - Loading state during submission
 * - Error display for failed attempts
 */
export function PinEntryModal() {
  const { t } = useTranslation(['auth', 'common']);
  const { needsAuth, clearAuth, failedAttempts, incrementFailedAttempts } = useLanAuthStore();

  const [digits, setDigits] = useState<string[]>(['', '', '', '']);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Refs for each input field
  const inputRefs = [
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
  ];

  // Auto-focus first field when modal opens
  useEffect(() => {
    if (needsAuth && inputRefs[0].current) {
      // Small delay to ensure modal is fully rendered
      setTimeout(() => {
        inputRefs[0].current?.focus();
      }, 100);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needsAuth]);

  // Reset state when modal opens
  useEffect(() => {
    if (needsAuth) {
      setDigits(['', '', '', '']);
      setError(null);
      setIsSubmitting(false);
    }
  }, [needsAuth]);

  /**
   * Handle digit input change
   */
  const handleDigitChange = (index: number, value: string) => {
    // Only allow single digits 0-9
    const sanitized = value.replace(/[^0-9]/g, '').slice(0, 1);

    const newDigits = [...digits];
    newDigits[index] = sanitized;
    setDigits(newDigits);
    setError(null); // Clear error on input

    // Auto-advance to next field if digit was entered
    if (sanitized && index < 3) {
      inputRefs[index + 1].current?.focus();
    }
  };

  /**
   * Handle keydown for backspace navigation
   */
  const handleKeyDown = (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      // Move to previous field if current is empty
      inputRefs[index - 1].current?.focus();
    } else if (e.key === 'Enter' && isPinComplete) {
      // Submit on Enter if PIN is complete
      handleSubmit();
    }
  };

  /**
   * Handle paste event to distribute 4-digit code across fields
   */
  const handlePaste = (e: ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/[^0-9]/g, '');

    if (pastedData.length === 4) {
      const newDigits = pastedData.split('');
      setDigits(newDigits);
      setError(null);
      // Focus the last input
      inputRefs[3].current?.focus();
    }
  };

  /**
   * Check if all 4 digits are filled
   */
  const isPinComplete = digits.every((d) => d !== '');

  /**
   * Submit PIN for authentication
   */
  const handleSubmit = async () => {
    if (!isPinComplete || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    const pin = digits.join('');

    try {
      // Redirect to /auth endpoint with PIN as query parameter
      // The server will validate and set the auth cookie
      const response = await fetch(`http://localhost:8080/auth?pin=${pin}`, {
        method: 'GET',
        credentials: 'include', // Include cookies in request
      });

      if (response.ok) {
        // Success - clear auth requirement
        clearAuth();
        // Optionally reload or update app state
        window.location.reload();
      } else {
        // Failed authentication
        incrementFailedAttempts();

        if (failedAttempts >= 2) {
          setError(t('auth:pin.tooManyAttempts'));
        } else {
          setError(t('auth:pin.invalidPin'));
        }

        // Clear PIN fields for retry
        setDigits(['', '', '', '']);
        inputRefs[0].current?.focus();
      }
    } catch (_err) {
      // Network or other error
      setError(t('auth:pin.networkError'));
      incrementFailedAttempts();
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!needsAuth) return null;

  return (
    <Dialog open={needsAuth} onOpenChange={() => {}}>
      <DialogContent
        className="sm:max-w-md"
        hideCloseButton
        onPointerDownOutside={(e) => e.preventDefault()}
        onEscapeKeyDown={(e) => e.preventDefault()}
      >
        {/* Logo/Icon */}
        <div className="flex justify-center mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Lock className="h-8 w-8 text-primary" />
          </div>
        </div>

        <DialogHeader>
          <DialogTitle className="text-center">{t('auth:pin.title')}</DialogTitle>
          <DialogDescription className="text-center">
            {t('auth:pin.instruction')}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* PIN Input Fields */}
          <div className="flex justify-center gap-3">
            {digits.map((digit, index) => (
              <input
                key={index}
                ref={inputRefs[index]}
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                maxLength={1}
                value={digit}
                onChange={(e) => handleDigitChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={index === 0 ? handlePaste : undefined}
                aria-label={t(`auth:pin.digit${index + 1}` as 'auth:pin.digit1' | 'auth:pin.digit2' | 'auth:pin.digit3' | 'auth:pin.digit4')}
                disabled={isSubmitting}
                className={cn(
                  'h-14 w-14 rounded-lg border-2 text-center text-2xl font-bold',
                  'bg-card text-foreground',
                  'transition-all duration-200',
                  'focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  digit ? 'border-primary' : 'border-border',
                  error && 'border-destructive focus:ring-destructive'
                )}
              />
            ))}
          </div>

          {/* Paste hint */}
          <p className="text-xs text-center text-muted-foreground">
            {t('auth:pin.pasteInstructions')}
          </p>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Submit Button */}
          <Button
            onClick={handleSubmit}
            disabled={!isPinComplete || isSubmitting}
            className="w-full h-12 text-base"
            size="lg"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {t('auth:pin.submitting')}
              </>
            ) : (
              t('auth:pin.submit')
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
