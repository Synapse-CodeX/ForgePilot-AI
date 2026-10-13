import { useEffect, useState } from 'react';
import { AppShell } from './components/layout/AppShell';
import { HomePage } from './pages/HomePage';
import { NewRepairPage } from './pages/NewRepairPage';
import { RepairWorkspacePage } from './pages/RepairWorkspacePage';
import { HistoryPage } from './pages/HistoryPage';

type Route =
  | { id: 'home' }
  | { id: 'repair.new' }
  | { id: 'repair.workspace'; jobId: string }
  | { id: 'history' };

function parseHash(hash: string): Route {
  const h = hash.replace(/^#/, '');

  if (!h || h === '/' || h === '')            return { id: 'home' };
  if (h === '/repair/new')                     return { id: 'repair.new' };
  if (h === '/history')                        return { id: 'history' };

  // /repair/:jobId
  const workspaceMatch = h.match(/^\/repair\/([^/]+)$/);
  if (workspaceMatch) {
    return { id: 'repair.workspace', jobId: workspaceMatch[1] };
  }

  // Fallback to home
  return { id: 'home' };
}

function useRoute(): Route {
  const [route, setRoute] = useState<Route>(() =>
    parseHash(window.location.hash),
  );

  useEffect(() => {
    const onHashChange = () => setRoute(parseHash(window.location.hash));
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  return route;
}

function RouteView({ route }: { route: Route }) {
  switch (route.id) {
    case 'home':
      return <HomePage />;
    case 'repair.new':
      return <NewRepairPage />;
    case 'repair.workspace':
      return <RepairWorkspacePage jobId={route.jobId} />;
    case 'history':
      return <HistoryPage />;
  }
}

export default function App() {
  const route = useRoute();

  return (
    <AppShell>
      <RouteView route={route} />
    </AppShell>
  );
}