import { useState } from 'react';
import { GitBranch, Hash, ExternalLink, Clock, Inbox } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { ErrorBanner } from '../components/ui/ErrorBanner';
import { EmptyState } from '../components/ui/EmptyState';
import { parseGitHubUrl } from '../lib/utils';
import { startRepair, ApiError } from '../api/client';

interface FormState {
  repositoryUrl: string;
  issueNumber:   string;
}

interface FormErrors {
  repositoryUrl?: string;
  issueNumber?:   string;
}

export function NewRepairPage() {
  const [form, setForm]       = useState<FormState>({ repositoryUrl: '', issueNumber: '' });
  const [errors, setErrors]   = useState<FormErrors>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const parsed = parseGitHubUrl(form.repositoryUrl);

  const validate = (): boolean => {
    const next: FormErrors = {};

    if (!form.repositoryUrl.trim()) {
      next.repositoryUrl = 'Repository URL is required.';
    } else if (!parsed) {
      next.repositoryUrl = 'Must be a valid GitHub repository URL (e.g. https://github.com/owner/repo).';
    }

    const num = parseInt(form.issueNumber, 10);
    if (!form.issueNumber.trim()) {
      next.issueNumber = 'Issue number is required.';
    } else if (isNaN(num) || num < 1) {
      next.issueNumber = 'Must be a positive integer.';
    }

    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      await startRepair({
        repository_url: form.repositoryUrl.trim(),
        issue_number:   parseInt(form.issueNumber, 10),
      });
    } catch (err) {
      setApiError(
        err instanceof ApiError
          ? err.message
          : 'An unexpected error occurred.',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: undefined }));
    }
    if (apiError) setApiError(null);
  };

  return (
    <div className="new-repair-page">
      <header className="page-header">
        <h1 className="page-title">New Repair</h1>
        <p className="page-subtitle">
          Point ForgePilot at a GitHub repository and issue number to start an autonomous repair.
        </p>
      </header>

      <div className="new-repair-layout">
        {/* Form card */}
        <section className="panel" aria-label="Repair form">
          <form onSubmit={handleSubmit} noValidate className="repair-form">
            {/* Repository URL */}
            <div className="form-field">
              <label htmlFor="repo-url" className="form-label">
                Repository URL
              </label>
              <div className={['form-input-wrap', errors.repositoryUrl ? 'form-input-wrap--error' : ''].filter(Boolean).join(' ')}>
                <GitBranch size={14} className="form-input-icon" aria-hidden="true" />
                <input
                  id="repo-url"
                  type="url"
                  className="form-input"
                  placeholder="https://github.com/owner/repo"
                  value={form.repositoryUrl}
                  onChange={handleChange('repositoryUrl')}
                  autoComplete="url"
                  aria-invalid={!!errors.repositoryUrl}
                  aria-describedby={errors.repositoryUrl ? 'repo-url-error' : undefined}
                  spellCheck={false}
                />
              </div>
              {errors.repositoryUrl && (
                <p id="repo-url-error" className="form-error" role="alert">{errors.repositoryUrl}</p>
              )}
              {/* Preview */}
              {parsed && !errors.repositoryUrl && (
                <div className="form-preview">
                  <ExternalLink size={11} aria-hidden="true" />
                  <span>{parsed.owner} / {parsed.repo}</span>
                </div>
              )}
            </div>

            {/* Issue number */}
            <div className="form-field">
              <label htmlFor="issue-num" className="form-label">
                Issue Number
              </label>
              <div className={['form-input-wrap', errors.issueNumber ? 'form-input-wrap--error' : ''].filter(Boolean).join(' ')}>
                <Hash size={14} className="form-input-icon" aria-hidden="true" />
                <input
                  id="issue-num"
                  type="number"
                  className="form-input"
                  placeholder="42"
                  min={1}
                  step={1}
                  value={form.issueNumber}
                  onChange={handleChange('issueNumber')}
                  aria-invalid={!!errors.issueNumber}
                  aria-describedby={errors.issueNumber ? 'issue-num-error' : undefined}
                />
              </div>
              {errors.issueNumber && (
                <p id="issue-num-error" className="form-error" role="alert">{errors.issueNumber}</p>
              )}
            </div>

            {/* API error */}
            {apiError && (
              <ErrorBanner
                error={apiError}
                onRetry={() => setApiError(null)}
              />
            )}

            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={loading}
              icon={<GitBranch size={15} />}
              className="repair-form__submit"
            >
              Start Repair
            </Button>
          </form>
        </section>

        {/* Recent repairs */}
        <section className="panel" aria-label="Recent repairs">
          <h2 className="panel__title">Recent Repairs</h2>
          <EmptyState
            icon={<Inbox size={32} />}
            title="No repair history yet"
            description="Repair history will appear here once the backend supports job persistence."
            action={{ label: 'Start your first repair', onClick: () => document.getElementById('repo-url')?.focus() }}
          />
          <div className="panel__note">
            <Clock size={11} aria-hidden="true" />
            History requires persistent storage — backend integration pending.
          </div>
        </section>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.new-repair-page {
  display: flex;
  flex-direction: column;
  gap: 28px;
  max-width: 820px;
  animation: fadeIn 250ms ease;
}

.page-header { display: flex; flex-direction: column; gap: 8px; }

.page-title {
  font-size: 22px;
  font-weight: 650;
  letter-spacing: -0.03em;
  color: var(--color-text-primary);
  margin: 0;
}

.page-subtitle {
  font-size: 13.5px;
  color: var(--color-text-muted);
  margin: 0;
  line-height: 1.5;
}

.new-repair-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.panel__title {
  font-size: 13.5px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 16px;
}

.panel__note {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--color-text-muted);
  padding: 12px 4px 0;
  border-top: 1px solid var(--color-border-subtle);
  margin-top: 12px;
}

/* Form */
.repair-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  letter-spacing: 0.01em;
}

.form-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.form-input-icon {
  position: absolute;
  left: 10px;
  color: var(--color-text-muted);
  pointer-events: none;
  flex-shrink: 0;
}

.form-input {
  width: 100%;
  height: 38px;
  padding: 0 12px 0 32px;
  font-size: 13px;
  border-radius: var(--radius-md);
}

.form-input-wrap--error .form-input {
  border-color: var(--color-danger);
}

.form-input-wrap--error .form-input:focus {
  box-shadow: 0 0 0 3px var(--color-danger-subtle);
  border-color: var(--color-danger);
}

.form-error {
  font-size: 12px;
  color: var(--color-danger);
  margin: 0;
}

.form-preview {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  color: var(--color-accent);
  font-family: var(--font-mono);
}

.repair-form__submit { align-self: flex-start; }

@media (max-width: 700px) {
  .new-repair-layout { grid-template-columns: 1fr; }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('new-repair-page-styles')) {
  const el = document.createElement('style');
  el.id = 'new-repair-page-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
