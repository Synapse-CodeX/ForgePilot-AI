import { History, GitBranch } from 'lucide-react';
import { EmptyState } from '../components/ui/EmptyState';

export function HistoryPage() {
  const navigate = (hash: string) => { window.location.hash = hash; };

  return (
    <div className="history-page">
      <header className="page-header">
        <h1 className="page-title">Repair History</h1>
        <p className="page-subtitle">
          Browse past repair runs and their outcomes.
        </p>
      </header>

      <div className="panel history-panel">
        <EmptyState
          icon={<History size={36} />}
          title="No repair history"
          description="No repair runs have been recorded yet. Start a new repair to see it appear here."
          action={{
            label:   'Start a repair',
            onClick: () => navigate('#/repair/new'),
          }}
        />

        <div className="history-panel__note">
          <GitBranch size={12} aria-hidden="true" />
          <span>
            History requires persistent storage on the backend. This section will populate
            automatically once the repair workflow endpoints are implemented.
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.history-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 820px;
  animation: fadeIn 250ms ease;
}

.history-panel {
  min-height: 320px;
  justify-content: center;
}

.history-panel__note {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 16px;
  margin: 0 -22px -22px;
  border-top: 1px solid var(--color-border-subtle);
  background: rgba(255,255,255,0.015);
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  line-height: 1.5;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('history-page-styles')) {
  const el = document.createElement('style');
  el.id = 'history-page-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
