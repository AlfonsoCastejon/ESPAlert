import type { TipoAlerta } from "./alert";

export interface EstadoFiltros {
  tipos: Record<TipoAlerta, boolean>;
  severidades: Record<string, boolean>;
  region: string;
}

export const FILTROS_INICIALES: EstadoFiltros = {
  tipos: {
    meteorologico: true,
    sismico: true,
    trafico: true,
    mesh: true,
  },
  severidades: {
    verde: true,
    amarillo: true,
    naranja: true,
    rojo: true,
  },
  region: "",
};

export const REGIONES = [
  { valor: "", etiqueta: "Toda España" },
  { valor: "andalucia", etiqueta: "Andalucía" },
  { valor: "aragon", etiqueta: "Aragón" },
  { valor: "asturias", etiqueta: "Asturias" },
  { valor: "baleares", etiqueta: "Baleares" },
  { valor: "canarias", etiqueta: "Canarias" },
  { valor: "cantabria", etiqueta: "Cantabria" },
  { valor: "castilla-la-mancha", etiqueta: "Castilla-La Mancha" },
  { valor: "castilla-y-leon", etiqueta: "Castilla y León" },
  { valor: "cataluna", etiqueta: "Cataluña" },
  { valor: "ceuta", etiqueta: "Ceuta" },
  { valor: "extremadura", etiqueta: "Extremadura" },
  { valor: "galicia", etiqueta: "Galicia" },
  { valor: "la-rioja", etiqueta: "La Rioja" },
  { valor: "madrid", etiqueta: "Madrid" },
  { valor: "melilla", etiqueta: "Melilla" },
  { valor: "murcia", etiqueta: "Murcia" },
  { valor: "navarra", etiqueta: "Navarra" },
  { valor: "pais-vasco", etiqueta: "País Vasco" },
  { valor: "valencia", etiqueta: "Valencia" },
];
