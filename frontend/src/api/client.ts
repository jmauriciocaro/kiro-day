// Thin HTTP client for the POS backend.
// The base URL comes from a Vite env var (never hardcoded); the bearer token is
// injected per request. Backend errors already carry Spanish messages.

import type {
  DailyReport,
  Product,
  Sale,
  SaleItemIn,
  TokenResponse,
} from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; token?: string | null } = {},
): Promise<T> {
  const { method = "GET", body, token } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let message = "Ocurrió un error inesperado";
    try {
      const data = await response.json();
      // Domain errors -> {error}; validation errors -> {detail}
      message = data.error ?? data.detail ?? message;
      if (Array.isArray(message)) message = "Datos inválidos";
    } catch {
      // keep default message
    }
    throw new ApiError(response.status, message as string);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  login(username: string, password: string): Promise<TokenResponse> {
    return request<TokenResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
  },

  listProducts(token: string): Promise<Product[]> {
    return request<Product[]>("/products", { token });
  },

  createSale(
    token: string,
    items: SaleItemIn[],
    paymentMethod: string,
  ): Promise<Sale> {
    return request<Sale>("/sales", {
      method: "POST",
      token,
      body: { items, payment_method: paymentMethod },
    });
  },

  dailyReport(token: string, date?: string): Promise<DailyReport> {
    const query = date ? `?date=${encodeURIComponent(date)}` : "";
    return request<DailyReport>(`/reports/daily${query}`, { token });
  },
};
