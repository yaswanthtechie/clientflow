
import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import apiClient from "./api/client";

const pages = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/clients", label: "Clients" },
  { to: "/projects", label: "Projects" },
  { to: "/invoices", label: "Invoices" },
];

function Dashboard() {
  const [health, setHealth] = useState({
    state: "checking",
    message: "Checking API connection...",
  });

  useEffect(() => {
    let active = true;

    apiClient
      .get("/health")
      .then(({ data }) => {
        if (!active) return;

        if (data?.status === "ok") {
          setHealth({ state: "online", message: "API is online" });
        } else {
          setHealth({
            state: "offline",
            message: "API returned an unexpected health status.",
          });
        }
      })
      .catch(() => {
        if (active) {
          setHealth({
            state: "offline",
            message: "API is unavailable. Start the backend and try again.",
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">OVERVIEW</p>
        <h1>Welcome to ClientFlow</h1>
        <p className="muted">
          Manage your freelance work, projects, and invoices in one place.
        </p>
      </header>

      <section className="dashboard-grid">
        <article className="panel">
          <p className="eyebrow">YOUR WORKSPACE</p>
          <h2>Everything, in one place.</h2>
          <p className="muted">
            Explore clients, projects, and invoices from your workspace.
          </p>
        </article>

        <article className="panel">
          <p className="eyebrow">SYSTEM STATUS</p>
          <h2>Backend connection</h2>
          <p className="health-status" role="status" aria-live="polite">
            <span className={`status-dot ${health.state}`} aria-hidden="true" />
            {health.message}
          </p>
          <code className="endpoint-label">GET /health</code>
        </article>
      </section>
    </>
  );
}

function Placeholder({ title }) {
  return (
    <>
      <h1>{title}</h1>
      <section className="panel">
        <h2>Coming soon</h2>
        <p className="muted">
          {title} functionality will be added in a future update.
        </p>
      </section>
    </>
  );
}

function Login() {
  return (
    <section className="panel">
      <h1>Welcome back</h1>
      <p className="muted">
        Login is a placeholder. Authentication is not enabled.
      </p>
      <NavLink to="/">Back to dashboard</NavLink>
    </section>
  );
}

function NotFound() {
  return (
    <section className="panel">
      <h1>404 — Page not found</h1>
      <NavLink to="/">Return to dashboard</NavLink>
    </section>
  );
}

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/" className="brand">
          <strong>ClientFlow</strong>
        </NavLink>

        <p className="nav-caption">WORKSPACE</p>

        <nav className="main-navigation" aria-label="Main navigation">
          {pages.map((page) => (
            <NavLink
              key={page.to}
              to={page.to}
              end={page.end}
              className={({ isActive }) =>
                `nav-link${isActive ? " active" : ""}`
              }
            >
              {page.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <NavLink to="/login">Login ↗</NavLink>
        </div>
      </aside>

      <main className="main-content">
        {/* TODO: Replace hardcoded workspace text with dynamic workspace data. */}
        <header className="topbar">ClientFlow / Workspace</header>

        <div className="content-container">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/login" element={<Login />} />
            <Route path="/clients" element={<Placeholder title="Clients" />} />
            <Route path="/projects" element={<Placeholder title="Projects" />} />
            <Route path="/invoices" element={<Placeholder title="Invoices" />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
