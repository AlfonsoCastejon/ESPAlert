"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { REGIONES } from "@/types/filters";
import type { Alerta } from "@/types/alert";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const COLOR_CSS: Record<string, string> = {
  red: "rojo", orange: "naranja", yellow: "amarillo",
  green: "verde", purple: "morado",
};

const ETIQUETA_SEVERIDAD: Record<string, string> = {
  extreme: "Extrema", severe: "Severa", moderate: "Moderada",
  minor: "Menor", unknown: "Desconocida",
};

type Seccion = "favoritos" | "preferencias" | "notificaciones";

export default function PerfilPage() {
  const router = useRouter();
  const { usuario, cargando, logout } = useAuth();
  const [seccion, setSeccion] = useState<Seccion>("favoritos");

  const [favoritos, setFavoritos] = useState<Alerta[]>([]);
  const [totalFav, setTotalFav] = useState(0);
  const [cargandoFav, setCargandoFav] = useState(true);

  const [region, setRegion] = useState("");
  const [notifSeveridades, setNotifSeveridades] = useState({
    extreme: true,
    severe: true,
    moderate: true,
    minor: false,
  });
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!cargando && !usuario) {
      router.push("/login");
    }
  }, [cargando, usuario, router]);

  const cargarFavoritos = useCallback(async () => {
    setCargandoFav(true);
    try {
      const res = await fetch(`${API_URL}/api/user/favorites?limit=50`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setFavoritos(data.items || []);
      setTotalFav(data.total || 0);
    } catch {
      setFavoritos([]);
    } finally {
      setCargandoFav(false);
    }
  }, []);

  const cargarPreferencias = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/user/preferences`, {
        credentials: "include",
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data.region) setRegion(data.region);
      if (data.filters?.severidades) setNotifSeveridades(data.filters.severidades);
    } catch { /* silenciar */ }
  }, []);

  useEffect(() => {
    if (usuario) {
      cargarFavoritos();
      cargarPreferencias();
    }
  }, [usuario, cargarFavoritos, cargarPreferencias]);

  async function quitarFavorito(alertId: string) {
    try {
      const res = await fetch(`${API_URL}/api/user/favorites/${alertId}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        setFavoritos((prev) => prev.filter((a) => a.id !== alertId));
        setTotalFav((prev) => prev - 1);
      }
    } catch { /* silenciar */ }
  }

  async function guardarPreferencias() {
    setGuardando(true);
    setMensaje("");
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/user/preferences`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          region: region || null,
          filters: { severidades: notifSeveridades },
        }),
      });
      if (!res.ok) throw new Error();
      setMensaje("Preferencias guardadas");
    } catch {
      setError("Error al guardar preferencias.");
    } finally {
      setGuardando(false);
    }
  }

  function formatearFecha(iso: string | null): string {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("es-ES", {
      day: "2-digit", month: "short", year: "numeric",
    });
  }

  if (cargando || !usuario) {
    return <div className="perfil"><p className="perfil__estado">Cargando...</p></div>;
  }

  return (
    <div className="perfil">
      <div className="perfil__cabecera">
        <h1 className="perfil__titulo">Mi perfil</h1>
        <div className="perfil__info">
          <span className="perfil__email">{usuario.email}</span>
          <span className="perfil__role">
            {usuario.role === "admin" ? "Administrador" : "Usuario"}
          </span>
        </div>
      </div>

      <div className="perfil__tabs">
        <button
          className={`perfil__tab ${seccion === "favoritos" ? "perfil__tab--activo" : ""}`}
          onClick={() => setSeccion("favoritos")}
        >
          Favoritos ({totalFav})
        </button>
        <button
          className={`perfil__tab ${seccion === "preferencias" ? "perfil__tab--activo" : ""}`}
          onClick={() => setSeccion("preferencias")}
        >
          Zona de alertas
        </button>
        <button
          className={`perfil__tab ${seccion === "notificaciones" ? "perfil__tab--activo" : ""}`}
          onClick={() => setSeccion("notificaciones")}
        >
          Notificaciones
        </button>
      </div>

      {error && <p className="perfil__error">{error}</p>}
      {mensaje && <p className="perfil__exito">{mensaje}</p>}

      {seccion === "favoritos" && (
        <div className="perfil__seccion">
          {cargandoFav ? (
            <p className="perfil__estado">Cargando favoritos...</p>
          ) : favoritos.length === 0 ? (
            <div className="perfil__vacio">
              <p>No tienes alertas favoritas.</p>
              <p className="perfil__vacio-hint">
                Marca alertas con el icono de favorito en la página de alertas.
              </p>
            </div>
          ) : (
            <div className="perfil__lista-fav">
              {favoritos.map((a) => (
                <div key={a.id} className={`perfil__fav-item perfil__fav-item--${COLOR_CSS[a.color] || "verde"}`}>
                  <div className="perfil__fav-contenido">
                    <span className={`perfil__fav-indicador perfil__fav-indicador--${COLOR_CSS[a.color] || "verde"}`} />
                    <div>
                      <h4 className="perfil__fav-titulo">{a.headline}</h4>
                      <p className="perfil__fav-meta">
                        {ETIQUETA_SEVERIDAD[a.severity] || a.severity}
                        {a.area_description && ` · ${a.area_description}`}
                        {a.effective_at && ` · ${formatearFecha(a.effective_at)}`}
                      </p>
                    </div>
                  </div>
                  <button
                    className="perfil__fav-quitar"
                    onClick={() => quitarFavorito(a.id)}
                    title="Quitar de favoritos"
                  >
                    &#x2715;
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {seccion === "preferencias" && (
        <div className="perfil__seccion">
          <div className="perfil__bloque">
            <h3 className="perfil__bloque-titulo">Región de interés</h3>
            <p className="perfil__bloque-desc">
              Selecciona tu comunidad autónoma para recibir alertas relevantes.
            </p>
            <select
              className="perfil__select"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
            >
              {REGIONES.map((r) => (
                <option key={r.valor} value={r.valor}>{r.etiqueta}</option>
              ))}
            </select>
          </div>

          <div className="perfil__bloque">
            <h3 className="perfil__bloque-titulo">Severidades a recibir</h3>
            <p className="perfil__bloque-desc">
              Elige qué niveles de alerta quieres que te notifiquemos.
            </p>
            <div className="perfil__checks">
              {(["extreme", "severe", "moderate", "minor"] as const).map((sev) => (
                <label key={sev} className="perfil__check-label">
                  <input
                    type="checkbox"
                    checked={notifSeveridades[sev]}
                    onChange={(e) =>
                      setNotifSeveridades((prev) => ({ ...prev, [sev]: e.target.checked }))
                    }
                  />
                  {ETIQUETA_SEVERIDAD[sev]}
                </label>
              ))}
            </div>
          </div>

          <button
            className="perfil__btn-guardar"
            onClick={guardarPreferencias}
            disabled={guardando}
          >
            {guardando ? "Guardando..." : "Guardar preferencias"}
          </button>
        </div>
      )}

      {seccion === "notificaciones" && (
        <div className="perfil__seccion">
          <div className="perfil__bloque">
            <h3 className="perfil__bloque-titulo">Notificaciones push</h3>
            <p className="perfil__bloque-desc">
              Recibe notificaciones en tu navegador cuando haya alertas en tu zona.
            </p>
            <button
              className="perfil__btn-guardar"
              onClick={async () => {
                if (!("Notification" in window)) {
                  setError("Tu navegador no soporta notificaciones.");
                  return;
                }
                const perm = await Notification.requestPermission();
                if (perm === "granted") {
                  setMensaje("Notificaciones activadas");
                } else {
                  setError("Permiso de notificaciones denegado.");
                }
              }}
            >
              Activar notificaciones
            </button>
          </div>

          <div className="perfil__bloque">
            <h3 className="perfil__bloque-titulo">Mi cuenta</h3>
            <p className="perfil__bloque-desc">
              Datos de la cuenta y cambio de contraseña.
            </p>
            <Link href="/perfil/cuenta" className="perfil__enlace">
              Ir a mi cuenta
            </Link>
          </div>

          <div className="perfil__bloque">
            <h3 className="perfil__bloque-titulo">Cerrar sesión</h3>
            <p className="perfil__bloque-desc">
              Cierra tu sesión en este dispositivo.
            </p>
            <button
              className="perfil__btn-danger"
              onClick={async () => {
                await logout();
                router.push("/");
              }}
            >
              Cerrar sesión
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
