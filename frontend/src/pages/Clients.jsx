import { useEffect, useState } from "react";
import apiClient from "../api/client";

export default function Clients() {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [hourlyRate, setHourlyRate] = useState("");

  async function loadClients() {
    setLoading(true);
    setError("");

    try {
      const response = await apiClient.get("/clients");
      setClients(response.data);
    } catch {
      setError("Unable to load clients. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadClients();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setFormError("");

    const cleanName = name.trim();
    const cleanEmail = email.trim();
    const rate = Number(hourlyRate);

    if (!cleanName) {
      setFormError("Client name is required.");
      return;
    }

    if (!hourlyRate || !Number.isFinite(rate) || rate < 0) {
      setFormError("Please enter a valid hourly rate.");
      return;
    }

    if (rate > 100000000) {
      setFormError("Hourly rate is too large.");
      return;
    }

    setSaving(true);

    try {
      await apiClient.post("/clients", {
        name: cleanName,
        email: cleanEmail || null,
        hourly_rate_cents: Math.round(rate * 100),
      });

      setName("");
      setEmail("");
      setHourlyRate("");
      await loadClients();
    } catch (err) {
      if (err.response?.status === 422) {
        setFormError("Please check the client details.");
      } else {
        setFormError("Unable to create client. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(client) {
    const confirmed = window.confirm(
      `Deleting "${client.name}" will permanently delete all related projects, tasks, time entries, and invoices (including paid invoices). This cannot be undone. Continue?`
    );

    if (!confirmed) return;

    setDeleteError("");

    try {
      await apiClient.delete(`/clients/${client.id}`);
      await loadClients();
    } catch (err) {
      if (err.response?.status === 404) {
        setDeleteError("Client was not found. Refresh the list.");
      } else {
        setDeleteError("Unable to delete client. Please try again.");
      }
    }
  }

  function formatCurrency(cents) {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(cents / 100);
  }

  return (
    <>
      <header className="page-heading">
        <p className="eyebrow">WORKSPACE</p>
        <h1>Clients</h1>
        <p className="muted">
          Manage your clients and their hourly billing rates.
        </p>
      </header>

      <section className="panel clients-form-panel">
        <h2>Add client</h2>

        <form className="client-form" onSubmit={handleSubmit}>
          <label className="form-field">
            Client name
            <input
              className="login-input"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Client name"
              maxLength={255}
              required
            />
          </label>

          <label className="form-field">
            Email (optional)
            <input
              className="login-input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="client@example.com"
              maxLength={255}
            />
          </label>

          <label className="form-field">
            Hourly rate (INR)
            <input
              className="login-input"
              type="number"
              min="0"
              step="0.01"
              value={hourlyRate}
              onChange={(event) => setHourlyRate(event.target.value)}
              placeholder="1000"
              required
            />
          </label>

          {formError && (
            <p className="login-error" role="alert">
              {formError}
            </p>
          )}

          <button className="login-button" type="submit" disabled={saving}>
            {saving ? "Saving client..." : "Add client"}
          </button>
        </form>
      </section>

      <section className="clients-list-section">
        <div className="clients-list-heading">
          <h2>Your clients</h2>
          <button
            className="secondary-button"
            type="button"
            onClick={loadClients}
            disabled={loading}
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>

        {deleteError && (
          <p className="login-error" role="alert">
            {deleteError}
          </p>
        )}

        {loading && (
          <p className="muted" role="status">
            Loading clients...
          </p>
        )}

        {!loading && error && (
          <div className="panel">
            <p className="login-error" role="alert">{error}</p>
            <button className="secondary-button" onClick={loadClients}>
              Try again
            </button>
          </div>
        )}

        {!loading && !error && clients.length === 0 && (
          <section className="panel empty-state">
            <h3>No clients yet</h3>
            <p className="muted">
              Add your first client using the form above.
            </p>
          </section>
        )}

        {!loading && !error && clients.length > 0 && (
          <div className="clients-list">
            {clients.map((client) => (
              <article className="panel client-card" key={client.id}>
                <div className="client-card-info">
                  <h3>{client.name}</h3>
                  <p className="muted">
                    {client.email || "No email provided"}
                  </p>
                  <p className="client-rate">
                    {formatCurrency(client.hourly_rate_cents)} / hour
                  </p>
                </div>

                <button
                  className="delete-button"
                  type="button"
                  onClick={() => handleDelete(client)}
                >
                  Delete
                </button>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
