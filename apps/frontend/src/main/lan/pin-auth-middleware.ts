/**
 * PIN Authentication Middleware
 *
 * HTTP middleware for PIN-based authentication with cookie support.
 * Integrates with LanAccessModule for PIN validation.
 */

import { getLanAccessModule } from './lan-module';

/**
 * Middleware function signature
 */
export type Middleware = (request: Request) => Response | void | Promise<Response | void>;

/**
 * Check if the request is from localhost
 */
function isLocalhost(request: Request): boolean {
  const url = new URL(request.url);
  const hostname = url.hostname;

  return (
    hostname === 'localhost' ||
    hostname === '127.0.0.1' ||
    hostname === '::1' ||
    hostname === '[::1]'
  );
}

/**
 * Parse cookies from request headers
 */
function parseCookies(request: Request): Map<string, string> {
  const cookieHeader = request.headers.get('cookie');
  const cookies = new Map<string, string>();

  if (!cookieHeader) {
    return cookies;
  }

  // Parse cookie header: "name1=value1; name2=value2"
  const parts = cookieHeader.split(';');
  for (const part of parts) {
    const [name, ...valueParts] = part.split('=');
    if (name && valueParts.length > 0) {
      const trimmedName = name.trim();
      const value = valueParts.join('=').trim(); // Handle values with '=' in them
      cookies.set(trimmedName, value);
    }
  }

  return cookies;
}

/**
 * Get PIN from query parameter
 */
function getPinFromQuery(request: Request): string | null {
  const url = new URL(request.url);
  return url.searchParams.get('pin');
}

/**
 * Create a clean URL without the pin parameter
 */
function getCleanUrl(request: Request): string {
  const url = new URL(request.url);
  url.searchParams.delete('pin');
  return url.toString();
}

/**
 * Create Set-Cookie header value
 */
function createCookieHeader(pin: string): string {
  const maxAge = 30 * 24 * 60 * 60; // 30 days in seconds (2,592,000)

  return [
    `nightshift_lan_auth=${pin}`,
    `Max-Age=${maxAge}`,
    'HttpOnly',
    'SameSite=Lax',
    'Path=/',
  ].join('; ');
}

/**
 * Generate the PIN entry HTML page
 */
