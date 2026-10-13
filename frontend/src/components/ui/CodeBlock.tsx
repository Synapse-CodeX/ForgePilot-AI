import { useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { copyToClipboard } from '../../lib/utils';

interface CodeBlockProps {
  code:            string;
  language?:       string;
  showLineNumbers?: boolean;
  maxHeight?:      string;
  className?:      string;
}

export function CodeBlock({
  code,
  language,
  showLineNumbers = false,
  maxHeight       = '400px',
  className,
}: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const lines = code.split('\n');

  const handleCopy = async () => {
    await copyToClipboard(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={['code-block', className ?? ''].filter(Boolean).join(' ')}>
      <div className="code-block__header">
        {language && (
          <span className="code-block__lang">{language}</span>
        )}
        <button
          className="code-block__copy"
          onClick={handleCopy}
          title={copied ? 'Copied!' : 'Copy to clipboard'}
          aria-label={copied ? 'Copied!' : 'Copy code to clipboard'}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      <div className="code-block__body" style={{ maxHeight, overflowY: 'auto' }}>
        <pre className="code-block__pre">
          {showLineNumbers ? (
            <table className="code-block__table" aria-label="code">
              <tbody>
                {lines.map((line, i) => (
                  <tr key={i}>
                    <td className="code-block__ln" aria-hidden="true">{i + 1}</td>
                    <td className="code-block__lc"><code>{line || '\u00a0'}</code></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <code>{code}</code>
          )}
        </pre>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.code-block {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-code-bg);
  font-family: var(--font-mono);
  font-size: 12.5px;
}

.code-block__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--color-border-subtle);
  min-height: 34px;
}

.code-block__lang {
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 500;
  font-family: var(--font-mono);
}

.code-block__copy {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-text-muted);
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  transition: background var(--transition-fast), color var(--transition-fast);
  cursor: pointer;
  border: none;
  background: none;
  font-family: var(--font-sans);
  margin-left: auto;
}

.code-block__copy:hover {
  background: var(--color-surface-raised);
  color: var(--color-text-primary);
}

.code-block__body {
  overflow-x: auto;
}

.code-block__pre {
  margin: 0;
  padding: 14px 0;
}

.code-block__pre > code {
  display: block;
  padding: 0 16px;
  white-space: pre;
  color: var(--color-text-secondary);
}

.code-block__table {
  border-collapse: collapse;
  width: 100%;
}

.code-block__ln {
  text-align: right;
  padding: 0 12px 0 16px;
  color: var(--color-text-muted);
  user-select: none;
  min-width: 40px;
  font-size: 11px;
}

.code-block__lc {
  padding: 0 16px 0 0;
  white-space: pre;
}

.code-block__lc code {
  color: var(--color-text-secondary);
  font-size: inherit;
  white-space: pre;
}
`;

if (typeof document !== 'undefined' && !document.getElementById('code-block-styles')) {
  const el = document.createElement('style');
  el.id = 'code-block-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
