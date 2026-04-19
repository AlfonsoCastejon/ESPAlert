"use client";

/**
 * Página de administración de mensajes Meshtastic.
 * Solo accesible para usuarios con rol admin.
 */

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface MensajeMesh {
  id: string;
  node_id: string;
  channel: string | null;
  message: string;
  latitude: number | null;
  longitude: number | null;
  snr: number | null;
  rssi: number | null;
  received_at: string | null;
}

export default function AdminMeshPage() {
  const router = useRouter();
  const { usuario, cargando } = useAuth();
  const [mensajes, setMensajes] = useState<MensajeMesh[]>([]);
  const [total, setTotal] = useState(0);
  const [cargandoDatos, setCargandoDatos] = useState(true);
  const [error, setError] = useState("");
  const [mensajeExito, setMensajeExito] = useState("");

  useEffect(() => {
    if (!cargando && (!usuario || usuario.role !== "admin")) {
      router.push("/");
    }
  }, [cargando, usuario, router]);

  const cargar = useCallback(async () => {
    setCargandoDatos(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/admin/mesh?limit=100`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMensajes(data.items || []);
      setTotal(data.total || 0);
    } catch {
      setError("No se pudieron cargar los mensajes mesh.");
    } finally {
      setCargandoDatos(false);
    }
  }, []);

  useEffect(() => {
    if (usuario?.role === "admin") cargar();
  }, [usuario, cargar]);

  async function eliminar(id: string) {
    setError("");
    setMensajeExito("");
    try {
      const res = await fetch(`${API_URL}/api/admin/mesh/${id}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        setMensajes((prev) => prev.filter((m) => m.id !== id));
        setTotal((prev) => prev - 1);
        setMensajeExito("Mensaje eliminado");
      } else {
        throw new Error();
      }
    } catch {
      setError("Error al eliminar el mensaje.");
    }
  }

  function formatearFecha(iso: string | null): string {
    if (!iso) return "\u2014";
    return new Date(iso).toLocaleString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  if (cargando || !usuario || usuario.role !== "admin") {
    return <div className="admin"><p className="admin__estado">Cargando...</p></div>;
  }

  return (
    <div className="admin">
      <div className="admin__cabecera">
        <h1 className="admin__titulo">Mensajes Meshtastic</h1>
        <p className="admin__subtitulo">{total} mensajes recibidos</p>
      </div>

      {error && <p className="admin__error">{error}</p>}
      {mensajeExito && <p className="admin__exito">{mensajeExito}</p>}

      {cargandoDatos ? (
        <p className="admin__estado">Cargando mensajes...</p>
      ) : mensajes.length === 0 ? (
        <div className="admin__seccion">
          <p className="admin__estado">No hay mensajes mesh almacenados.</p>
        </div>
      ) : (
        <div className="admin__tabla-contenedor">
          <table className="admin__tabla">
            <thead>
              <tr>
                <th>Nodo</th>
                <th>Canal</th>
                <th>Mensaje</th>
                <th>SNR / RSSI</th>
                <th>Recibido</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {mensajes.map((m) => (
                <tr key={m.id}>
                  <td><code>{m.node_id}</code></td>
                  <td>{m.channel || "\u2014"}</td>
                  <td>{m.message}</td>
                  <td>
                    {m.snr != null ? `${m.snr} dB` : "\u2014"} /{" "}
                    {m.rssi != null ? `${m.rssi} dBm` : "\u2014"}
                  </td>
                  <td>{formatearFecha(m.received_at)}</td>
                  <td>
                    <button
                      className="admin__btn-danger"
                      onClick={() => eliminar(m.id)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
