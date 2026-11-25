import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import apiClient from "../api/client";

export default function Projects() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState("");
  const [projects, setProjects] = useState([]);
  const [projectName, setProjectName] = useState("");
  const [loading, setLoading] = useState(true);
  const [projectsLoading, setProjectsLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updatingProjectId, setUpdatingProjectId] = useState(null);
  const [deletingProjectId, setDeletingProjectId] = useState(null);
  const [error, setError] = useState("");
  const [projectsError, setProjectsError] = useState("");
  const [formError, setFormError] = useState("");
  const [success, setSuccess] = useState("");
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    async function fetchClients() {
      try {
        setLoading(true);
        setError("");
        const response = await apiClient.get("/clients");
        setClients(response.data);
      } catch (err) {
        setError("Unable to load clients. Please try again.");
      } finally {
        setLoading(false);
      }
    }
    fetchClients();
  }, []);

  useEffect(() => {
    let active = true;

    if (!selectedClient) {
      setProjects([]);
      setProjectsError("");
      setProjectsLoading(false);
      return () => {
        active = false;
      };
    }

    async function fetchProjects() {
      try {
        setProjectsLoading(true);
        setProjectsError("");
        setProjects([]);
        const response = await apiClient.get("/projects", {
          params: { client_id: selectedClient },
        });

        if (active) {
          setProjects(response.data);
        }
      } catch (err) {
        if (active) {
          setProjectsError("Unable to load projects. Please try again.");
        }
      } finally {
        if (active) {
          setProjectsLoading(false);
        }
      }
    }

    fetchProjects();

    return () => {
      active = false;
    };
  }, [selectedClient]);

  async function handleCreateProject(event) {
    event.preventDefault();
    setFormError("");
    setSuccess("");

    const cleanName = projectName.trim();

    if (!selectedClient) {
      setFormError("Please select a client first.");
      return;
    }
    if (!cleanName) {
      setFormError("Project name is required.");
      return;
    }
    if (cleanName.length > 255) {
      setFormError("Project name must be 255 characters or less.");
      return;
    }

    try {
      setCreating(true);
      await apiClient.post("/projects", {
        client_id: Number(selectedClient),
        name: cleanName,
      });
      const response = await apiClient.get("/projects", {
        params: { client_id: selectedClient },
      });
      setProjects(response.data);
      setProjectName("");
      setSuccess("Project created successfully.");
    } catch (err) {
      if (err.response?.status === 422) {
        setFormError("Invalid project details. Please check your input.");
      } else if (err.response?.status === 404) {
        setFormError("Selected client was not found.");
      } else {
        setFormError("Unable to create project. Please try again.");
      }
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleStatus(project) {
    setActionError("");
    setSuccess("");

    const newStatus = project.status === "active" ? "archived" : "active";

    try {
      setUpdatingProjectId(project.id);
      const response = await apiClient.patch(`/projects/${project.id}`, {
        status: newStatus,
      });
      setProjects((currentProjects) =>
        currentProjects.map((item) =>
          item.id === project.id ? response.data : item
        )
      );
      setSuccess(
        newStatus === "archived"
          ? "Project archived successfully."
          : "Project reactivated successfully."
      );
    } catch (err) {
      setActionError("Unable to update project status. Please try again.");
    } finally {
      setUpdatingProjectId(null);
    }
  }

  async function handleDeleteProject(project) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${project.name}"? This will permanently delete the project, all its tasks, and all associated time entries, including time entries already included in invoices. Existing invoice records and their totals will remain, but the deleted time-entry details will no longer be available. This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setSuccess("");

    try {
      setDeletingProjectId(project.id);
      await apiClient.delete(`/projects/${project.id}`);
      setProjects((currentProjects) =>
        currentProjects.filter((item) => item.id !== project.id)
      );
      setSuccess("Project deleted successfully.");
    } catch (err) {
      setActionError("Unable to delete project. Please try again.");
    } finally {
      setDeletingProjectId(null);
    }
  }

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">WORKSPACE</p>
        <h1>Projects</h1>
        <p className="muted">Manage your client projects and track their status.</p>
      </header>

      <section className="panel">
        <h2>Select Client</h2>
        {loading && <p className="muted">Loading clients...</p>}
        {error && <p className="login-error" role="alert">{error}</p>}
        {!loading && !error && clients.length === 0 && (
          <p className="muted">No clients found. Please <Link to="/clients">create a client first</Link>.</p>
        )}
        {!loading && clients.length > 0 && (
          <div className="form-field">
            <label htmlFor="client-select">Client</label>
            <select
              id="client-select"
              className="login-input"
              value={selectedClient}
              onChange={(event) => {
                setSelectedClient(event.target.value);
                setProjectName("");
                setSuccess("");
                setFormError("");
                setActionError("");
              }}
            >
              <option value="">Select a client</option>
              {clients.map((client) => (
                <option key={client.id} value={client.id}>{client.name}</option>
              ))}
            </select>
          </div>
        )}
      </section>

      {selectedClient && (
        <>
          <section className="panel" style={{ marginTop: "20px" }}>
            <h2>Create Project</h2>
            <form className="login-form" onSubmit={handleCreateProject}>
              <label className="form-field" htmlFor="project-name">
                Project name
                <input
                  id="project-name"
                  className="login-input"
                  type="text"
                  placeholder="Enter project name"
                  value={projectName}
                  onChange={(event) => {
                    setProjectName(event.target.value);
                    setFormError("");
                    setSuccess("");
                  }}
                  maxLength={255}
                  required
                />
              </label>
              {formError && <p className="login-error" role="alert">{formError}</p>}
              <button className="login-button" type="submit" disabled={creating}>
                {creating ? "Creating project..." : "Create Project"}
              </button>
            </form>
          </section>

          <section className="panel" style={{ marginTop: "20px" }}>
            <h2>Client Projects</h2>
            {projectsLoading && <p className="muted">Loading projects...</p>}
            {projectsError && <p className="login-error" role="alert">{projectsError}</p>}
            {actionError && <p className="login-error" role="alert">{actionError}</p>}
            {success && <p role="status" style={{ color: "#27835d" }}>{success}</p>}
            {!projectsLoading && !projectsError && projects.length === 0 && (
              <p className="muted">No projects found for this client.</p>
            )}
            {!projectsLoading && !projectsError && projects.length > 0 && (
              <div>
                {projects.map((project) => {
                  const busy =
                    updatingProjectId === project.id ||
                    deletingProjectId === project.id;

                  return (
                    <article
                      key={project.id}
                      style={{
                        padding: "15px 0",
                        borderBottom: "1px solid #e4eaf0",
                      }}
                    >
                      <h3 style={{ margin: "0 0 8px" }}>{project.name}</h3>
<p className="muted">
  Client: {clients.find((client) => client.id === project.client_id)?.name || "Unknown client"}
</p>
                      <p className="muted">Status: {project.status}</p>
                      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                        <button
                          className="login-button"
                          type="button"
                          style={{ maxWidth: "180px" }}
                          disabled={busy}
                          onClick={() => handleToggleStatus(project)}
                        >
                          {updatingProjectId === project.id
                            ? "Updating..."
                            : project.status === "active"
                              ? "Archive Project"
                              : "Reactivate Project"}
                        </button>
                        <button
                          className="delete-button"
                          type="button"
                          style={{ maxWidth: "180px" }}
                          disabled={busy}
                          onClick={() => handleDeleteProject(project)}
                        >
                          {deletingProjectId === project.id
                            ? "Deleting..."
                            : "Delete Project"}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </>
  );
}
