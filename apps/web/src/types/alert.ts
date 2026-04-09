/** Tipos e interfaces de las alertas recibidas desde la API */

export type TipoAlerta = "meteorologico" | "sismico" | "trafico" | "mesh";
export type Severidad = "minor" | "moderate" | "severe" | "extreme" | "unknown";
export type ColorAlerta = "green" | "yellow" | "orange" | "red" | "purple";
export type FuenteAlerta = "aemet" | "ign" | "dgt" | "meteoalarm" | "meshtastic";

export interface Alerta {
  id: string;
  external_id: string | null;
  source: FuenteAlerta;
  alert_type: TipoAlerta;
  severity: Severidad;
  color: ColorAlerta;
  headline: string;
  description: string | null;
  area_description: string | null;
  geometry: GeoJSON.Geometry | null;
  effective_at: string | null;
  expires_at: string | null;
  fetched_at: string;
  created_at: string;
}

export interface RespuestaAlertas {
  total: number;
  items: Alerta[];
  limit: number;
  offset: number;
}
