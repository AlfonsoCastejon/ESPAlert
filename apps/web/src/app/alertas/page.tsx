"use client";

/**
 * Página de alertas: listado completo con filtros por fuente, severidad y región.
 * Permite ordenar por fecha o severidad y paginar los resultados.
 */

import { useState, useEffect, useCallback } from "react";
import { Star } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { REGIONES } from "@/types/filters";
import type { Alerta, FuenteAlerta, ColorAlerta } from "@/types/alert";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const POR_PAGINA = 20;

const FUENTES: { valor: FuenteAlerta | ""; etiqueta: string }[] = [
  { valor: "", etiqueta: "Todas las fuentes" },
  { valor: "aemet", etiqueta: "AEMET" },
  { valor: "ign", etiqueta: "IGN" },
  { valor: "dgt", etiqueta: "DGT" },
  { valor: "meteoalarm", etiqueta: "MeteoAlarm" },
  { valor: "meshtastic", etiqueta: "Meshtastic" },
];

const SEVERIDADES_FILTRO: { valor: string; etiqueta: string }[] = [
  { valor: "", etiqueta: "Todas" },
  { valor: "extreme", etiqueta: "Extrema" },
  { valor: "severe", etiqueta: "Severa" },
  { valor: "moderate", etiqueta: "Moderada" },
  { valor: "minor", etiqueta: "Menor" },
];

const ORDEN_SEVERIDAD: Record<string, number> = {
  red: 0, orange: 1, yellow: 2, green: 3, purple: 4,
};

const NOMBRE_FUENTE: Record<string, string> = {
  aemet: "AEMET", ign: "IGN", dgt: "DGT",
  meteoalarm: "MeteoAlarm", meshtastic: "Meshtastic",
};

const COLOR_CSS: Record<ColorAlerta, string> = {
  red: "rojo", orange: "naranja", yellow: "amarillo",
  green: "verde", purple: "morado",
};

const ETIQUETA_SEVERIDAD: Record<string, string> = {
  extreme: "Extrema", severe: "Severa", moderate: "Moderada",
  minor: "Menor", unknown: "Desconocida",
};

type Orden = "fecha" | "severidad";

