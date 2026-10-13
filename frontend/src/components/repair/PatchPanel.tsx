import { useState } from 'react';
import { Wrench, Copy, Check, FileCode } from 'lucide-react';
import type { PatchProposal, PatchApplicationResult } from '../../types/api';
import { EmptyState } from '../ui/EmptyState';
import { Badge } from '../ui/Badge';
import { copyToClipboard } from '../../lib/utils';

interface PatchPanelProps {
  proposal?:    PatchProposal;
  application?: PatchApplicationResult;
}

interface DiffLine {
  type:    'add' | 'remove' | 'context' | 'hunk' | 'meta';
  content: string;
  lineNo?: number;
}

function parseDiff(unified: string): DiffLine[] {
  return unified.split('\n').map((line): DiffLine => {
    if (line.startsWith('@@'))   return { type: 'hunk',    content: line };
    if (line.startsWith('---') || line.startsWith('+++')) return { type: 'meta', content: line };
    if (line.startsWith('+'))   return { type: 'add',     content: line.slice(1) };
    if (line.startsWith('-'))   return { type: 'remove',  content: line.slice(1) };
    if (line.startsWith(' '))   return { type: 'context', content: line.slice(1) };
    return { type: 'context', content: line };
  });
}

export function PatchPanel({ proposal, application }: PatchPanelProps) {
  const [copied, setCopied] = useState(false);
  const [activeFile, setActiveFile] = useState<number>(0);

  if (!proposal) {
    return (
      <EmptyState
        icon={<Wrench size={28} />}
        title="Patch generation pending"
        description="The patch proposal will appear here once the patch generation stage completes."
      />
    );
  }

  const diffLines = parseDiff(proposal.unified_diff);

  const handleCopy = async () => {
    await copyToClipboard(proposal.unified_diff);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="patch-panel">
      {/* Header meta */}
      <div className="patch-panel__header">
        <div className="patch-panel__meta">
          <p className="patch-summary">{proposal.summary}</p>
          {proposal.rationale && (
            <p className="patch-rationale">{proposal.rationale}</p>
          )}
        </div>

        <div className="patch-panel__actions">
          {/* Only show applied badge if explicitly confirmed */}
          {application?.applied === true && (
            <Badge variant="success" size="md">Applied</Badge>
          )}

          <button
            className="patch-copy-btn"
            onClick={handleCopy}
            title={copied ? 'Copied!' : 'Copy unified diff'}
            aria-label={copied ? 'Copied!' : 'Copy unified diff to clipboard'}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy diff'}</span>
          </button>
        </div>
      </div>

      {/* File tabs (when multiple files) */}
      {proposal.files_changed.length > 1 && (
        <div className="patch-file-tabs" role="tablist" aria-label="Changed files">
          {proposal.files_changed.map((file, i) => (
            <button
              key={file}
              role="tab"
              aria-selected={activeFile === i}
              className={['patch-file-tab', activeFile === i ? 'patch-file-tab--active' : ''].filter(Boolean).join(' ')}
              onClick={() => setActiveFile(i)}
            >
              <FileCode size={12} aria-hidden="true" />
              <span className="truncate">{file.split('/').pop()}</span>
            </button>
          ))}
        </div>
      )}

      {/* Single file label */}
      {proposal.files_changed.length === 1 && (
        <div className="patch-file-single">
          <FileCode size={12} aria-hidden="true" />
          <code>{proposal.files_changed[0]}</code>
        </div>
      )}

      {/* Diff viewer */}
      <div className="diff-viewer" aria-label="Unified diff">
        <div className="diff-viewer__scroll">
          <table className="diff-table" aria-label="Patch diff">
            <tbody>
              {diffLines.map((line, i) => (
                <tr
                  key={i}
                  className={[
                    'diff-row',
                    `diff-row--${line.type}`,
                  ].join(' ')}
                >
                  <td className="diff-sign" aria-hidden="true">
                    {line.type === 'add'    && '+'}
                    {line.type === 'remove' && '-'}
                    {line.type === 'context' && ' '}
                  </td>
                  <td className="diff-code">
                    <code>{line.content || '\u00a0'}</code>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.patch-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.patch-panel__header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex-wrap: wrap;
}

.patch-panel__meta {
  flex: 1;
  min-width: 0;
}

.patch-summary {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 4px;
}

.patch-rationale {
  font-size: 12.5px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

.patch-panel__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.patch-copy-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface-raised);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
  font-family: var(--font-sans);
}

.patch-copy-btn:hover {
  color: var(--color-text-primary);
  background: #191f27;
}

.patch-file-tabs {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--color-border);
  overflow-x: auto;
}

.patch-file-tab {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 12px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.patch-file-tab--active {
  color: var(--color-accent);
  border-bottom-color: var(--color-accent);
  font-weight: 600;
}

.patch-file-tab:hover { color: var(--color-text-secondary); }

.patch-file-single {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-muted);
  padding: 4px 0;
}

.patch-file-single code {
  font-size: 11.5px;
  font-family: var(--font-mono);
  color: var(--color-text-secondary);
  word-break: break-all;
}

/* Diff viewer */
.diff-viewer {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-code-bg);
}

.diff-viewer__scroll {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.diff-table {
  border-collapse: collapse;
  width: 100%;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.5;
}

.diff-row { width: 100%; }

.diff-row--add    { background: var(--color-diff-add);  }
.diff-row--remove { background: var(--color-diff-del);  }
.diff-row--hunk   { background: var(--color-diff-hunk); }
.diff-row--meta   { background: var(--color-surface);   }

.diff-sign {
  width: 24px;
  min-width: 24px;
  text-align: center;
  padding: 0 4px;
  user-select: none;
  font-weight: 700;
  vertical-align: top;
  line-height: 1.8;
}

.diff-row--add    .diff-sign { color: var(--color-success); }
.diff-row--remove .diff-sign { color: var(--color-danger);  }
.diff-row--hunk   .diff-sign { color: var(--color-info);    }

.diff-code {
  padding: 1px 12px 1px 4px;
  white-space: pre;
  overflow: visible;
  vertical-align: top;
}

.diff-code code {
  color: var(--color-text-secondary);
  font-size: inherit;
  white-space: pre;
}

.diff-row--hunk .diff-code code   { color: var(--color-info); font-style: italic; }
.diff-row--meta .diff-code code   { color: var(--color-text-muted); }
.diff-row--add  .diff-code code   { color: var(--color-text-primary); }
.diff-row--remove .diff-code code { color: var(--color-text-primary); }
`;

if (typeof document !== 'undefined' && !document.getElementById('patch-panel-styles')) {
  const el = document.createElement('style');
  el.id = 'patch-panel-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
