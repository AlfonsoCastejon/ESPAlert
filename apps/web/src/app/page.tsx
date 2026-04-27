"use client";

/**
 * Página principal: mapa de alertas con panel lateral de filtros.
 * Carga 200 alertas por fuente cada 60 s y las ordena por severidad.
 */

import { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import AlertFilters from "@/components/filters/AlertFilters";

const AlertMap = dynamic(() => import("@/components/map/AlertMap"), {
  ssr: false,
  loading: () => <div className="pagina-estado pagina-estado--centrado">Cargando mapa...</div>,
});
import { FILTROS_INICIALES } from "@/types/filters";
import type { EstadoFiltros } from "@/types/filters";
import type { Alerta, ColorAlerta } from "@/types/alert";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Mapeo de severidad del filtro (español) a los colores de la API (inglés) */
const COLOR_A_SEVERIDAD: Record<string, ColorAlerta[]> = {
  verde: ["green"],
  amarillo: ["yellow"],
  naranja: ["orange"],
  rojo: ["red"],
};

/** Mapeo del tipo que devuelve la API al nombre interno del filtro */
const TIPO_API_A_FILTRO: Record<string, keyof EstadoFiltros["tipos"]> = {
  meteorological: "meteorologico",
  seismic: "sismico",
  traffic: "trafico",
  mesh: "mesh",
};

export default function Home() {
  const [filtros, setFiltros] = useState<EstadoFiltros>(FILTROS_INICIALES);
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [filtrosAbiertos, setFiltrosAbiertos] = useState(false);
  const [errorConexion, setErrorConexion] = useState(false);

  const cargarAlertas = useCallback(async () => {
    try {
      const fuentes = ["aemet", "ign", "dgt", "meteoalarm", "meshtastic"];
      const peticiones = fuentes.map((fuente) => {
        const params = new URLSearchParams();
        params.set("source", fuente);
        params.set("limit", "200");
        if (filtros.region) params.set("region", filtros.region);
        return fetch(`${API_URL}/api/alerts?${params}`)
          .then((r) => (r.ok ? r.json() : { items: [] }))
          .then((d) => d.items || []);
      });

      const resultados = await Promise.all(peticiones);
      const todas: Alerta[] = resultados.flat();

      const ordenSeveridad: Record<string, number> = {
        red: 0, orange: 1, yellow: 2, green: 3, purple: 4,
      };
      todas.sort((a, b) => (ordenSeveridad[a.color] ?? 9) - (ordenSeveridad[b.color] ?? 9));

      setAlertas(todas);
      setErrorConexion(false);
    } catch {
      setErrorConexion(true);
    }
  }, [filtros.region]);

  useEffect(() => {
    cargarAlertas();
    const intervalo = setInterval(cargarAlertas, 60_000);
    return () => clearInterval(intervalo);
  }, [cargarAlertas]);

  const alertasFiltradas = alertas.filter((a) => {
    const tipoFiltro = TIPO_API_A_FILTRO[a.alert_type];
    if (!tipoFiltro || !filtros.tipos[tipoFiltro]) {
      return false;
    }

    const activas = Object.entries(filtros.severidades)
      .filter(([, v]) => v)
      .flatMap(([k]) => COLOR_A_SEVERIDAD[k] || []);

    if (a.color === "purple") return filtros.tipos.mesh;
    return activas.includes(a.color);
  });

  const ahora = Date.now();
  const hace24h = ahora - 24 * 60 * 60 * 1000;
  const hace7d = ahora - 7 * 24 * 60 * 60 * 1000;
  const alertasMapa = alertasFiltradas.filter((a) => {
    const fecha = new Date(a.effective_at || a.created_at).getTime();
    const umbral = a.source === "meshtastic" ? hace7d : hace24h;
    return fecha >= umbral;
  });

  return (
    <>
      <h1 className="sr-only">Mapa de alertas de riesgo en España</h1>
      <aside className="lateral">
        <AlertFilters
          filtros={filtros}
          onCambio={setFiltros}
          alertas={alertasFiltradas}
          idPrefijo="filtro-lateral"
        />
      </aside>

      <div
        className={`bandeja ${filtrosAbiertos ? "bandeja--abierta" : ""}`}
      >
        <div className="bandeja__asa" onClick={() => setFiltrosAbiertos(!filtrosAbiertos)}>
          <span className="bandeja__asa-linea" />
        </div>
        <div className="bandeja__contenido">
          <AlertFilters
            filtros={filtros}
            onCambio={setFiltros}
            alertas={alertasFiltradas}
            idPrefijo="filtro-bandeja"
          />
        </div>
      </div>

      {filtrosAbiertos && (
        <div className="overlay overlay--bandeja" onClick={() => setFiltrosAbiertos(false)} />
      )}

      <div className="contenedor-mapa">
        {errorConexion && (
          <div className="mapa-error">Sin conexión con el servidor</div>
        )}
        <AlertMap alertas={alertasMapa} region={filtros.region} />
        <button
          className="boton-filtros"
          onClick={() => setFiltrosAbiertos(true)}
        >
          Filtros
        </button>
      </div>
    </>
  );
}
