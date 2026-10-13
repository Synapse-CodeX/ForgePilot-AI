import { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronRight, Clock, AlertTriangle } from 'lucide-react';
import type { ValidationReport, ValidationCommandResult } from '../../types/api';
import { EmptyState } from '../ui/EmptyState';
import { Badge } from '../ui/Badge';
import { StatusIcon } from '../ui/StatusIcon';
import { CodeBlock } from '../ui/CodeBlock';
import { formatDuration } from '../../lib/utils';

interface ValidationPanelProps {
  report?: ValidationReport;
}

function ValidationRow({ result }: { result: ValidationCommandResult }) {
  const [expanded, setExpanded] = useState(false);
  const hasOutput = result.stdout || result.stderr;

  return (
    <div className="val-row">
      {/* Summary row */}
      <button
        className="val-row__header"
        onClick={() => hasOutput && setExpanded((v) => !v)}
        aria-expanded={hasOutput ? expanded : undefined}
        aria-disabled={!hasOutput}
        disabled={!hasOutput}
      >
        <StatusIcon status={result.passed ? 'success' : 'failed'} size={14} />

        <span className="val-row__profile">{result.profile}</span>

        <code className="val-row__command">{result.command}</code>

        <div className="val-row__meta">
          {result.timed_out && (
            <Badge variant="warning" size="sm">
              <Clock size={10} aria-hidden="true" />
              Timed out
            </Badge>
          )}
          <span className="val-row__exit-code" title="Exit code">
            exit {result.exit_code}
          </span>
          <span className="val-row__duration">
            {formatDuration(result.duration_seconds)}
          </span>
        </div>

        {hasOutput && (
          <span className="val-row__chevron" aria-hidden="true">
            {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
          </span>
        )}
      </button>

      {/* Expanded detail */}
      {expanded && hasOutput && (
        <div className="val-row__detail">
          {result.stderr && (
            <div className="val-row__output-section val-row__output-section--err">
              <span className="val-output-label">
                <AlertTriangle size={10} aria-hidden="true" />
                stderr
              </span>
              <CodeBlock
                code={result.stderr}
                language="shell"
                maxHeight="220px"
              />
            </div>
          )}
          {result.stdout && (
            <div className="val-row__output-section">
              <span className="val-output-label">stdout</span>
              <CodeBlock
                code={result.stdout}
                language="shell"
                maxHeight="220px"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ValidationPanel({ report }: ValidationPanelProps) {
  if (!report) {
    return (
      <EmptyState
        icon={<ShieldCheck size={28} />}
        title="Validation pending"
        description="Test results will appear here once the validation stage completes."
      />
    );
  }

  return (
    <div className="validation-panel">
      {/* Overall result */}
      <div className="validation-panel__summary">
        <div className="validation-overall">
          <StatusIcon
            status={report.passed ? 'success' : 'failed'}
            size={18}
          />
          <span className="validation-overall__label">
            {report.passed ? 'All checks passed' : 'Some checks failed'}
          </span>
          <Badge
            variant={report.passed ? 'success' : 'danger'}
            size="md"
          >
            {report.results.filter((r) => r.passed).length} / {report.results.length} passed
          </Badge>
        </div>
        {report.summary && (
          <p className="validation-summary-text">{report.summary}</p>
        )}
      </div>

      {/* Command results */}
      <div className="validation-results" role="list" aria-label="Validation commands">
        {report.results.map((result, i) => (
          <ValidationRow key={i} result={result} />
        ))}
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.validation-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.validation-panel__summary {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border-subtle);
}

.validation-overall {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.validation-overall__label {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.validation-summary-text {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.validation-results {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* Validation row */
.val-row {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.val-row__header {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 9px 12px;
  background: var(--color-surface-raised);
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast);
  min-height: 44px;
  flex-wrap: wrap;
}

.val-row__header:not([disabled]):hover {
  background: #15191f;
}

.val-row__header[aria-disabled="true"] { cursor: default; }

.val-row__profile {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex-shrink: 0;
}

.val-row__command {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--color-text-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.val-row__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.val-row__exit-code {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.val-row__duration {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-muted);
}

.val-row__chevron {
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.val-row__detail {
  padding: 12px;
  border-top: 1px solid var(--color-border-subtle);
  background: var(--color-code-bg);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.val-row__output-section {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.val-output-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.val-row__output-section--err .val-output-label {
  color: var(--color-danger);
}
`;

if (typeof document !== 'undefined' && !document.getElementById('validation-panel-styles')) {
  const el = document.createElement('style');
  el.id = 'validation-panel-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