function generatePinEntryPage(showError: boolean = false): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>PIN Authentication</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      color: #e0e0e0;
    }

    .container {
      width: 100%;
      max-width: 400px;
      background: rgba(255, 255, 255, 0.05);
      border-radius: 20px;
      padding: 40px 30px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .logo {
      text-align: center;
      margin-bottom: 30px;
    }

    .logo svg {
      width: 60px;
      height: 60px;
      margin-bottom: 15px;
    }

    h1 {
      text-align: center;
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 10px;
      color: #fff;
    }

    .subtitle {
      text-align: center;
      font-size: 14px;
      color: rgba(255, 255, 255, 0.6);
      margin-bottom: 40px;
    }

    .pin-inputs {
      display: flex;
      gap: 12px;
      justify-content: center;
      margin-bottom: 30px;
    }

    .pin-input {
      width: 60px;
      height: 70px;
      font-size: 32px;
      font-weight: 600;
      text-align: center;
      background: rgba(255, 255, 255, 0.1);
      border: 2px solid rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      color: #fff;
      outline: none;
      transition: all 0.2s ease;
      caret-color: #4a9eff;
    }

    .pin-input:focus {
      border-color: #4a9eff;
      background: rgba(74, 158, 255, 0.1);
      box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.2);
    }

    .pin-input.filled {
      border-color: rgba(255, 255, 255, 0.3);
      background: rgba(255, 255, 255, 0.15);
    }

    .pin-input.error {
      border-color: #ff4757;
      background: rgba(255, 71, 87, 0.1);
      animation: shake 0.4s ease;
    }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-10px); }
      75% { transform: translateX(10px); }
    }

    .error-message {
      text-align: center;
      color: #ff4757;
      font-size: 14px;
      margin-bottom: 20px;
      min-height: 20px;
      font-weight: 500;
    }

    .submit-btn {
      width: 100%;
      padding: 16px;
      font-size: 16px;
      font-weight: 600;
      color: #fff;
      background: linear-gradient(135deg, #4a9eff 0%, #3b7dd6 100%);
      border: none;
      border-radius: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
      box-shadow: 0 4px 15px rgba(74, 158, 255, 0.3);
    }

    .submit-btn:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(74, 158, 255, 0.4);
    }

    .submit-btn:active:not(:disabled) {
      transform: translateY(0);
    }

    .submit-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .hint {
      text-align: center;
      margin-top: 20px;
      font-size: 13px;
      color: rgba(255, 255, 255, 0.4);
    }

    /* Mobile adjustments */
    @media (max-width: 480px) {
      .container {
        padding: 30px 20px;
      }

      .pin-input {
        width: 55px;
        height: 65px;
        font-size: 28px;
      }

      .pin-inputs {
        gap: 10px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">
      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M12 2L2 7v10c0 5.55 3.84 10.74 10 12 6.16-1.26 10-6.45 10-12V7l-10-5z"
              fill="url(#shield-gradient)" stroke="#4a9eff" stroke-width="1.5"/>
        <path d="M12 8v8M8 12h8" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
        <defs>
          <linearGradient id="shield-gradient" x1="2" y1="2" x2="22" y2="22">
            <stop offset="0%" stop-color="rgba(74, 158, 255, 0.3)"/>
            <stop offset="100%" stop-color="rgba(59, 125, 214, 0.3)"/>
          </linearGradient>
        </defs>
      </svg>
    </div>

    <h1>Enter PIN</h1>
    <p class="subtitle">Enter your 4-digit PIN to access this device</p>

    <form id="pin-form" method="GET">
      <div class="pin-inputs">
        <input type="text" inputmode="numeric" pattern="[0-9]" maxlength="1"
               class="pin-input" id="pin-1" autocomplete="off" autofocus>
        <input type="text" inputmode="numeric" pattern="[0-9]" maxlength="1"
               class="pin-input" id="pin-2" autocomplete="off">
        <input type="text" inputmode="numeric" pattern="[0-9]" maxlength="1"
               class="pin-input" id="pin-3" autocomplete="off">
        <input type="text" inputmode="numeric" pattern="[0-9]" maxlength="1"
               class="pin-input" id="pin-4" autocomplete="off">
      </div>

      <div class="error-message" id="error-message">${showError ? 'Invalid PIN. Please try again.' : ''}</div>

      <button type="submit" class="submit-btn" id="submit-btn" disabled>
        Unlock
      </button>

      <p class="hint">PIN will be remembered for 30 days</p>
    </form>
  </div>

  <script>
    (function() {
      const form = document.getElementById('pin-form');
      const inputs = Array.from(document.querySelectorAll('.pin-input'));
      const errorMessage = document.getElementById('error-message');
      const submitBtn = document.getElementById('submit-btn');

      // Focus first input
      inputs[0].focus();

      // Auto-advance on input
      inputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
          const value = e.target.value;

          // Only allow digits
          if (value && !/^[0-9]$/.test(value)) {
            e.target.value = '';
            return;
          }

          // Add filled class
          if (value) {
            e.target.classList.add('filled');
            e.target.classList.remove('error');
          } else {
            e.target.classList.remove('filled');
          }

          // Clear error on input
          errorMessage.textContent = '';
          inputs.forEach(inp => inp.classList.remove('error'));

          // Auto-advance to next input
          if (value && index < inputs.length - 1) {
            inputs[index + 1].focus();
            inputs[index + 1].select();
          }

          // Enable submit button when all fields filled
          updateSubmitButton();
        });

        // Handle backspace
        input.addEventListener('keydown', (e) => {
          if (e.key === 'Backspace') {
            if (!e.target.value && index > 0) {
              inputs[index - 1].focus();
              inputs[index - 1].select();
            }
          } else if (e.key === 'ArrowLeft' && index > 0) {
            inputs[index - 1].focus();
            inputs[index - 1].select();
          } else if (e.key === 'ArrowRight' && index < inputs.length - 1) {
            inputs[index + 1].focus();
            inputs[index + 1].select();
          }
        });
      });

      // Paste support
      inputs[0].addEventListener('paste', (e) => {
        e.preventDefault();
        const paste = (e.clipboardData || window.clipboardData).getData('text');
        const digits = paste.replace(/\\D/g, '').slice(0, 4);

        if (digits.length === 4) {
          digits.split('').forEach((digit, index) => {
            inputs[index].value = digit;
            inputs[index].classList.add('filled');
          });
          inputs[3].focus();
          updateSubmitButton();
        }
      });

      // Update submit button state
      function updateSubmitButton() {
        const allFilled = inputs.every(input => input.value.length === 1);
        submitBtn.disabled = !allFilled;
      }

      // Handle form submission
      form.addEventListener('submit', (e) => {
        e.preventDefault();

        const pin = inputs.map(input => input.value).join('');

        if (pin.length !== 4) {
          showError('Please enter all 4 digits');
          return;
        }

        // Submit to current URL with pin parameter
        const url = new URL(window.location.href);
        url.searchParams.set('pin', pin);
        window.location.href = url.toString();
      });

      // Show error
      function showError(message) {
        errorMessage.textContent = message;
        inputs.forEach(input => {
          input.classList.add('error');
          input.value = '';
          input.classList.remove('filled');
        });
        inputs[0].focus();
        updateSubmitButton();
      }

      // Auto-submit when all digits entered
      inputs[3].addEventListener('input', (e) => {
        if (e.target.value) {
          setTimeout(() => {
            if (!submitBtn.disabled) {
              form.dispatchEvent(new Event('submit'));
            }
          }, 300);
        }
      });
    })();
  </script>
