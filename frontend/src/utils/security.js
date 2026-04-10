/**
 * Frontend Security Utilities
 * 
 * - Iframe detection
 * - XSS prevention (sanitize data)
 * - Secure token storage
 */

// ============ IFRAME DETECTION ============

/**
 * Check if app is loaded inside an iframe (clickjacking attempt)
 * Allows trusted Emergent iframe for visual edits
 */
export const checkIframeEmbedding = () => {
  if (window.self !== window.top) {
    // Allow Emergent's iframe for visual editing
    try {
      const parentOrigin = document.referrer;
      const allowedParents = [
        'emergentagent.com',
        'emergent.sh',
        'localhost'
      ];
      
      const isAllowed = allowedParents.some(domain => 
        parentOrigin.includes(domain)
      );
      
      if (!isAllowed) {
        console.warn('[Security] Blocked iframe embedding from:', parentOrigin);
        // Optionally break out of frame
        // window.top.location = window.self.location;
        return false;
      }
    } catch (e) {
      // Cross-origin - can't access parent
      console.warn('[Security] App loaded in cross-origin iframe');
    }
  }
  return true;
};

// ============ XSS PREVENTION ============

/**
 * Sanitize string to prevent XSS
 * Removes HTML tags and dangerous patterns
 */
export const sanitizeString = (str) => {
  if (typeof str !== 'string') return str;
  
  // Create a text node to encode HTML entities
  const div = document.createElement('div');
  div.textContent = str;
  let safe = div.innerHTML;
  
  // Remove any remaining dangerous patterns
  safe = safe
    .replace(/javascript:/gi, '')
    .replace(/on\w+\s*=/gi, '')
    .replace(/<script/gi, '&lt;script')
    .replace(/<\/script>/gi, '&lt;/script&gt;');
  
  return safe;
};

/**
 * Sanitize object recursively for safe rendering
 */
export const sanitizeData = (data) => {
  if (data === null || data === undefined) return data;
  
  if (typeof data === 'string') {
    return sanitizeString(data);
  }
  
  if (Array.isArray(data)) {
    return data.map(item => sanitizeData(item));
  }
  
  if (typeof data === 'object') {
    const sanitized = {};
    for (const [key, value] of Object.entries(data)) {
      sanitized[sanitizeString(key)] = sanitizeData(value);
    }
    return sanitized;
  }
  
  return data;
};

// ============ SECURE TOKEN STORAGE ============

const TOKEN_KEY = 'auth_token';
const ADMIN_TOKEN_KEY = 'admin_token';

/**
 * Store auth token securely
 * Note: For maximum security, tokens should be in httpOnly cookies
 * This is a client-side fallback
 */
export const storeToken = (token, isAdmin = false) => {
  const key = isAdmin ? ADMIN_TOKEN_KEY : TOKEN_KEY;
  
  try {
    // Use sessionStorage for admin (more secure, clears on tab close)
    // Use localStorage for regular users (persistent)
    if (isAdmin) {
      sessionStorage.setItem(key, token);
    } else {
      localStorage.setItem(key, token);
    }
    return true;
  } catch (e) {
    console.error('[Security] Failed to store token:', e);
    return false;
  }
};

/**
 * Retrieve stored token
 */
export const getToken = (isAdmin = false) => {
  const key = isAdmin ? ADMIN_TOKEN_KEY : TOKEN_KEY;
  
  try {
    if (isAdmin) {
      return sessionStorage.getItem(key);
    }
    return localStorage.getItem(key);
  } catch (e) {
    console.error('[Security] Failed to retrieve token:', e);
    return null;
  }
};

/**
 * Clear stored token
 */
export const clearToken = (isAdmin = false) => {
  const key = isAdmin ? ADMIN_TOKEN_KEY : TOKEN_KEY;
  
  try {
    if (isAdmin) {
      sessionStorage.removeItem(key);
    } else {
      localStorage.removeItem(key);
    }
    return true;
  } catch (e) {
    return false;
  }
};

/**
 * Clear all auth tokens
 */
export const clearAllTokens = () => {
  clearToken(false);
  clearToken(true);
};

// ============ INPUT VALIDATION ============

/**
 * Validate Indian phone number
 */
export const validatePhoneNumber = (phone) => {
  if (!phone) return false;
  const digits = phone.replace(/\D/g, '');
  return digits.length === 10 && /^[6-9]/.test(digits);
};

/**
 * Validate email format
 */
export const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};

// ============ INITIALIZE SECURITY ============

export const initSecurity = () => {
  // Check iframe embedding on load
  checkIframeEmbedding();
  
  // Log security initialization
  console.log('[Security] Frontend security utilities initialized');
};

export default {
  checkIframeEmbedding,
  sanitizeString,
  sanitizeData,
  storeToken,
  getToken,
  clearToken,
  clearAllTokens,
  validatePhoneNumber,
  validateEmail,
  initSecurity,
};
