import { useState } from 'react';
import { AlertTriangle, X, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  error:     string;
  onRetry?:  () => void;
  className?: string;
}

export function ErrorBanner({ error, onRetry, className }: ErrorBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div
      className={['error-banner', className ?? ''].filter(Boolean).join(' ')}
      role="alert"
      aria-live="assertive"
    >
      <AlertTriangle size={16} className="error-banner__icon" aria-hidden="true" />

      <p className="error-banner__message">{error}</p>

      <div className="error-banner__actions">
        {onRetry && (
          <button
            className="error-banner__btn"
            onClick={onRetry}
            aria-label="Retry"
            title="Retry"
          >
            <RefreshCw size={13} />
            <span>Retry</span>
          </button>
        )}

        <button
          className="error-banner__btn error-banner__close"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss error"
          title="Dismiss"
        >
          <X size={13} />
        </button>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-danger-subtle);
  border: 1px solid rgba(248, 81, 73, 0.25);
  animation: fadeIn 200ms ease;
}

.error-banner__icon {
  color: var(--color-danger);
  flex-shrink: 0;
  margin-top: 1px;
}

.error-banner__message {
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
  flex: 1;
  margin: 0;
}

.error-banner__actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.error-banner__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 500;
  color: var(--color-danger);
  background: none;
  border: none;
  cursor: pointer;
  transition: background var(--transition-fast);
}

.error-banner__btn:hover {
  background: rgba(248, 81, 73, 0.15);
}

.error-banner__close {
  padding: 4px;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('error-banner-styles')) {
  const el = document.createElement('style');
  el.id = 'error-banner-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
