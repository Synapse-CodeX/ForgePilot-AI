import { useState, useEffect } from 'react';
import {
  Wrench,
  Home,
  GitBranch,
  History,
  Menu,
  X,
  Activity,
  WifiOff,
} from 'lucide-react';
import { useHealth } from '../../hooks/useHealth';
import { Spinner } from '../ui/Spinner';

interface NavItem {
  label:  string;
  hash:   string;
  icon:   React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Home',        hash: '#/',           icon: <Home      size={15} /> },
  { label: 'New Repair',  hash: '#/repair/new', icon: <GitBranch size={15} /> },
  { label: 'History',     hash: '#/history',    icon: <History   size={15} /> },
];

function useCurrentHash(): string {
  const [hash, setHash] = useState(() => window.location.hash || '#/');

  useEffect(() => {
    const onHashChange = () => setHash(window.location.hash || '#/');
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return hash;
}

export function Sidebar() {
  const [open, setOpen]     = useState(false);
  const currentHash         = useCurrentHash();
  const { status, loading, error } = useHealth();

  const isActive = (hash: string) => {
    if (hash === '#/') return currentHash === '#/' || currentHash === '#' || currentHash === '';
    return currentHash.startsWith(hash);
  };

  const navigate = (hash: string) => {
    window.location.hash = hash;
    setOpen(false);
  };

  const sidebarContent = (
    <nav className="sidebar" aria-label="Main navigation">
      {/* Brand */}
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark" aria-hidden="true">
          <Wrench size={16} strokeWidth={1.8} />
        </div>
        <span className="sidebar__brand-name">ForgePilot</span>
      </div>

      {/* Nav items */}
      <ul className="sidebar__nav" role="list">
        {NAV_ITEMS.map((item) => (
          <li key={item.hash}>
            <button
              className={['sidebar__nav-item', isActive(item.hash) ? 'sidebar__nav-item--active' : ''].filter(Boolean).join(' ')}
              onClick={() => navigate(item.hash)}
              aria-current={isActive(item.hash) ? 'page' : undefined}
            >
              <span className="sidebar__nav-icon" aria-hidden="true">{item.icon}</span>
              {item.label}
            </button>
          </li>
        ))}
      </ul>

      {/* Health indicator */}
      <div className="sidebar__footer">
        <div className="sidebar__health">
          {loading ? (
            <>
              <Spinner size="sm" />
              <span className="sidebar__health-label">Checking…</span>
            </>
          ) : error ? (
            <>
              <WifiOff size={13} style={{ color: 'var(--color-danger)', flexShrink: 0 }} aria-hidden="true" />
              <span className="sidebar__health-label sidebar__health-label--error">Backend unreachable</span>
            </>
          ) : (
            <>
              <Activity size={13} style={{ color: 'var(--color-success)', flexShrink: 0 }} aria-hidden="true" />
              <span className="sidebar__health-label sidebar__health-label--ok">
                {status?.service ?? 'API'} operational
              </span>
            </>
          )}
        </div>
      </div>
    </nav>
  );

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="sidebar__hamburger"
        onClick={() => setOpen(true)}
        aria-label="Open navigation"
        aria-expanded={open}
      >
        <Menu size={20} />
      </button>

      {/* Desktop sidebar */}
      <div className="sidebar-desktop" aria-hidden="false">
        {sidebarContent}
      </div>

      {/* Mobile overlay + drawer */}
      {open && (
        <>
          <div
            className="sidebar-overlay"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          <div className="sidebar-drawer">
            <button
              className="sidebar-drawer__close"
              onClick={() => setOpen(false)}
              aria-label="Close navigation"
            >
              <X size={18} />
            </button>
            {sidebarContent}
          </div>
        </>
      )}
    </>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const styles = `
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 16px 10px 12px;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 6px 6px 16px;
  border-bottom: 1px solid var(--color-border-subtle);
  margin-bottom: 8px;
}

.sidebar__brand-mark {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: var(--color-surface-raised);
  border: 1px solid var(--color-border);
  color: var(--color-accent);
  flex-shrink: 0;
}

.sidebar__brand-name {
  font-size: 14px;
  font-weight: 650;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.sidebar__nav {
  list-style: none;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 7px 10px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.sidebar__nav-item:hover {
  background: var(--color-surface-raised);
  color: var(--color-text-secondary);
}

.sidebar__nav-item--active {
  background: var(--color-accent-subtle);
  color: var(--color-accent);
  font-weight: 600;
}

.sidebar__nav-item--active:hover {
  background: var(--color-accent-subtle);
  color: var(--color-accent-hover);
}

.sidebar__nav-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.sidebar__footer {
  padding-top: 12px;
  border-top: 1px solid var(--color-border-subtle);
  margin-top: auto;
}

.sidebar__health {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
}

.sidebar__health-label {
  font-size: 11.5px;
  color: var(--color-text-muted);
  truncate: true;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar__health-label--ok    { color: var(--color-success); }
.sidebar__health-label--error { color: var(--color-danger);  }

/* Desktop sidebar container */
.sidebar-desktop {
  width: var(--sidebar-width);
  height: 100vh;
  position: sticky;
  top: 0;
  flex-shrink: 0;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border-subtle);
  overflow-y: auto;
}

/* Mobile hamburger */
.sidebar__hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  background: none;
  border: none;
  cursor: pointer;
}

.sidebar__hamburger:hover {
  background: var(--color-surface-raised);
}

/* Mobile overlay */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 40;
}

/* Mobile drawer */
.sidebar-drawer {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 260px;
  background: var(--color-surface);
  border-right: 1px solid var(--color-border);
  z-index: 50;
  overflow-y: auto;
  animation: slideIn 200ms ease;
}

.sidebar-drawer__close {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 6px;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to   { transform: translateX(0); }
}

@media (max-width: 768px) {
  .sidebar-desktop { display: none; }
  .sidebar__hamburger { display: flex; }
}
`;

if (typeof document !== 'undefined' && !document.getElementById('sidebar-styles')) {
  const el = document.createElement('style');
  el.id = 'sidebar-styles';
  el.textContent = styles;
  document.head.appendChild(el);
}
