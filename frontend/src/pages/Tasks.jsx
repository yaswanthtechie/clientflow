import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import apiClient from "../api/client";

export default function Tasks() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [updatingTaskId, setUpdatingTaskId] = useState(null);
  const [deletingTaskId, setDeletingTaskId] = useState(null);
  const [error, setError] = useState("");
  const [tasksError, setTasksError] = useState("");
  const [formError, setFormError] = useState("");
  const [actionError, setActionError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    async function fetchProjects() {
      try {
        setLoading(true);
        setError("");
        const response = await apiClient.get("/projects");
        setProjects(response.data);
      } catch {
        setError("Unable to load projects. Please try again.");
      } finally {
        setLoading(false);
      }
    }

    fetchProjects();
  }, []);

  useEffect(() => {
    let active = true;

    if (!selectedProject) {
      setTasks([]);
      setTasksError("");
      setTasksLoading(false);
      return () => {
        active = false;
      };
    }

    async function fetchTasks() {
      try {
        setTasksLoading(true);
        setTasksError("");
        setTasks([]);
        const response = await apiClient.get("/tasks", {
          params: { project_id: selectedProject },
        });

        if (active) {
          setTasks(response.data);
        }
      } catch {
        if (active) {
          setTasksError("Unable to load tasks. Please try again.");
        }
      } finally {
        if (active) {
          setTasksLoading(false);
        }
      }
    }

    fetchTasks();

    return () => {
      active = false;
    };
  }, [selectedProject]);

  async function handleCreateTask(event) {
    event.preventDefault();
    setFormError("");
    setActionError("");
    setSuccess("");

    const cleanTitle = title.trim();

    if (!selectedProject) {
      setFormError("Please select a project first.");
      return;
    }

    if (!cleanTitle) {
      setFormError("Task title is required.");
      return;
    }

    if (cleanTitle.length > 255) {
      setFormError("Task title must be 255 characters or less.");
      return;
    }

    try {
      setCreating(true);
      const response = await apiClient.post("/tasks", {
        project_id: Number(selectedProject),
        title: cleanTitle,
      });

      setTasks((currentTasks) => [...currentTasks, response.data]);
      setTitle("");
      setSuccess("Task created successfully.");
    } catch (err) {
      if (err.response?.status === 422) {
        setFormError("Invalid task details. Please check the title.");
      } else if (err.response?.status === 404) {
        setFormError("Selected project was not found.");
      } else {
        setFormError("Unable to create task. Please try again.");
      }
    } finally {
      setCreating(false);
    }
  }

  async function handleToggleStatus(task) {
    setActionError("");
    setSuccess("");

    const newStatus = task.status === "open" ? "done" : "open";

    try {
      setUpdatingTaskId(task.id);
      const response = await apiClient.patch(`/tasks/${task.id}`, {
        status: newStatus,
      });

      setTasks((currentTasks) =>
        currentTasks.map((item) =>
          item.id === task.id ? response.data : item
        )
      );

      setSuccess(
        newStatus === "done"
          ? "Task marked as done."
          : "Task reopened successfully."
      );
    } catch {
      setActionError("Unable to update task status. Please try again.");
    } finally {
      setUpdatingTaskId(null);
    }
  }

  async function handleDeleteTask(task) {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${task.title}"? All time entries associated with this task will also be permanently deleted. This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setActionError("");
    setSuccess("");

    try {
      setDeletingTaskId(task.id);
      await apiClient.delete(`/tasks/${task.id}`);

      setTasks((currentTasks) =>
        currentTasks.filter((item) => item.id !== task.id)
      );

      setSuccess("Task deleted successfully.");
    } catch {
      setActionError("Unable to delete task. Please try again.");
    } finally {
      setDeletingTaskId(null);
    }
  }

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">WORKSPACE</p>
        <h1>Tasks</h1>
        <p className="muted">
          Manage project tasks and track their completion status.
        </p>
      </header>

      <section className="panel">
        <h2>Select Project</h2>

        {loading && <p className="muted">Loading projects...</p>}

        {error && (
          <p className="login-error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && projects.length === 0 && (
          <p className="muted">
            No projects found. Please <Link to="/projects">create a project first</Link>.
          </p>
        )}

        {!loading && projects.length > 0 && (
          <div className="form-field">
            <label htmlFor="task-project-select">Project</label>
            <select
              id="task-project-select"
              className="login-input"
              value={selectedProject}
              onChange={(event) => {
                setSelectedProject(event.target.value);
                setTitle("");
                setSuccess("");
                setFormError("");
                setActionError("");
              }}
            >
              <option value="">Select a project</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name} ({project.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </section>

      {selectedProject && (
        <>
          <section className="panel" style={{ marginTop: "20px" }}>
            <h2>Create Task</h2>

            <form className="login-form" onSubmit={handleCreateTask}>
              <label className="form-field" htmlFor="task-title">
                Task title
                <input
                  id="task-title"
                  className="login-input"
                  type="text"
                  placeholder="Enter task title"
                  value={title}
                  onChange={(event) => {
                    setTitle(event.target.value);
                    setFormError("");
                    setSuccess("");
                  }}
                  maxLength={255}
                  required
                />
              </label>

              {formError && (
                <p className="login-error" role="alert">
                  {formError}
                </p>
              )}

              <button
                className="login-button"
                type="submit"
                disabled={creating}
              >
                {creating ? "Creating task..." : "Create Task"}
              </button>
            </form>
          </section>

          <section className="panel" style={{ marginTop: "20px" }}>
            <h2>Project Tasks</h2>

            {tasksLoading && <p className="muted">Loading tasks...</p>}

            {tasksError && (
              <p className="login-error" role="alert">
                {tasksError}
              </p>
            )}

            {actionError && (
              <p className="login-error" role="alert">
                {actionError}
              </p>
            )}

            {success && (
              <p role="status" style={{ color: "#27835d" }}>
                {success}
              </p>
            )}

            {!tasksLoading && !tasksError && tasks.length === 0 && (
              <div className="empty-state">
                No tasks found for this project. Create your first task above.
              </div>
            )}

            {!tasksLoading && !tasksError && tasks.length > 0 && (
              <div>
                {tasks.map((task) => {
                  const busy =
                    updatingTaskId === task.id ||
                    deletingTaskId === task.id;

                  return (
                    <article
                      key={task.id}
                      style={{
                        padding: "15px 0",
                        borderBottom: "1px solid #e4eaf0",
                      }}
                    >
                      <h3 style={{ margin: "0 0 8px", overflowWrap: "anywhere" }}>
                        {task.title}
                      </h3>

                      <p className="muted">
                        Project:{" "}
                        {projects.find(
                          (project) => project.id === task.project_id
                        )?.name || "Unknown project"}
                      </p>

                      <p className="muted">Status: {task.status}</p>

                      <div
                        style={{
                          display: "flex",
                          gap: "10px",
                          flexWrap: "wrap",
                        }}
                      >
                        <button
                          className="login-button"
                          type="button"
                          style={{ maxWidth: "180px" }}
                          disabled={busy}
                          onClick={() => handleToggleStatus(task)}
                        >
                          {updatingTaskId === task.id
                            ? "Updating..."
                            : task.status === "open"
                              ? "Mark as Done"
                              : "Reopen Task"}
                        </button>

                        <button
                          className="delete-button"
                          type="button"
                          disabled={busy}
                          onClick={() => handleDeleteTask(task)}
                        >
                          {deletingTaskId === task.id
                            ? "Deleting..."
                            : "Delete Task"}
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
