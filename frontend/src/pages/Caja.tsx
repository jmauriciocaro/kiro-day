import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useCart } from "../cart/useCart";
import { Carrito } from "../components/Carrito";
import { Catalogo } from "../components/Catalogo";
import { Recibo } from "../components/Recibo";
import { money } from "../format";
import type { PaymentMethod, Product, Sale } from "../types";

export function Caja() {
  const { token } = useAuth();
  const cart = useCart();
  const [products, setProducts] = useState<Product[]>([]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("efectivo");
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [lastSale, setLastSale] = useState<Sale | null>(null);

  async function loadProducts() {
    if (!token) return;
    try {
      setProducts(await api.listProducts(token));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cargar el catálogo");
    }
  }

  useEffect(() => {
    void loadProducts();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function handleConfirm() {
    if (!token) return;
    const confirmed = window.confirm(
      `¿Confirmar la venta por un total de ${money(cart.total)}?`,
    );
    if (!confirmed) return;

    setError(null);
    setConfirming(true);
    try {
      const sale = await api.createSale(token, cart.toItems(), paymentMethod);
      setLastSale(sale);
      cart.clear();
      await loadProducts(); // refresh stock
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo registrar la venta");
    } finally {
      setConfirming(false);
    }
  }

  if (lastSale) {
    return <Recibo sale={lastSale} onClose={() => setLastSale(null)} />;
  }

  return (
    <div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <Catalogo products={products} onAdd={cart.add} />
      <Carrito
        lines={cart.lines}
        total={cart.total}
        paymentMethod={paymentMethod}
        onPaymentMethodChange={setPaymentMethod}
        onSetQty={cart.setQty}
        onRemove={cart.remove}
        onConfirm={handleConfirm}
        confirming={confirming}
      />
    </div>
  );
}
