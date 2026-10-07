import {
  Activity,
  GitBranch,
  ShieldCheck,
  Wrench,
} from "lucide-react";

function App() {
  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <div className="brand-mark">
            <Wrench size={18} strokeWidth={1.8} />
          </div>

          <div>
            <h1>ForgePilot</h1>
            <span>Autonomous Repository Repair</span>
          </div>
        </div>

        <div className="system-status">
          <span className="status-dot" />
          System operational
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <span className="eyebrow">
            <Activity size={14} />
            AI ENGINEERING PLATFORM
          </span>

          <h2>
            From GitHub issue
            <br />
            to validated patch.
          </h2>

          <p>
            ForgePilot autonomously investigates repository issues,
            generates repairs, and validates them inside an isolated
            execution environment.
          </p>

          <div className="hero-actions">
            <button className="primary-button">
              <GitBranch size={16} />
              Start a repair
            </button>

            <button className="secondary-button">
              <ShieldCheck size={16} />
              View evaluations
            </button>
          </div>
        </section>

        <section className="status-card">
          <div>
            <span className="card-label">ENGINE STATUS</span>

            <h3>Ready for a repair job</h3>
          </div>

          <div className="status-check">
            <ShieldCheck size={18} />
            All systems operational
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;