export default function AlertasPage() {
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [total, setTotal] = useState(0);
  const [pagina, setPagina] = useState(0);
  const [cargando, setCargando] = useState(true);

  const [fuente, setFuente] = useState("");
  const [severidad, setSeveridad] = useState("");
  const [region, setRegion] = useState("");
  const [orden, setOrden] = useState<Orden>("severidad");
  const [alertaAbierta, setAlertaAbierta] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [favoritosIds, setFavoritosIds] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState("");
  const { usuario } = useAuth();
  const esAdmin = usuario?.role === "admin";

  function mostrarToast(mensaje: string) {
    setToast(mensaje);
    setTimeout(() => setToast(""), 2000);
  }

  async function copiarUuid(e: React.MouseEvent, alertId: string) {
    e.stopPropagation();
    try {
      await navigator.clipboard.writeText(alertId);
      mostrarToast("UUID copiado al portapapeles");
    } catch {
      /* ignorar */
    }
  }

  async function eliminarAlerta(e: React.MouseEvent, alertId: string) {
    e.stopPropagation();
    if (!window.confirm("¿Eliminar esta alerta?")) return;
    try {
      const res = await fetch(`${API_URL}/api/admin/alerts/${alertId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        setAlertas((prev) => prev.filter((a) => a.id !== alertId));
        setTotal((t) => Math.max(0, t - 1));
        mostrarToast("Alerta eliminada");
      } else {
        mostrarToast("No se pudo eliminar");
      }
    } catch {
      mostrarToast("Error al eliminar");
    }
  }

  const cargar = useCallback(async () => {
    setCargando(true);
    setError("");
    try {
      const params = new URLSearchParams();
      params.set("limit", String(POR_PAGINA));
      params.set("offset", String(pagina * POR_PAGINA));
      if (fuente) params.set("source", fuente);
      if (severidad) params.set("severity", severidad);
      if (region) params.set("region", region);

      const res = await fetch(`${API_URL}/api/alerts?${params}`);
      if (!res.ok) throw new Error();
      const data = await res.json();

      let items: Alerta[] = data.items || [];
      if (orden === "severidad") {
        items.sort((a, b) => (ORDEN_SEVERIDAD[a.color] ?? 9) - (ORDEN_SEVERIDAD[b.color] ?? 9));
      }

      setAlertas(items);
      setTotal(data.total || 0);
    } catch {
      setAlertas([]);
      setTotal(0);
      setError("No se pudieron cargar las alertas. Comprueba la conexión.");
    } finally {
      setCargando(false);
    }
  }, [pagina, fuente, severidad, region, orden]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  useEffect(() => {
    if (!usuario) { setFavoritosIds(new Set()); return; }
    fetch(`${API_URL}/api/user/favorites?limit=200`, { credentials: "include" })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => {
        if (data?.items) {
          setFavoritosIds(new Set(data.items.map((a: Alerta) => a.id)));
        }
      })
      .catch(() => {});
  }, [usuario]);

  async function toggleFavorito(e: React.MouseEvent, alertId: string) {
    e.stopPropagation();
    if (!usuario) return;
    const esFav = favoritosIds.has(alertId);
    try {
      const res = await fetch(`${API_URL}/api/user/favorites/${alertId}`, {
        method: esFav ? "DELETE" : "POST",
        credentials: "include",
      });
      if (res.ok || res.status === 201 || res.status === 204) {
        setFavoritosIds((prev) => {
          const next = new Set(prev);
          if (esFav) next.delete(alertId); else next.add(alertId);
          return next;
        });
      }
    } catch { /* silenciar */ }
  }

  function cambiarFiltro(setter: (v: string) => void, valor: string) {
    setter(valor);
    setPagina(0);
  }

  const totalPaginas = Math.ceil(total / POR_PAGINA);

  function formatearFecha(iso: string | null): string {
    if (!iso) return "—";
    const d = new Date(iso);
    return d.toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }

  return (
    <div className="alertas-page">
      {toast && <div className="alertas-page__toast">{toast}</div>}
      <div className="alertas-page__cabecera">
        <h1 className="alertas-page__titulo">Alertas activas</h1>
        <p className="alertas-page__subtitulo">
          {total} {total === 1 ? "alerta" : "alertas"} en tiempo real
        </p>
      </div>

      <div className="alertas-page__filtros">
        <select
          className="alertas-page__select"
          value={fuente}
          onChange={(e) => cambiarFiltro(setFuente, e.target.value)}
        >
          {FUENTES.map((f) => (
            <option key={f.valor} value={f.valor}>{f.etiqueta}</option>
          ))}
        </select>

        <select
          className="alertas-page__select"
          value={severidad}
          onChange={(e) => cambiarFiltro(setSeveridad, e.target.value)}
        >
          {SEVERIDADES_FILTRO.map((s) => (
            <option key={s.valor} value={s.valor}>{s.etiqueta}</option>
          ))}
        </select>

        <select
          className="alertas-page__select"
          value={region}
          onChange={(e) => cambiarFiltro(setRegion, e.target.value)}
        >
          {REGIONES.map((r) => (
            <option key={r.valor} value={r.valor}>{r.etiqueta}</option>
          ))}
        </select>

        <select
          className="alertas-page__select"
          value={orden}
          onChange={(e) => { setOrden(e.target.value as Orden); setPagina(0); }}
        >
          <option value="severidad">Ordenar por severidad</option>
          <option value="fecha">Ordenar por fecha</option>
        </select>
      </div>

      {error && <p className="alertas-page__error">{error}</p>}

      {cargando ? (
        <p className="alertas-page__estado">Cargando alertas...</p>
      ) : !error && alertas.length === 0 ? (
        <p className="alertas-page__estado">No se han encontrado alertas con estos filtros.</p>
      ) : (
        <div className="alertas-page__lista">
          {alertas.map((a) => (
            <article
              key={a.id}
              className={`alerta-fila alerta-fila--${COLOR_CSS[a.color] || "verde"}`}
              onClick={() => setAlertaAbierta(alertaAbierta === a.id ? null : a.id)}
            >
              <div className="alerta-fila__principal">
                <span className={`alerta-fila__indicador alerta-fila__indicador--${COLOR_CSS[a.color] || "verde"}`} />
                <div className="alerta-fila__contenido">
                  <h3 className="alerta-fila__titulo">{a.headline}</h3>
                  <div className="alerta-fila__meta">
                    <span className="alerta-fila__fuente">{NOMBRE_FUENTE[a.source] || a.source}</span>
                    <span className="alerta-fila__separador">·</span>
                    <span>{a.area_description || "España"}</span>
                    <span className="alerta-fila__separador">·</span>
                    <span>{ETIQUETA_SEVERIDAD[a.severity] || a.severity}</span>
                  </div>
                </div>
                <div className="alerta-fila__acciones">
                  {esAdmin && (
                    <>
                      <button
                        type="button"
                        className="alerta-fila__uuid"
                        title="Copiar UUID"
                        aria-label={`Copiar UUID de la alerta ${a.id}`}
                        onClick={(e) => copiarUuid(e, a.id)}
                      >
                        {a.id.slice(0, 8)}…
                      </button>
                      <button
                        type="button"
                        className="alerta-fila__eliminar"
                        title="Eliminar alerta"
                        onClick={(e) => eliminarAlerta(e, a.id)}
                      >
                        Eliminar
                      </button>
                    </>
                  )}
                  {usuario && (
                    <button
                      className={`alerta-fila__fav ${favoritosIds.has(a.id) ? "alerta-fila__fav--activo" : ""}`}
                      onClick={(e) => toggleFavorito(e, a.id)}
                      title={favoritosIds.has(a.id) ? "Quitar de favoritos" : "Añadir a favoritos"}
                      aria-label={favoritosIds.has(a.id) ? "Quitar de favoritos" : "Añadir a favoritos"}
                      aria-pressed={favoritosIds.has(a.id)}
                    >
                      <Star size={18} fill={favoritosIds.has(a.id) ? "currentColor" : "none"} />
                    </button>
                  )}
                  <time className="alerta-fila__fecha">{formatearFecha(a.effective_at || a.created_at)}</time>
                </div>
              </div>

              {alertaAbierta === a.id && (
                <div className="alerta-fila__detalle">
                  {a.description && <p className="alerta-fila__descripcion">{a.description}</p>}
                  <div className="alerta-fila__info">
                    {a.expires_at && (
                      <span>Expira: {formatearFecha(a.expires_at)}</span>
                    )}
                    <span>Fuente: {NOMBRE_FUENTE[a.source]}</span>
                  </div>
                </div>
              )}
            </article>
          ))}
        </div>
      )}

      {totalPaginas > 1 && (
        <div className="alertas-page__paginacion">
          <button
            disabled={pagina === 0}
            onClick={() => setPagina(pagina - 1)}
          >
            Anterior
          </button>
          <span className="alertas-page__pagina">
            {pagina + 1} / {totalPaginas}
          </span>
          <button
            disabled={pagina >= totalPaginas - 1}
            onClick={() => setPagina(pagina + 1)}
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
}
