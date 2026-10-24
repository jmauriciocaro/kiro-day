// Shared currency formatter so every screen shows money consistently.
const formatter = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
});

export function money(value: string | number): string {
  return formatter.format(Number(value));
}
