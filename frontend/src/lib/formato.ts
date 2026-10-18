const numero = new Intl.NumberFormat("pt-BR");
const decimal = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const dataHora = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});
const data = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeZone: "UTC" });

export const fmtNumero = (v: number) => numero.format(v);
export const fmtPct = (v: number | null) => (v === null ? "—" : `${decimal.format(v)}%`);
export const fmtHoras = (v: number | null) => (v === null ? "—" : `${decimal.format(v)} h`);
export const fmtDataHora = (iso: string) => dataHora.format(new Date(iso));
/** Datas "YYYY-MM-DD" sem fuso (evita voltar um dia ao converter). */
export const fmtData = (iso: string) => data.format(new Date(`${iso}T00:00:00Z`));
