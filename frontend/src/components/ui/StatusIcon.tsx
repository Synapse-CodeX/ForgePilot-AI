import {
  CheckCircle,
  XCircle,
  Clock,
  Loader,
  AlertTriangle,
} from 'lucide-react';

export type StatusValue = 'success' | 'failed' | 'running' | 'pending' | 'warning';

interface StatusIconProps {
  status:    StatusValue;
  size?:     number;
  className?: string;
}

const config: Record<StatusValue, { Icon: React.FC<{ size?: number; className?: string }>; color: string; label: string }> = {
  success: { Icon: CheckCircle,   color: 'var(--color-success)', label: 'Succeeded'  },
  failed:  { Icon: XCircle,       color: 'var(--color-danger)',  label: 'Failed'     },
  running: { Icon: Loader,        color: 'var(--color-accent)',  label: 'Running'    },
  pending: { Icon: Clock,         color: 'var(--color-text-muted)', label: 'Pending' },
  warning: { Icon: AlertTriangle, color: 'var(--color-warning)', label: 'Warning'   },
};

export function StatusIcon({ status, size = 16, className }: StatusIconProps) {
  const { Icon, color, label } = config[status];

  const isSpinning = status === 'running';

  return (
    <span
      role="img"
      aria-label={label}
      title={label}
      className={['status-icon', isSpinning ? 'status-icon--spin' : '', className ?? '']
        .filter(Boolean)
        .join(' ')}
      style={{ color, display: 'inline-flex', alignItems: 'center', flexShrink: 0 }}
    >
      <Icon size={size} />
    </span>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.status-icon--spin {
  animation: spin 1s linear infinite;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('status-icon-styles')) {
  const el = document.createElement('style');
  el.id = 'status-icon-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
