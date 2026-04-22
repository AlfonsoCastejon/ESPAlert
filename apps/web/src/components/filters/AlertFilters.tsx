"use client";

/**
 * Panel de filtros del sidebar: tipo de alerta, severidad y zona geográfica.
 * Muestra debajo un listado de las alertas graves (roja y naranja).
 */

import type { Alerta } from "@/types/alert";
import type { EstadoFiltros } from "@/types/filters";
import { REGIONES } from "@/types/filters";

interface AlertFiltersProps {
  filtros: EstadoFiltros;
  onCambio: (filtros: EstadoFiltros) => void;
  alertas: Alerta[];
}

const TIPOS = [
  { clave: "meteorologico" as const, etiqueta: "Meteorológico" },
  { clave: "sismico" as const, etiqueta: "Sísmico" },
  { clave: "trafico" as const, etiqueta: "Tráfico" },
  { clave: "mesh" as const, etiqueta: "Mesh" },
];

const SEVERIDADES = [
  { clave: "verde", etiqueta: "Verde", color: "var(--color-verde-alerta)" },
  { clave: "amarillo", etiqueta: "Amarillo", color: "var(--color-amarillo-alerta)" },
  { clave: "naranja", etiqueta: "Naranja", color: "var(--color-naranja-alerta)" },
  { clave: "rojo", etiqueta: "Rojo", color: "var(--color-rojo-alerta)" },
];

export default function AlertFilters({
  filtros,
  onCambio,
  alertas,
}: AlertFiltersProps) {
  function toggleTipo(clave: keyof EstadoFiltros["tipos"]) {
    onCambio({
      ...filtros,
      tipos: { ...filtros.tipos, [clave]: !filtros.tipos[clave] },
    });
  }

  function toggleSeveridad(clave: string) {
    onCambio({
      ...filtros,
      severidades: {
        ...filtros.severidades,
        [clave]: !filtros.severidades[clave],
      },
    });
  }

  function cambiarRegion(valor: string) {
    onCambio({ ...filtros, region: valor });
  }

  const alertasGraves = alertas.filter(
    (a) => a.color === "red" || a.color === "orange"
  );

  return (
    <div className="filtros">
      <h2 className="filtros__titulo">Filtros</h2>

      <fieldset className="filtros__seccion">
        <legend className="filtros__etiqueta">Tipo de alerta</legend>
        {TIPOS.map((tipo) => (
          <label key={tipo.clave} className="filtros__opcion">
            <input
              id={`filtro-tipo-${tipo.clave}`}
              type="checkbox"
              title={tipo.etiqueta}
              aria-label={tipo.etiqueta}
              checked={filtros.tipos[tipo.clave]}
              onChange={() => toggleTipo(tipo.clave)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  toggleTipo(tipo.clave);
                }
              }}
            />
            {tipo.etiqueta}
          </label>
        ))}
      </fieldset>

      <fieldset className="filtros__seccion">
        <legend className="filtros__etiqueta">Severidad</legend>
        {SEVERIDADES.map((sev) => (
          <label
            key={sev.clave}
            className={`filtros__opcion-severidad ${
              filtros.severidades[sev.clave] ? "filtros__opcion-severidad--activo" : ""
            }`}
          >
            <input
              id={`filtro-severidad-${sev.clave}`}
              type="checkbox"
              className="filtros__check-oculto"
              title={sev.etiqueta}
              aria-label={sev.etiqueta}
              checked={filtros.severidades[sev.clave]}
              onChange={() => toggleSeveridad(sev.clave)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  toggleSeveridad(sev.clave);
                }
              }}
            />
            <span
              className={`filtros__indicador filtros__indicador--${sev.clave}`}
            />
            {sev.etiqueta}
          </label>
        ))}
      </fieldset>

      <div className="filtros__seccion">
        <label className="filtros__etiqueta" htmlFor="filtro-region">
          Zona geográfica
        </label>
        <select
          id="filtro-region"
          className="filtros__select"
          value={filtros.region}
          onChange={(e) => cambiarRegion(e.target.value)}
        >
          {REGIONES.map((r) => (
            <option key={r.valor} value={r.valor}>
              {r.etiqueta}
            </option>
          ))}
        </select>
      </div>

      <p className="filtros__contador">
        Alertas graves ({alertasGraves.length})
      </p>

      <div className="filtros__lista">
        {alertasGraves.map((alerta) => (
          <div
            key={alerta.id}
            className={`tarjeta-alerta tarjeta-alerta--${colorACss(alerta.color)}`}
          >
            <div className="tarjeta-alerta__titulo">{alerta.headline}</div>
            <div className="tarjeta-alerta__fuente">
              {fuenteTexto(alerta.source)} - {alerta.area_description || "España"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Traduce el color de la API (green, red...) al nombre CSS en español */
function colorACss(color: string): string {
  const mapa: Record<string, string> = {
    green: "verde",
    yellow: "amarillo",
    orange: "naranja",
    red: "rojo",
    purple: "morado",
  };
  return mapa[color] || "verde";
}

/** Nombre legible de cada fuente para mostrar en la tarjeta */
function fuenteTexto(source: string): string {
  const mapa: Record<string, string> = {
    aemet: "AEMET",
    ign: "IGN",
    dgt: "DGT",
    meteoalarm: "MeteoAlarm",
    meshtastic: "Mesh",
  };
  return mapa[source] || source;
}
