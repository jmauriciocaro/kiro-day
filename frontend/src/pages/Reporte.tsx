import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { money } from "../format";
import type { DailyReport } from "../types";

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function Reporte() {
  const { token } = useAuth();
  const [date, setDate] = useState(today());
  const [report, setReport] = useState<DailyReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load(selected: string) {
    if (!token) return;
    setError(null);
    setLoading(true);
    try {
      setReport(await api.dailyReport(token, selected));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cargar el reporte");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(date);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div>
      <section className="card" aria-label="Reporte de ventas del día">
        <h2>Reporte de ventas</h2>
        <div className="field">
          <label htmlFor="date">Fecha</label>
          <input
            id="date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <button className="btn" onClick={() => load(date)} disabled={loading}>
          {loading ? "Cargando…" : "Ver reporte"}
        </button>
      </section>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {report && (
        <section className="card" aria-live="polite">
          <p className="total">
            {report.count} venta(s) — Total del día: {money(report.total)}
          </p>
          {report.sales.length === 0 ? (
            <p>No hubo ventas en la fecha seleccionada.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Hora</th>
                  <th>Recibo</th>
                  <th>Pago</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {report.sales.map((s) => (
                  <tr key={s.sale_id}>
                    <td>{new Date(s.created_at).toLocaleTimeString("es-CO")}</td>
                    <td>{s.sale_id.slice(0, 8)}</td>
                    <td>{s.payment_method}</td>
                    <td>{money(s.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}
    </div>
  );
}
