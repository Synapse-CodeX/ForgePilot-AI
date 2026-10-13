import type { ReactNode } from 'react';

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info';
export type BadgeSize    = 'sm' | 'md';

interface BadgeProps {
  variant?: BadgeVariant;
  size?:    BadgeSize;
  children: ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'badge--default',
  success: 'badge--success',
  warning: 'badge--warning',
  danger:  'badge--danger',
  info:    'badge--info',
};

export function Badge({
  variant  = 'default',
  size     = 'sm',
  children,
  className,
}: BadgeProps) {
  return (
    <span
      className={[
        'badge',
        variantStyles[variant],
        size === 'md' ? 'badge--md' : '',
        className ?? '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </span>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 7px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.6;
  white-space: nowrap;
}

.badge--md {
  padding: 4px 10px;
  font-size: 12px;
}

.badge--default {
  background: var(--color-surface-raised);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
}

.badge--success {
  background: var(--color-success-subtle);
  color: var(--color-success);
  border: 1px solid rgba(63, 185, 80, 0.25);
}

.badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
  border: 1px solid rgba(210, 153, 34, 0.25);
}

.badge--danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
  border: 1px solid rgba(248, 81, 73, 0.25);
}

.badge--info {
  background: var(--color-info-subtle);
  color: var(--color-info);
  border: 1px solid rgba(121, 192, 255, 0.25);
}
`;

// Inject once
if (typeof document !== 'undefined' && !document.getElementById('badge-styles')) {
  const el = document.createElement('style');
  el.id = 'badge-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
