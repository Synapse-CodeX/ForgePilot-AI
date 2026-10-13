import { Stethoscope, FileCode, Lightbulb, AlertTriangle } from 'lucide-react';
import type { RootCauseAnalysis } from '../../types/api';
import { EmptyState } from '../ui/EmptyState';

interface DiagnosisPanelProps {
  analysis?: RootCauseAnalysis;
}

export function DiagnosisPanel({ analysis }: DiagnosisPanelProps) {
  if (!analysis) {
    return (
      <EmptyState
        icon={<Stethoscope size={28} />}
        title="Root cause analysis pending"
        description="Diagnosis results will appear here once the analysis stage completes."
      />
    );
  }

  const confidencePct = Math.round(analysis.confidence * 100);

  return (
    <div className="diagnosis-panel">
      {/* Summary */}
      <div className="diagnosis-section">
        <p className="panel-section-label">DIAGNOSIS SUMMARY</p>
        <p className="diagnosis-summary">{analysis.summary}</p>
      </div>

      {/* Root cause */}
      <div className="diagnosis-section">
        <p className="panel-section-label">ROOT CAUSE</p>
        <p className="diagnosis-root-cause">{analysis.root_cause}</p>
      </div>

      {/* Confidence */}
      {analysis.confidence > 0 && (
        <div className="diagnosis-section">
          <p className="panel-section-label">
            MODEL CONFIDENCE
            <span className="confidence-pct">{confidencePct}%</span>
          </p>
          <div className="confidence-bar" aria-label={`Model confidence: ${confidencePct}%`}>
            <div
              className="confidence-bar__fill"
              style={{
                width: `${confidencePct}%`,
                background:
                  confidencePct >= 70 ? 'var(--color-success)' :
                  confidencePct >= 40 ? 'var(--color-warning)' :
                  'var(--color-danger)',
              }}
            />
          </div>
          <p className="confidence-note">
            <AlertTriangle size={10} aria-hidden="true" />
            This is a model-generated hypothesis, not a verified finding.
          </p>
        </div>
      )}

      {/* Evidence */}
      {analysis.evidence.length > 0 && (
        <div className="diagnosis-section">
          <p className="panel-section-label">
            <Lightbulb size={11} aria-hidden="true" />
            EVIDENCE (HYPOTHESES)
          </p>
          <ul className="evidence-list" role="list">
            {analysis.evidence.map((ev, i) => (
              <li key={i} className="evidence-item">
                <code className="evidence-file">{ev.file_path}</code>
                <p className="evidence-observation">{ev.observation}</p>
                {ev.code_reference && (
                  <pre className="evidence-code-ref"><code>{ev.code_reference}</code></pre>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommended files */}
      {analysis.recommended_files.length > 0 && (
        <div className="diagnosis-section">
          <p className="panel-section-label">
            <FileCode size={11} aria-hidden="true" />
            RECOMMENDED FILES
          </p>
          <ul className="recommended-files" role="list">
            {analysis.recommended_files.map((file) => (
              <li key={file} className="recommended-file">
                <FileCode size={12} aria-hidden="true" />
                <code>{file}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.diagnosis-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.diagnosis-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel-section-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin: 0;
}

.confidence-pct {
  margin-left: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.diagnosis-summary {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.65;
  margin: 0;
}

.diagnosis-root-cause {
  font-size: 13px;
  color: var(--color-text-primary);
  font-weight: 500;
  line-height: 1.6;
  margin: 0;
  padding: 10px 12px;
  background: var(--color-surface-raised);
  border-radius: var(--radius-md);
  border-left: 2px solid var(--color-accent);
}

.confidence-bar {
  height: 5px;
  background: var(--color-border);
  border-radius: 99px;
  overflow: hidden;
}

.confidence-bar__fill {
  height: 100%;
  border-radius: 99px;
  transition: width 400ms ease;
}

.confidence-note {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-text-muted);
  margin: 0;
}

.evidence-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.evidence-item {
  padding: 10px 12px;
  background: var(--color-surface-raised);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-subtle);
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.evidence-file {
  font-size: 11px;
  color: var(--color-accent);
  font-family: var(--font-mono);
  word-break: break-all;
}

.evidence-observation {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.evidence-code-ref {
  margin: 4px 0 0;
  padding: 6px 10px;
  background: var(--color-code-bg);
  border-radius: var(--radius-sm);
  font-size: 11.5px;
  color: var(--color-text-secondary);
  overflow-x: auto;
  white-space: pre;
}

.recommended-files {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.recommended-file {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 4px 0;
}

.recommended-file code {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--color-text-secondary);
  word-break: break-all;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('diagnosis-panel-styles')) {
  const el = document.createElement('style');
  el.id = 'diagnosis-panel-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
