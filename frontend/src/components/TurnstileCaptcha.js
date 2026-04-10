/**
 * Cloudflare Turnstile CAPTCHA Component
 * 
 * Wraps @marsidev/react-turnstile with Drops Curated styling
 * and unified token handling.
 */

import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Turnstile as TurnstileWidget } from '@marsidev/react-turnstile';

const SITE_KEY = process.env.REACT_APP_TURNSTILE_SITE_KEY || '';

/**
 * TurnstileCaptcha Component
 * 
 * @param {Object} props
 * @param {function} props.onVerify - Callback when verification succeeds (receives token)
 * @param {function} props.onError - Callback when verification fails
 * @param {function} props.onExpire - Callback when token expires
 * @param {'light'|'dark'|'auto'} props.theme - Widget theme
 * @param {'normal'|'compact'|'invisible'} props.size - Widget size
 * @param {string} props.className - Additional CSS classes
 */
const TurnstileCaptcha = forwardRef(({ 
  onVerify, 
  onError, 
  onExpire,
  theme = 'dark',
  size = 'normal',
  className = ''
}, ref) => {
  const turnstileRef = useRef(null);

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    reset: () => turnstileRef.current?.reset(),
    getToken: () => turnstileRef.current?.getResponse(),
    execute: () => turnstileRef.current?.execute(),
  }));

  // Handle dev mode (no site key)
  useEffect(() => {
    if (!SITE_KEY && onVerify) {
      console.warn('[Turnstile] No site key configured - CAPTCHA disabled');
      onVerify('dev_mode_skip_captcha');
    }
  }, [onVerify]);

  // Don't render widget if no site key (development mode)
  if (!SITE_KEY) {
    return null;
  }

  return (
    <div className={`turnstile-container ${className}`}>
      <TurnstileWidget
        ref={turnstileRef}
        siteKey={SITE_KEY}
        onSuccess={(token) => {
          console.log('[Turnstile] Verification successful');
          onVerify?.(token);
        }}
        onError={(error) => {
          console.error('[Turnstile] Error:', error);
          onError?.(error);
        }}
        onExpire={() => {
          console.warn('[Turnstile] Token expired');
          onExpire?.();
        }}
        options={{
          theme,
          size,
        }}
      />
    </div>
  );
});

TurnstileCaptcha.displayName = 'TurnstileCaptcha';

/**
 * Invisible Turnstile for seamless protection
 * Call execute() to trigger verification
 */
export const InvisibleTurnstile = forwardRef(({ onVerify, onError }, ref) => {
  return (
    <TurnstileCaptcha
      ref={ref}
      onVerify={onVerify}
      onError={onError}
      size="invisible"
    />
  );
});

InvisibleTurnstile.displayName = 'InvisibleTurnstile';

export default TurnstileCaptcha;
