import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Spinner } from './Spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize    = 'sm' | 'md' | 'lg';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?:    ButtonSize;
  loading?: boolean;
  icon?:    ReactNode;
  children?: ReactNode;
}

export function Button({
  variant  = 'secondary',
  size     = 'md',
  loading  = false,
  icon,
  children,
  disabled,
  className,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading;

  return (
    <button
      className={[
        'btn',
        `btn--${variant}`,
        `btn--${size}`,
        loading ? 'btn--loading' : '',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
      disabled={isDisabled}
      aria-disabled={isDisabled}
      aria-busy={loading}
      {...rest}
    >
      {loading ? (
        <Spinner size="sm" />
      ) : (
        icon && <span className="btn__icon" aria-hidden="true">{icon}</span>
      )}
      {children && <span>{children}</span>}
    </button>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-radius: var(--radius-md);
  font-weight: 600;
  letter-spacing: -0.01em;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--transition-fast),
    border-color var(--transition-fast),
    color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
  border: 1px solid transparent;
  outline: none;
  text-decoration: none;
}

.btn:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}

.btn:not(:disabled):active {
  transform: translateY(1px);
}

.btn:disabled,
.btn[aria-disabled="true"] {
  cursor: not-allowed;
  opacity: 0.45;
  transform: none;
}

/* Size */
.btn--sm { min-height: 30px; padding: 0 10px; font-size: 12px; }
.btn--md { min-height: 36px; padding: 0 14px; font-size: 13px; }
.btn--lg { min-height: 44px; padding: 0 20px; font-size: 14px; }

/* Variants */
.btn--primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}
.btn--primary:not(:disabled):hover {
  background: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
  box-shadow: 0 0 0 3px var(--color-accent-subtle);
}

.btn--secondary {
  background: var(--color-surface-raised);
  border-color: var(--color-border);
  color: var(--color-text-secondary);
}
.btn--secondary:not(:disabled):hover {
  border-color: var(--color-text-muted);
  color: var(--color-text-primary);
  background: #191f27;
}

.btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--color-text-secondary);
}
.btn--ghost:not(:disabled):hover {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
}

.btn--danger {
  background: var(--color-danger-subtle);
  border-color: rgba(248, 81, 73, 0.3);
  color: var(--color-danger);
}
.btn--danger:not(:disabled):hover {
  background: rgba(248, 81, 73, 0.2);
}

.btn__icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('btn-styles')) {
  const el = document.createElement('style');
  el.id = 'btn-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
