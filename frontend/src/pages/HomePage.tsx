import { GitBranch, Inspect, Search, Stethoscope, Wrench, ShieldCheck, Activity, AlertCircle } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Spinner } from '../components/ui/Spinner';
import { useHealth } from '../hooks/useHealth';

const STAGES = [
  { key: 'inspect',   label: 'Inspect',   icon: <Inspect      size={14} />, desc: 'Fetches repository and issue context from GitHub' },
  { key: 'analyze',   label: 'Analyze',   icon: <Search       size={14} />, desc: 'Scans files and scores candidates' },
  { key: 'diagnose',  label: 'Diagnose',  icon: <Stethoscope  size={14} />, desc: 'Identifies the root cause with AI analysis' },
  { key: 'patch',     label: 'Patch',     icon: <Wrench       size={14} />, desc: 'Generates and applies a targeted code patch' },
  { key: 'validate',  label: 'Validate',  icon: <ShieldCheck  size={14} />, desc: 'Runs tests in an isolated environment' },
] as const;

export function HomePage() {
  const { status, loading, error } = useHealth();

  const navigate = (hash: string) => {
    window.location.hash = hash;
  };

  return (
    <div className="home-page">
      {/* Hero */}
      <section className="home-hero">
        <div className="home-hero__eyebrow">
          <Activity size={13} aria-hidden="true" />
          AI ENGINEERING PLATFORM
        </div>
        <h1 className="home-hero__title">
          From GitHub issue to<br />
          validated patch.<br />
          <span className="home-hero__accent">Autonomously.</span>
        </h1>
        <p className="home-hero__sub">
          ForgePilot investigates repository issues, generates targeted code repairs,
          and validates them inside an isolated execution environment — with full transparency
          at every stage.
        </p>
        <div className="home-hero__actions">
          <Button
            variant="primary"
            size="lg"
            icon={<GitBranch size={16} />}
            onClick={() => navigate('#/repair/new')}
          >
            Start a repair
          </Button>
        </div>
      </section>

      {/* Workflow timeline */}
      <section className="home-pipeline" aria-label="Workflow stages">
        <p className="home-section-label">HOW IT WORKS</p>
        <div className="home-pipeline__stages">
          {STAGES.map((stage, i) => (
            <div key={stage.key} className="pipeline-stage">
              <div className="pipeline-stage__connector" aria-hidden="true">
                <div className="pipeline-stage__icon">{stage.icon}</div>
                {i < STAGES.length - 1 && (
                  <div className="pipeline-stage__line" aria-hidden="true" />
                )}
              </div>
              <div className="pipeline-stage__text">
                <span className="pipeline-stage__num">0{i + 1}</span>
                <span className="pipeline-stage__name">{stage.label}</span>
                <span className="pipeline-stage__desc">{stage.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Engine status card */}
      <section className="home-status-card" aria-label="Engine status">
        <div className="home-status-card__left">
          <span className="home-section-label">ENGINE STATUS</span>
          {loading ? (
            <div className="home-status-card__row">
              <Spinner size="sm" />
              <span className="home-status-card__title">Checking backend…</span>
            </div>
          ) : error ? (
            <div className="home-status-card__row home-status-card__row--error">
              <AlertCircle size={16} aria-hidden="true" />
              <span className="home-status-card__title">Backend unreachable</span>
            </div>
          ) : (
            <div className="home-status-card__row home-status-card__row--ok">
              <span className="status-dot-pulse" aria-hidden="true" />
              <span className="home-status-card__title">
                {status?.service ?? 'API'} — {status?.status ?? 'online'}
              </span>
            </div>
          )}

          {error && (
            <p className="home-status-card__note">
              {error} — repair functionality requires a running backend.
            </p>
          )}
        </div>

        <Button
          variant="secondary"
          size="sm"
          icon={<GitBranch size={14} />}
          onClick={() => navigate('#/repair/new')}
        >
          New repair
        </Button>
      </section>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.home-page {
  display: flex;
  flex-direction: column;
  gap: 48px;
  max-width: 820px;
  animation: fadeIn 250ms ease;
}

.home-hero__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: 20px;
}

.home-hero__title {
  font-size: clamp(32px, 5vw, 52px);
  font-weight: 650;
  line-height: 1.08;
  letter-spacing: -0.04em;
  color: var(--color-text-primary);
  margin-bottom: 18px;
}

.home-hero__accent {
  color: var(--color-accent);
}

.home-hero__sub {
  font-size: 15px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  max-width: 560px;
  margin-bottom: 28px;
}

.home-hero__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.home-section-label {
  display: block;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--color-text-muted);
  margin-bottom: 16px;
}

/* Pipeline */
.home-pipeline {
  padding: 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}

.home-pipeline__stages {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.pipeline-stage {
  display: flex;
  gap: 14px;
}

.pipeline-stage__connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.pipeline-stage__icon {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  color: var(--color-accent);
  flex-shrink: 0;
}

.pipeline-stage__line {
  width: 1px;
  flex: 1;
  min-height: 12px;
  background: var(--color-border-subtle);
  margin: 4px 0;
}

.pipeline-stage__text {
  display: flex;
  flex-direction: column;
  padding-bottom: 16px;
  padding-top: 4px;
  gap: 2px;
  min-width: 0;
}

.pipeline-stage__num {
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-muted);
  letter-spacing: 0.05em;
}

.pipeline-stage__name {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.pipeline-stage__desc {
  font-size: 12.5px;
  color: var(--color-text-muted);
  line-height: 1.4;
}

/* Status card */
.home-status-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  flex-wrap: wrap;
}

.home-status-card__left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.home-status-card__row {
  display: flex;
  align-items: center;
  gap: 9px;
}

.home-status-card__row--ok    { color: var(--color-success); }
.home-status-card__row--error { color: var(--color-danger); }

.home-status-card__title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.home-status-card__note {
  font-size: 12px;
  color: var(--color-danger);
  margin: 0;
}

/* Pulsing dot */
.status-dot-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-success);
  box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4);
  animation: statusPulse 2s ease infinite;
  flex-shrink: 0;
}

@keyframes statusPulse {
  0%   { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4); }
  70%  { box-shadow: 0 0 0 6px rgba(63, 185, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(63, 185, 80, 0); }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('home-page-styles')) {
  const el = document.createElement('style');
  el.id = 'home-page-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
