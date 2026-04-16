"use client";

/**
 * Página de predicción meteorológica.
 * Buscador de municipios + tabla de predicción diaria estilo AEMET.
 */

import { useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Municipio {
  codigo: string;
  nombre: string;
}

interface PeriodoCielo {
  periodo: string;
  valor: string;
  descripcion: string;
}

interface PeriodoPrecip {
  periodo: string;
  valor: number;
}

interface PeriodoViento {
  periodo: string;
  direccion: string;
  velocidad: number;
}

interface PeriodoCota {
  periodo: string;
  valor: string;
}

interface DiaPrediccion {
  fecha: string;
  temp_max: number | null;
  temp_min: number | null;
  sens_termica_max: number | null;
  sens_termica_min: number | null;
  humedad_max: number | null;
  humedad_min: number | null;
  prob_precipitacion: PeriodoPrecip[];
  cota_nieve: PeriodoCota[];
  estado_cielo: PeriodoCielo[];
  viento: PeriodoViento[];
  racha_max: number | null;
  uv_max: number | null;
}

interface Prediccion {
  municipio: string;
  provincia: string;
  elaborado: string;
  dias: DiaPrediccion[];
}

/** Icono del cielo según el código AEMET */
function iconoCielo(codigo: string): string {
  if (!codigo) return "\u2014";
  const c = codigo.replace("n", "");
  const mapa: Record<string, string> = {
    "11": "\u2600\uFE0F", "12": "\u26C5", "13": "\u26C5",
    "14": "\u2601\uFE0F", "15": "\u2601\uFE0F", "16": "\u2601\uFE0F",
    "17": "\u26C5", "23": "\u{1F326}\uFE0F", "24": "\u{1F326}\uFE0F",
    "25": "\u{1F326}\uFE0F", "26": "\u{1F326}\uFE0F",
    "33": "\u{1F327}\uFE0F", "34": "\u{1F327}\uFE0F",
    "35": "\u{1F327}\uFE0F", "36": "\u{1F327}\uFE0F",
    "43": "\u{1F327}\uFE0F", "44": "\u{1F327}\uFE0F",
    "45": "\u{1F327}\uFE0F", "46": "\u{1F327}\uFE0F",
    "51": "\u{1F329}\uFE0F", "52": "\u{1F329}\uFE0F",
    "53": "\u{1F329}\uFE0F", "54": "\u{1F329}\uFE0F",
    "61": "\u{1F329}\uFE0F", "62": "\u{1F329}\uFE0F",
    "63": "\u{1F329}\uFE0F", "64": "\u{1F329}\uFE0F",
    "71": "\u2744\uFE0F", "72": "\u2744\uFE0F",
    "73": "\u2744\uFE0F", "74": "\u2744\uFE0F",
    "81": "\u{1F32B}\uFE0F", "82": "\u{1F32B}\uFE0F",
  };
  return mapa[c] || "\u2601\uFE0F";
}

function formatearDia(fechaISO: string): string {
  const d = new Date(fechaISO);
  return d.toLocaleDateString("es-ES", { weekday: "short", day: "numeric", month: "short" });
}

function etiquetaPeriodo(periodo: string): string {
  if (!periodo) return "";
  return periodo.replace("-", "\u2013") + " h";
}

/** Determina qué sub-periodos mostrar para un día según los datos disponibles */
function obtenerPeriodosVisibles(dia: DiaPrediccion): string[] {
  const p6h = ["00-06", "06-12", "12-18", "18-24"];
  const tiene6h = p6h.some((p) =>
    dia.estado_cielo.some((ec) => ec.periodo === p && ec.valor),
  );
  if (tiene6h) {
    return p6h.filter((p) =>
      dia.estado_cielo.some((ec) => ec.periodo === p && ec.valor),
    );
  }

  const p12h = ["00-12", "12-24"];
  const tiene12h = p12h.some((p) =>
    dia.estado_cielo.some((ec) => ec.periodo === p && ec.valor),
  );
  if (tiene12h) return p12h;

  return [""];
}

function buscarPeriodo<T extends { periodo: string }>(arr: T[], periodo: string): T | undefined {
  return arr.find((item) => item.periodo === periodo);
}

export default function PrediccionPage() {
  const [busqueda, setBusqueda] = useState("");
  const [sugerencias, setSugerencias] = useState<Municipio[]>([]);
  const [cargandoBusqueda, setCargandoBusqueda] = useState(false);
  const [prediccion, setPrediccion] = useState<Prediccion | null>(null);
  const [cargandoPred, setCargandoPred] = useState(false);
  const [error, setError] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  function buscar(texto: string) {
    setBusqueda(texto);
    setError("");
    if (timerRef.current) clearTimeout(timerRef.current);
    if (abortRef.current) abortRef.current.abort();
    if (texto.length < 2) {
      setSugerencias([]);
      return;
    }

    timerRef.current = setTimeout(async () => {
      const controller = new AbortController();
      abortRef.current = controller;
      setCargandoBusqueda(true);
      try {
        const res = await fetch(
          `${API_URL}/api/forecast/municipios?q=${encodeURIComponent(texto)}`,
          { signal: controller.signal },
        );
        if (res.ok) setSugerencias(await res.json());
      } catch (e) {
        if (e instanceof DOMException && e.name === "AbortError") return;
      } finally {
        setCargandoBusqueda(false);
      }
    }, 300);
  }

  async function seleccionar(m: Municipio) {
    setBusqueda(m.nombre);
    setSugerencias([]);
    setCargandoPred(true);
    setError("");
    setPrediccion(null);

    try {
      const res = await fetch(`${API_URL}/api/forecast/${m.codigo}`);
      if (!res.ok) {
        setError("No se pudo obtener la predicción para este municipio.");
        return;
      }
      setPrediccion(await res.json());
    } catch {
      setError("Error de conexión con el servidor.");
    } finally {
      setCargandoPred(false);
    }
  }

  // Filtrar días anteriores al actual y procesar periodos
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);

  const diasProcesados = prediccion?.dias
    .filter((dia) => new Date(dia.fecha) >= hoy)
    .map((dia) => ({
      dia,
      periodos: obtenerPeriodosVisibles(dia),
    })) || [];

  return (
    <div className="prediccion">
      <div className="prediccion__cabecera">
        <h1 className="prediccion__titulo">Predicción meteorológica</h1>
        <p className="prediccion__subtitulo">
          Busca un municipio para ver la predicción diaria — Fuente: AEMET
        </p>
      </div>

      <div className="prediccion__buscador">
        <input
          type="text"
          className="prediccion__input"
          placeholder="Escribe un municipio..."
          value={busqueda}
          onChange={(e) => buscar(e.target.value)}
        />
        {cargandoBusqueda && <span className="prediccion__spinner" />}

        {sugerencias.length > 0 && (
          <ul className="prediccion__sugerencias">
            {sugerencias.map((m) => (
              <li key={m.codigo}>
                <button
                  className="prediccion__sugerencia"
                  onClick={() => seleccionar(m)}
                >
                  {m.nombre}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && <p className="prediccion__error">{error}</p>}

      {cargandoPred && <p className="prediccion__estado">Cargando predicción...</p>}

      {prediccion && diasProcesados.length > 0 && (
        <div className="prediccion__resultado">
          <h2 className="prediccion__municipio">
            {prediccion.municipio}
            <span className="prediccion__provincia">{prediccion.provincia}</span>
          </h2>

          <div className="prediccion__tabla-wrapper">
            <table className="prediccion__tabla">
              <thead>
                <tr>
                  <th className="prediccion__th prediccion__th--fijo" rowSpan={2}></th>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <th
                      key={dia.fecha}
                      className="prediccion__th prediccion__th--dia"
                      colSpan={periodos.length}
                    >
                      {formatearDia(dia.fecha)}
                    </th>
                  ))}
                </tr>
                <tr>
                  {diasProcesados.flatMap(({ dia, periodos }) =>
                    periodos.map((p) => (
                      <th
                        key={`per-${dia.fecha}-${p}`}
                        className="prediccion__th prediccion__th--periodo"
                      >
                        {etiquetaPeriodo(p)}
                      </th>
                    )),
                  )}
                </tr>
              </thead>
              <tbody>
                {/* Estado del cielo */}
                <tr>
                  <td className="prediccion__etiqueta">Estado del cielo</td>
                  {diasProcesados.flatMap(({ dia, periodos }) =>
                    periodos.map((p) => {
                      const ec = buscarPeriodo(dia.estado_cielo, p);
                      return (
                        <td
                          key={`cielo-${dia.fecha}-${p}`}
                          className="prediccion__celda prediccion__celda--cielo"
                          title={ec?.descripcion || ""}
                        >
                          {ec?.valor ? iconoCielo(ec.valor) : "\u2014"}
                          {ec?.descripcion && (
                            <span className="prediccion__cielo-texto">{ec.descripcion}</span>
                          )}
                        </td>
                      );
                    }),
                  )}
                </tr>

                {/* Probabilidad de precipitación */}
                <tr>
                  <td className="prediccion__etiqueta">Prob. precipitación</td>
                  {diasProcesados.flatMap(({ dia, periodos }) =>
                    periodos.map((p) => {
                      const pp = buscarPeriodo(dia.prob_precipitacion, p);
                      return (
                        <td key={`precip-${dia.fecha}-${p}`} className="prediccion__celda">
                          {pp ? `${pp.valor}%` : "\u2014"}
                        </td>
                      );
                    }),
                  )}
                </tr>

                {/* Cota de nieve */}
                <tr>
                  <td className="prediccion__etiqueta">Cota nieve (m)</td>
                  {diasProcesados.flatMap(({ dia, periodos }) =>
                    periodos.map((p) => {
                      const cn = buscarPeriodo(dia.cota_nieve, p);
                      return (
                        <td key={`cota-${dia.fecha}-${p}`} className="prediccion__celda">
                          {cn?.valor || "\u2014"}
                        </td>
                      );
                    }),
                  )}
                </tr>

                {/* Temperatura mínima y máxima */}
                <tr>
                  <td className="prediccion__etiqueta">Temperatura (°C)</td>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <td
                      key={`temp-${dia.fecha}`}
                      className="prediccion__celda prediccion__celda--temp"
                      colSpan={periodos.length}
                    >
                      {dia.temp_min != null && (
                        <span className="prediccion__temp-min">{dia.temp_min}</span>
                      )}
                      {dia.temp_min != null && dia.temp_max != null && " / "}
                      {dia.temp_max != null && (
                        <span className="prediccion__temp-max">{dia.temp_max}</span>
                      )}
                      {dia.temp_min == null && dia.temp_max == null && "\u2014"}
                    </td>
                  ))}
                </tr>

                {/* Sensación térmica mínima y máxima */}
                <tr>
                  <td className="prediccion__etiqueta">Sens. térmica (°C)</td>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <td
                      key={`sens-${dia.fecha}`}
                      className="prediccion__celda prediccion__celda--temp"
                      colSpan={periodos.length}
                    >
                      {dia.sens_termica_min != null && (
                        <span className="prediccion__temp-min">{dia.sens_termica_min}</span>
                      )}
                      {dia.sens_termica_min != null && dia.sens_termica_max != null && " / "}
                      {dia.sens_termica_max != null && (
                        <span className="prediccion__temp-max">{dia.sens_termica_max}</span>
                      )}
                      {dia.sens_termica_min == null && dia.sens_termica_max == null && "\u2014"}
                    </td>
                  ))}
                </tr>

                {/* Humedad relativa mínima y máxima */}
                <tr>
                  <td className="prediccion__etiqueta">Humedad (%)</td>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <td
                      key={`humedad-${dia.fecha}`}
                      className="prediccion__celda"
                      colSpan={periodos.length}
                    >
                      {dia.humedad_min != null && dia.humedad_max != null
                        ? `${dia.humedad_min} / ${dia.humedad_max}`
                        : "\u2014"}
                    </td>
                  ))}
                </tr>

                {/* Dirección y velocidad del viento */}
                <tr>
                  <td className="prediccion__etiqueta">Viento (km/h)</td>
                  {diasProcesados.flatMap(({ dia, periodos }) =>
                    periodos.map((p) => {
                      const v = buscarPeriodo(dia.viento, p);
                      return (
                        <td key={`viento-${dia.fecha}-${p}`} className="prediccion__celda">
                          {v && (v.direccion || v.velocidad)
                            ? `${v.direccion} ${v.velocidad}`
                            : "\u2014"}
                        </td>
                      );
                    }),
                  )}
                </tr>

                {/* Racha máxima */}
                <tr>
                  <td className="prediccion__etiqueta">Racha máx. (km/h)</td>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <td
                      key={`racha-${dia.fecha}`}
                      className="prediccion__celda"
                      colSpan={periodos.length}
                    >
                      {dia.racha_max != null ? dia.racha_max : "\u2014"}
                    </td>
                  ))}
                </tr>

                {/* Índice UV */}
                <tr>
                  <td className="prediccion__etiqueta">Índice UV</td>
                  {diasProcesados.map(({ dia, periodos }) => (
                    <td
                      key={`uv-${dia.fecha}`}
                      className="prediccion__celda"
                      colSpan={periodos.length}
                    >
                      {dia.uv_max != null ? dia.uv_max : "\u2014"}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>

          <p className="prediccion__aviso">
            Datos de AEMET — Elaborado: {prediccion.elaborado ? new Date(prediccion.elaborado).toLocaleString("es-ES") : "\u2014"}
          </p>
        </div>
      )}
    </div>
  );
}
