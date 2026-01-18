# Authentication Components

This directory contains authentication-related UI components for the Auto Claude frontend.

## Components

### PinEntryModal

A full-screen modal overlay for PIN authentication when LAN access requires authentication.

#### Features

- **4-digit PIN entry**: Separate input fields for each digit
- **Auto-focus**: First field is automatically focused when modal opens
- **Auto-advance**: Automatically moves to next field when a digit is entered
- **Smart backspace**: Backspace in empty field moves to previous field
- **Paste support**: Can paste a 4-digit code which distributes across all fields
- **Submit validation**: Submit button only enabled when all 4 digits are filled
- **Loading state**: Shows loading spinner during authentication
- **Error handling**: Displays error messages for failed attempts
- **Failed attempts tracking**: Tracks and displays number of failed attempts
- **Dark theme**: Matches the existing design system
- **Mobile-friendly**: Large touch targets for mobile devices
- **Accessibility**: Proper ARIA labels and keyboard navigation

#### Usage

The `PinEntryModal` is automatically rendered in `App.tsx` and displays when `useLanAuthStore().needsAuth === true`.

```tsx
import { PinEntryModal } from './components/auth';

function App() {
  return (
    <div>
      {/* ... other components ... */}
      <PinEntryModal />
    </div>
  );
}
```

#### Store Integration

The component uses the `useLanAuthStore` from Zustand to manage authentication state:

```typescript
import { useLanAuthStore } from '../../stores/lan-auth-store';

// In component
const {
  needsAuth,           // Whether PIN entry is required
  clearAuth,           // Clear auth requirement (after success)
  failedAttempts,      // Number of failed attempts
  incrementFailedAttempts  // Increment failed counter
} = useLanAuthStore();
```

#### Authentication Flow

1. User enters 4-digit PIN in separate input fields
2. On submit, makes GET request to `http://localhost:8080/auth?pin=XXXX`
3. Server validates PIN and sets authentication cookie
4. On success:
   - `clearAuth()` is called to hide the modal
   - Page reloads to apply authenticated state
5. On failure:
   - Failed attempts counter increments
   - Error message is displayed
   - PIN fields are cleared for retry
   - First field is re-focused

#### Translation Keys

All user-facing text uses i18n translation keys from the `auth` namespace:

```json
{
  "pin": {
    "title": "Enter PIN",
    "instruction": "Enter the 4-digit PIN shown on the daemon console",
    "digit1": "First digit",
    "digit2": "Second digit",
    "digit3": "Third digit",
    "digit4": "Fourth digit",
    "submit": "Submit",
    "submitting": "Authenticating...",
    "invalidPin": "Invalid PIN. Please try again.",
    "tooManyAttempts": "Too many failed attempts. Please check the daemon console.",
    "error": "Authentication failed",
    "networkError": "Network error. Please ensure the daemon is running.",
    "pasteInstructions": "You can paste a 4-digit code"
  }
}
```

Translation files are located in:
- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/shared/i18n/locales/en/auth.json` (English)
- `/Users/tinnguyen/Auto-Claude/apps/frontend/src/shared/i18n/locales/fr/auth.json` (French)

#### Keyboard Navigation

- **Arrow keys**: Not used (PIN entry uses single-character fields)
- **Tab**: Moves to next field
- **Shift+Tab**: Moves to previous field
- **Backspace**: Deletes current digit, or moves to previous field if empty
- **Enter**: Submits PIN when all 4 digits are filled
- **Paste** (Ctrl/Cmd+V): Distributes 4-digit code across all fields

#### Mobile Support

- Uses `inputMode="numeric"` for numeric keyboard on mobile
- Large touch targets (56px / 3.5rem height)
- Prevents zoom on input focus

#### Error States

The component displays different error messages based on the failure type:

1. **Invalid PIN**: "Invalid PIN. Please try again."
2. **Too many attempts**: "Too many failed attempts. Please check the daemon console."
3. **Network error**: "Network error. Please ensure the daemon is running."

#### Styling

The component uses Tailwind CSS classes and follows the existing design system:

- Dark theme by default
- Primary color for active states
- Destructive color for errors
- Smooth transitions and animations
- Consistent spacing and typography

#### Testing

To test the PIN entry modal:

1. Set `needsAuth: true` in the LAN auth store
2. Enter a valid 4-digit PIN
3. Submit and verify authentication
4. Test error states by entering invalid PINs
5. Test paste functionality with a 4-digit code
6. Test keyboard navigation (Tab, Backspace, Enter)

#### Implementation Notes

- The modal cannot be dismissed by clicking outside or pressing Escape (authentication is required)
- PIN fields are automatically cleared on submission failure
- The first field is auto-focused on modal open and after failed attempts
- Failed attempts counter is reset on successful authentication
- Component automatically reloads the page on successful authentication to apply the new auth state

## Future Enhancements

Potential improvements for future versions:

- [ ] Rate limiting UI feedback
- [ ] Biometric authentication support
- [ ] Remember device option
- [ ] PIN strength indicator
- [ ] Session timeout warning
- [ ] Multi-factor authentication support
