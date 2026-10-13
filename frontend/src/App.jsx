import { useEffect, useState } from "react";

import apiClient from "./api/client";

function App() {
  const [serviceState, setServiceState] = useState("Checking API connection...");

  useEffect(() => {
    apiClient
      .get("/health")
      .then(({ data }) => setServiceState(`API is ${data.status}`))
      .catch(() => setServiceState("API is unavailable. Start the backend and try again."));
  }, []);

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">ClientFlow</p>
        <h1>Freelance work, time, and invoices in one place.</h1>
        <p>{serviceState}</p>
      </section>
    </main>
  );
}

export default App;
