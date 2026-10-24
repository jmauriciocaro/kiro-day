import { useState } from "react";
import { useAuth } from "./auth/AuthContext";
import { Caja } from "./pages/Caja";
import { Login } from "./pages/Login";
import { Reporte } from "./pages/Reporte";

type View = "caja" | "reporte";

export function App() {
  const { token, role, username, logout } = useAuth();
  const [view, setView] = useState<View>("caja");

  if (!token) {
    return <Login />;
  }

  const isOwner = role === "dueno";

  return (
    <div className="app">
      <header className="topbar">
        <nav aria-label="Secciones">
          <button
            className={`btn ${view === "caja" ? "" : "secondary"}`}
            onClick={() => setView("caja")}
            aria-current={view === "caja"}
          >
            Caja
          </button>{" "}
          {isOwner && (
            <button
              className={`btn ${view === "reporte" ? "" : "secondary"}`}
              onClick={() => setView("reporte")}
              aria-current={view === "reporte"}
            >
              Reporte
            </button>
          )}
        </nav>
        <div>
          <span>
            {username} ({role})
          </span>{" "}
          <button className="btn secondary" onClick={logout}>
            Salir
          </button>
        </div>
      </header>

      <main>{view === "reporte" && isOwner ? <Reporte /> : <Caja />}</main>
    </div>
  );
}
