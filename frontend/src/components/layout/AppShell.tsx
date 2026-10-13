import type { ReactNode } from 'react';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-bg app-shell">
      <Sidebar />
      <div className="app-shell__main">
        <main className="app-shell__content" id="main-content">
          {children}
        </main>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.app-shell {
  display: flex;
  min-height: 100vh;
}

.app-shell__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.app-shell__content {
  flex: 1;
  padding: 32px 40px;
  max-width: 1200px;
  width: 100%;
}

@media (max-width: 768px) {
  .app-shell {
    flex-direction: column;
  }

  .app-shell__content {
    padding: 20px 16px 40px;
  }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('app-shell-styles')) {
  const el = document.createElement('style');
  el.id = 'app-shell-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