</body>
</html>`;
}

/**
 * Create PIN authentication middleware
 *
 * @param enable Whether to enable authentication (false = no-op)
 * @returns Middleware function
 *
 * @example
 * ```typescript
 * import { pinAuthMiddleware } from './pin-auth-middleware';
 *
 * const middleware = pinAuthMiddleware(true);
 *
 * // In your HTTP server:
 * const response = await middleware(request);
 * if (response) {
 *   return response; // Authentication failed or redirect
 * }
 * // Continue to handler...
 * ```
 */
export function pinAuthMiddleware(enable: boolean): Middleware {
  if (!enable) {
    // Disabled - return no-op middleware
    return () => void 0;
  }

  return (request: Request): Response | void => {
    // 1. Localhost bypass
    if (isLocalhost(request)) {
      return void 0; // Authenticated - proceed to handler
    }

    const lanModule = getLanAccessModule();
    const cookies = parseCookies(request);
    const pinFromQuery = getPinFromQuery(request);

    // 2. Check for valid auth cookie
    const cookiePin = cookies.get('nightshift_lan_auth');
    if (cookiePin && lanModule.validatePin(cookiePin)) {
      return void 0; // Authenticated - proceed to handler
    }

    // 3. Check for PIN in query parameter
    if (pinFromQuery) {
      if (lanModule.validatePin(pinFromQuery)) {
        // Valid PIN - redirect to clean URL with cookie set
        const cleanUrl = getCleanUrl(request);
        const cookieHeader = createCookieHeader(pinFromQuery);

        return new Response(null, {
          status: 302,
          headers: {
            'Location': cleanUrl,
            'Set-Cookie': cookieHeader,
          },
        });
      } else {
        // Invalid PIN - show error page
        return new Response(generatePinEntryPage(true), {
          status: 401,
          headers: {
            'Content-Type': 'text/html; charset=utf-8',
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma': 'no-cache',
          },
        });
      }
    }

    // 4. No authentication - show PIN entry page
    return new Response(generatePinEntryPage(false), {
      status: 401,
      headers: {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-store, no-cache, must-revalidate',
        'Pragma': 'no-cache',
      },
    });
  };
}
