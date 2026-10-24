import { money } from "../format";
import type { Product } from "../types";

interface Props {
  products: Product[];
  onAdd: (product: Product) => void;
}

export function Catalogo({ products, onAdd }: Props) {
  if (products.length === 0) {
    return <p>No hay productos en el catálogo.</p>;
  }
  return (
    <section className="card" aria-label="Catálogo de productos">
      <h2>Catálogo</h2>
      <div className="grid">
        {products.map((p) => {
          const agotado = p.stock <= 0;
          return (
            <button
              key={p.sku}
              className="btn secondary"
              onClick={() => onAdd(p)}
              disabled={agotado}
              aria-label={`Agregar ${p.name}, ${money(p.price)}, ${
                agotado ? "agotado" : `${p.stock} en stock`
              }`}
            >
              <strong>{p.name}</strong>
              <br />
              {money(p.price)}
              <br />
              <small>{agotado ? "Agotado" : `Stock: ${p.stock}`}</small>
            </button>
          );
        })}
      </div>
    </section>
  );
}
