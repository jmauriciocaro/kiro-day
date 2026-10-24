// Centralized sale-cart state: the single source of truth for the Caja screen.
import { useCallback, useMemo, useState } from "react";
import type { CartLine, Product, SaleItemIn } from "../types";

export function useCart() {
  const [lines, setLines] = useState<CartLine[]>([]);

  const add = useCallback((product: Product) => {
    setLines((prev) => {
      const existing = prev.find((l) => l.sku === product.sku);
      if (existing) {
        // Do not exceed available stock when bumping the quantity.
        const nextQty = Math.min(existing.qty + 1, product.stock);
        return prev.map((l) =>
          l.sku === product.sku ? { ...l, qty: nextQty } : l,
        );
      }
      return [
        ...prev,
        {
          sku: product.sku,
          name: product.name,
          price: product.price,
          qty: 1,
          stock: product.stock,
        },
      ];
    });
  }, []);

  const setQty = useCallback((sku: string, qty: number) => {
    setLines((prev) =>
      prev
        .map((l) =>
          l.sku === sku ? { ...l, qty: Math.min(qty, l.stock) } : l,
        )
        .filter((l) => l.qty > 0),
    );
  }, []);

  const remove = useCallback((sku: string) => {
    setLines((prev) => prev.filter((l) => l.sku !== sku));
  }, []);

  const clear = useCallback(() => setLines([]), []);

  const total = useMemo(
    () => lines.reduce((sum, l) => sum + Number(l.price) * l.qty, 0),
    [lines],
  );

  const toItems = useCallback(
    (): SaleItemIn[] => lines.map((l) => ({ sku: l.sku, qty: l.qty })),
    [lines],
  );

  return { lines, add, setQty, remove, clear, total, toItems };
}
