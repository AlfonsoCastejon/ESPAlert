"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
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
  });
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [error, setError] = useState("");

  // Estado de la suscripción push.
  const [pushActivo, setPushActivo] = useState(false);
  const [pushProcesando, setPushProcesando] = useState(false);
  const [pushSoportado, setPushSoportado] = useState(true);

  useEffect(() => {
    if (!cargando && !usuario) {
      router.push("/login");
    }
  }, [cargando, usuario, router]);

  // Detecta al cargar si el navegador ya tiene una suscripción push activa.
  useEffect(() => {
    async function comprobar() {
      if (typeof window === "undefined") return;
      if (!("serviceWorker" in navigator) || !("PushManager" in window)) {
        setPushSoportado(false);
        return;
      }
      try {
        const reg = await navigator.serviceWorker.getRegistration();
        if (!reg) return;
        const sub = await reg.pushManager.getSubscription();
        setPushActivo(sub !== null);
      } catch { /* silenciar */ }
    }
    if (usuario) comprobar();
  }, [usuario]);

  function urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
    const raw = atob(base64);
    const arr = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  async function activarNotificaciones() {
    setPushProcesando(true);
    setError("");
    setMensaje("");
    try {
      if (!("Notification" in window)) {
        setError("Tu navegador no soporta notificaciones.");
        return;
      }
      const perm = await Notification.requestPermission();
      if (perm !== "granted") {
        setError("Permiso de notificaciones denegado.");
        return;
      }

      const reg = await navigator.serviceWorker.register("/sw.js");
      await navigator.serviceWorker.ready;

      const res = await fetch(`${API_URL}/api/push/vapid-key`);
      if (!res.ok) throw new Error();
      const { public_key } = await res.json();

      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(public_key) as BufferSource,
      });

      const raw = sub.toJSON();
      const guardar = await fetch(`${API_URL}/api/push/subscribe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          endpoint: sub.endpoint,
          p256dh: raw.keys?.p256dh,
          auth: raw.keys?.auth,
        }),
      });
      if (!guardar.ok) throw new Error();

      setPushActivo(true);
      setMensaje("Notificaciones activadas");
    } catch (err) {
      console.error("Error al activar notificaciones:", err);
      setError("No se pudo activar las notificaciones.");
    } finally {
      setPushProcesando(false);
    }
  }

  async function desactivarNotificaciones() {
    setPushProcesando(true);
    setError("");
    setMensaje("");
    try {
      const reg = await navigator.serviceWorker.getRegistration();
      const sub = await reg?.pushManager.getSubscription();
      if (!sub) {
        setPushActivo(false);
        setMensaje("No había suscripción activa");
        return;
      }
      const endpoint = sub.endpoint;
      await sub.unsubscribe();
      await fetch(`${API_URL}/api/push/subscribe`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ endpoint }),
      });
      setPushActivo(false);
      setMensaje("Notificaciones desactivadas");
    } catch {
      setError("No se pudo desactivar las notificaciones.");
    } finally {
      setPushProcesando(false);
    }
  }

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
                    aria-label="Quitar de favoritos"
                  >
                    <X size={16} aria-hidden="true" />
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
              {(["extreme", "severe"] as const).map((sev) => (
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
            {!pushSoportado ? (
              <p className="perfil__error">Tu navegador no soporta notificaciones push.</p>
            ) : pushActivo ? (
              <button
                className="perfil__btn-danger"
                onClick={desactivarNotificaciones}
                disabled={pushProcesando}
              >
                {pushProcesando ? "Procesando..." : "Desactivar notificaciones"}
              </button>
            ) : (
              <button
                className="perfil__btn-guardar"
                onClick={activarNotificaciones}
                disabled={pushProcesando}
              >
                {pushProcesando ? "Procesando..." : "Activar notificaciones"}
              </button>
            )}
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
