import type { ReactNode } from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  icon:        ReactNode;
  title:       string;
  description?: string;
  action?:     {
    label:   string;
    onClick: () => void;
  };
  className?:  string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={['empty-state', className ?? ''].filter(Boolean).join(' ')}
      role="status"
    >
      <div className="empty-state__icon" aria-hidden="true">
        {icon}
      </div>

      <p className="empty-state__title">{title}</p>

      {description && (
        <p className="empty-state__desc">{description}</p>
      )}

      {action && (
        <Button
          variant="secondary"
          size="sm"
          onClick={action.onClick}
          className="empty-state__action"
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 24px;
  text-align: center;
  color: var(--color-text-muted);
}

.empty-state__icon {
  color: var(--color-border);
  margin-bottom: 4px;
  opacity: 0.8;
}

.empty-state__title {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.empty-state__desc {
  color: var(--color-text-muted);
  font-size: 13px;
  line-height: 1.5;
  max-width: 320px;
  margin: 0;
}

.empty-state__action {
  margin-top: 6px;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('empty-state-styles')) {
  const el = document.createElement('style');
  el.id = 'empty-state-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
