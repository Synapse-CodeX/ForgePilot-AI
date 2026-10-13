import {
  Inspect,
  Search,
  Stethoscope,
  Wrench,
  ShieldCheck,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import type { WorkflowStageResult, StageName } from '../../types/api';
import { StatusIcon, type StatusValue } from '../ui/StatusIcon';
import { formatDuration } from '../../lib/utils';

interface StageDefinition {
  key:   StageName;
  label: string;
  Icon:  React.FC<{ size?: number }>;
}

const STAGE_DEFS: StageDefinition[] = [
  { key: 'repository_inspection',  label: 'Repository Inspection',  Icon: Inspect      },
  { key: 'repository_analysis',    label: 'Repository Analysis',    Icon: Search       },
  { key: 'root_cause_analysis',    label: 'Root Cause Analysis',    Icon: Stethoscope  },
  { key: 'patch_generation',       label: 'Patch Generation',       Icon: Wrench       },
  { key: 'patch_validation',       label: 'Patch Validation',       Icon: ShieldCheck  },
];

function toStatusValue(
  status: WorkflowStageResult['status'] | 'pending',
): StatusValue {
  if (status === 'succeeded') return 'success';
  if (status === 'failed')    return 'failed';
  if (status === 'running')   return 'running';
  return 'pending';
}

interface WorkflowTimelineProps {
  stages?: WorkflowStageResult[];
}

export function WorkflowTimeline({ stages }: WorkflowTimelineProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const toggle = (key: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const stageMap = new Map(stages?.map((s) => [s.stage, s]) ?? []);

  return (
    <div className="workflow-timeline" aria-label="Workflow stages">
      {STAGE_DEFS.map((def, i) => {
        const result  = stageMap.get(def.key);
        const status  = result ? toStatusValue(result.status) : 'pending';
        const isLast  = i === STAGE_DEFS.length - 1;
        const isFailed = result?.status === 'failed';
        const isExpanded = expanded.has(def.key);

        return (
          <div key={def.key} className="timeline-stage">
            {/* Icon + connector */}
            <div className="timeline-stage__left" aria-hidden="true">
              <div className={['timeline-stage__dot', `timeline-stage__dot--${status}`].join(' ')}>
                <def.Icon size={13} />
              </div>
              {!isLast && <div className="timeline-stage__line" />}
            </div>

            {/* Content */}
            <div className="timeline-stage__content">
              <div className="timeline-stage__row">
                <span className="timeline-stage__name">{def.label}</span>

                <div className="timeline-stage__meta">
                  {result?.duration_seconds != null && (
                    <span className="timeline-stage__duration">
                      {formatDuration(result.duration_seconds)}
                    </span>
                  )}
                  <StatusIcon status={status} size={14} />
                </div>

                {isFailed && (
                  <button
                    className="timeline-stage__expand"
                    onClick={() => toggle(def.key)}
                    aria-expanded={isExpanded}
                    aria-label={isExpanded ? 'Collapse error details' : 'Expand error details'}
                  >
                    {isExpanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  </button>
                )}
              </div>

              {result?.message && (
                <p className="timeline-stage__message">{result.message}</p>
              )}

              {isFailed && isExpanded && (
                <div className="timeline-stage__error-detail">
                  {result?.error_type && (
                    <span className="timeline-stage__error-type">{result.error_type}</span>
                  )}
                  {result?.message && (
                    <p className="timeline-stage__error-msg">{result.message}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.workflow-timeline {
  display: flex;
  flex-direction: column;
}

.timeline-stage {
  display: flex;
  gap: 12px;
}

.timeline-stage__left {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.timeline-stage__dot {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1.5px solid var(--color-border);
  background: var(--color-surface-raised);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.timeline-stage__dot--success {
  border-color: rgba(63, 185, 80, 0.4);
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.timeline-stage__dot--failed {
  border-color: rgba(248, 81, 73, 0.4);
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

.timeline-stage__dot--running {
  border-color: rgba(79, 142, 247, 0.4);
  background: var(--color-accent-subtle);
  color: var(--color-accent);
}

.timeline-stage__line {
  width: 1.5px;
  flex: 1;
  min-height: 10px;
  background: var(--color-border-subtle);
  margin: 4px 0;
}

.timeline-stage__content {
  flex: 1;
  padding-bottom: 18px;
  padding-top: 4px;
  min-width: 0;
}

.timeline-stage__row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.timeline-stage__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
}

.timeline-stage__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.timeline-stage__duration {
  font-size: 11px;
  color: var(--color-text-muted);
  font-family: var(--font-mono);
}

.timeline-stage__expand {
  padding: 2px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.timeline-stage__expand:hover { color: var(--color-text-secondary); }

.timeline-stage__message {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 4px 0 0;
  line-height: 1.4;
}

.timeline-stage__error-detail {
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  background: var(--color-danger-subtle);
  border: 1px solid rgba(248, 81, 73, 0.2);
}

.timeline-stage__error-type {
  display: inline-block;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--color-danger);
  margin-bottom: 4px;
  font-weight: 600;
}

.timeline-stage__error-msg {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('workflow-timeline-styles')) {
  const el = document.createElement('style');
  el.id = 'workflow-timeline-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
