import { Navigate, Outlet } from "react-router-dom";

export default function GuestRoute() {
  const token = localStorage.getItem("access_token");

  return token ? <Navigate to="/" replace /> : <Outlet />;
}
