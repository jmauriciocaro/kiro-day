// TypeScript mirror of the backend Pydantic models.
// Monetary values arrive as strings (Decimal serialized) to preserve precision.

export type PaymentMethod = "efectivo" | "tarjeta";
export type Role = "cajero" | "dueno";

export interface Product {
  sku: string;
  name: string;
  price: string;
  stock: number;
}

export interface SaleItemIn {
  sku: string;
  qty: number;
}

export interface SaleItem extends SaleItemIn {
  name: string;
  unit_price: string;
}

export interface Sale {
  sale_id: string;
  created_at: string;
  items: SaleItem[];
  total: string;
  payment_method: PaymentMethod;
  payment_status: string;
  cashier: string;
}

export interface DailyReport {
  date: string;
  sales: Sale[];
  total: string;
  count: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: Role;
}

// Local cart line used by the Caja screen.
export interface CartLine {
  sku: string;
  name: string;
  price: string;
  qty: number;
  stock: number;
}
