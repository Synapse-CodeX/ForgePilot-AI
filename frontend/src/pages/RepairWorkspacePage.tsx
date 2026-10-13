import { useState } from 'react';
import { ArrowLeft, GitBranch, Hash, ServerOff } from 'lucide-react';
import type { RepairWorkflowResult } from '../types/api';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { WorkflowTimeline } from '../components/repair/WorkflowTimeline';
import { DiagnosisPanel } from '../components/repair/DiagnosisPanel';
import { PatchPanel } from '../components/repair/PatchPanel';
import { ValidationPanel } from '../components/repair/ValidationPanel';

interface RepairWorkspacePageProps {
  jobId?: string;
}

/** Map workflow status to badge variant */
function statusBadge(status: RepairWorkflowResult['status']) {
  if (status === 'succeeded')        return 'success' as const;
  if (status === 'validation_failed') return 'warning' as const;
  return 'danger' as const;
}

// For now there's no real data since the endpoint doesn't exist.
// The workspace renders its structure with empty panels.
const PLACEHOLDER_JOB_ID = '—';

export function RepairWorkspacePage({ jobId }: RepairWorkspacePageProps) {
  const navigate = (hash: string) => { window.location.hash = hash; };

  // Result state: typed as RepairWorkflowResult | null so it can be populated when an endpoint exists
  const [result] = useState<RepairWorkflowResult | null>(null);

  return (
    <div className="workspace-page">
      {/* Header */}
      <header className="workspace-header">
        <Button
          variant="ghost"
          size="sm"
          icon={<ArrowLeft size={14} />}
          onClick={() => navigate('#/')}
          aria-label="Back to home"
        >
          Back
        </Button>

        <div className="workspace-header__title">
          <div className="workspace-header__id">
            <GitBranch size={14} aria-hidden="true" />
            <span className="workspace-id-text">
              {jobId ?? PLACEHOLDER_JOB_ID}
            </span>
          </div>

          {result ? (
            <>
              <h1 className="workspace-repo">
                {result.repository_full_name}
              </h1>
              <div className="workspace-header__badges">
                <Badge variant="default">
                  <Hash size={10} aria-hidden="true" />
                  #{result.issue_number}
                </Badge>
                <Badge variant={statusBadge(result.status)} size="md">
                  {result.status.replace('_', ' ')}
                </Badge>
              </div>
            </>
          ) : (
            <div className="workspace-unavail">
              <ServerOff size={14} aria-hidden="true" />
              <span>Repair API not yet available — workspace preview</span>
            </div>
          )}
        </div>
      </header>

      {/* Two-column layout */}
      <div className="workspace-layout">
        {/* Left panel */}
        <div className="workspace-left">
          {/* Stages */}
          <section className="workspace-panel" aria-label="Workflow stages">
            <h2 className="workspace-panel__title">Workflow Stages</h2>
            <WorkflowTimeline stages={result?.stages} />
          </section>

          {/* Diagnosis */}
          <section className="workspace-panel" aria-label="Root cause diagnosis">
            <h2 className="workspace-panel__title">Diagnosis</h2>
            <DiagnosisPanel analysis={result?.root_cause} />
          </section>
        </div>

        {/* Right panel */}
        <div className="workspace-right">
          {/* Patch */}
          <section className="workspace-panel" aria-label="Patch proposal">
            <h2 className="workspace-panel__title">Patch</h2>
            <PatchPanel
              proposal={result?.patch_proposal}
              application={result?.patch_application}
            />
          </section>

          {/* Validation */}
          <section className="workspace-panel" aria-label="Validation results">
            <h2 className="workspace-panel__title">Validation</h2>
            <ValidationPanel report={result?.validation_report} />
          </section>
        </div>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.workspace-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fadeIn 250ms ease;
}

.workspace-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border-subtle);
  flex-wrap: wrap;
}

.workspace-header__title {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.workspace-header__id {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-muted);
}

.workspace-id-text {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.workspace-repo {
  font-size: 18px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-header__badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.workspace-unavail {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--color-text-muted);
  font-style: italic;
}

/* Two-column layout */
.workspace-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  align-items: start;
}

.workspace-left,
.workspace-right {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.workspace-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.workspace-panel__title {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
  letter-spacing: 0.01em;
  margin: 0;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-subtle);
}

@media (max-width: 900px) {
  .workspace-layout {
    grid-template-columns: 1fr;
  }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('workspace-page-styles')) {
  const el = document.createElement('style');
  el.id = 'workspace-page-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
