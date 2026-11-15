const currencyFormatter = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
});

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value));
}
