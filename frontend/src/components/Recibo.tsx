import { money } from "../format";
import type { Sale } from "../types";

interface Props {
  sale: Sale;
  onClose: () => void;
}

export function Recibo({ sale, onClose }: Props) {
  return (
    <section className="card" aria-label="Recibo de la venta" role="status">
      <h2 className="ok">Venta registrada ✓</h2>
      <p>
        <strong>Recibo:</strong> {sale.sale_id.slice(0, 8)}
        <br />
        <strong>Fecha:</strong> {new Date(sale.created_at).toLocaleString("es-CO")}
      </p>
      <table>
        <thead>
          <tr>
            <th>Producto</th>
            <th>Cant.</th>
            <th>Precio</th>
            <th>Subtotal</th>
          </tr>
        </thead>
        <tbody>
          {sale.items.map((it) => (
            <tr key={it.sku}>
              <td>{it.name}</td>
              <td>{it.qty}</td>
              <td>{money(it.unit_price)}</td>
              <td>{money(Number(it.unit_price) * it.qty)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="total">Total: {money(sale.total)}</p>
      <p>Pago: {sale.payment_method} — {sale.payment_status}</p>
      <button className="btn" onClick={onClose} autoFocus>
        Nueva venta
      </button>
    </section>
  );
}
