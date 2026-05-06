/**
 * API base includes `/api` suffix.
 * Set NEXT_PUBLIC_API_URL to backend origin only, e.g. https://market-scout-emg1.onrender.com
 */
export function getApiBase(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (explicit) {
    const base = explicit.replace(/\/$/, '');
    return base.endsWith('/api') ? base : `${base}/api`;
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') {
      return '/api';
    }
    return 'https://market-scout-emg1.onrender.com/api';
  }
  return '/api';
}

/** Origin for static files (PDFs under /reports). */
export function getBackendOrigin(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (explicit) {
    return explicit.replace(/\/$/, '').replace(/\/api$/, '');
  }
  if (typeof window !== 'undefined') {
    const h = window.location.hostname;
    if (h === 'localhost' || h === '127.0.0.1') {
      return 'http://localhost:8000';
    }
  }
  return 'https://market-scout-emg1.onrender.com';
}
