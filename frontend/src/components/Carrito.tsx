import { money } from "../format";
import type { CartLine, PaymentMethod } from "../types";

interface Props {
  lines: CartLine[];
  total: number;
  paymentMethod: PaymentMethod;
  onPaymentMethodChange: (m: PaymentMethod) => void;
  onSetQty: (sku: string, qty: number) => void;
  onRemove: (sku: string) => void;
  onConfirm: () => void;
  confirming: boolean;
}

export function Carrito({
  lines,
  total,
  paymentMethod,
  onPaymentMethodChange,
  onSetQty,
  onRemove,
  onConfirm,
  confirming,
}: Props) {
  const empty = lines.length === 0;
  return (
    <section className="card" aria-label="Carrito de venta">
      <h2>Carrito</h2>
      {empty ? (
        <p>Agrega productos del catálogo para iniciar una venta.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Producto</th>
              <th>Cantidad</th>
              <th>Subtotal</th>
              <th>
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l) => (
              <tr key={l.sku}>
                <td>{l.name}</td>
                <td>
                  <input
                    type="number"
                    min={1}
                    max={l.stock}
                    value={l.qty}
                    aria-label={`Cantidad de ${l.name} (máximo ${l.stock})`}
                    style={{ width: "4.5rem" }}
                    onChange={(e) =>
                      onSetQty(l.sku, Math.max(1, Number(e.target.value)))
                    }
                  />
                </td>
                <td>{money(Number(l.price) * l.qty)}</td>
                <td>
                  <button
                    className="btn secondary"
                    onClick={() => onRemove(l.sku)}
                    aria-label={`Quitar ${l.name} del carrito`}
                  >
                    Quitar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <p className="total" aria-live="polite">
        Total: {money(total)}
      </p>

      <div className="field">
        <label htmlFor="payment">Método de pago</label>
        <select
          id="payment"
          value={paymentMethod}
          onChange={(e) => onPaymentMethodChange(e.target.value as PaymentMethod)}
        >
          <option value="efectivo">Efectivo</option>
          <option value="tarjeta">Tarjeta</option>
        </select>
      </div>

      <button
        className="btn"
        onClick={onConfirm}
        disabled={empty || confirming}
      >
        {confirming ? "Procesando…" : "Cobrar"}
      </button>
    </section>
  );
}
