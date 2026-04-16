"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UsuarioAdmin {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

type Seccion = "usuarios" | "alertas";

export default function AdminPage() {
  const router = useRouter();
  const { usuario, cargando } = useAuth();
  const [seccion, setSeccion] = useState<Seccion>("usuarios");
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([]);
  const [totalUsuarios, setTotalUsuarios] = useState(0);
  const [cargandoDatos, setCargandoDatos] = useState(true);
  const [error, setError] = useState("");
  const [alertaIdEliminar, setAlertaIdEliminar] = useState("");
  const [mensajeExito, setMensajeExito] = useState("");

  useEffect(() => {
    if (!cargando && (!usuario || usuario.role !== "admin")) {
      router.push("/");
    }
  }, [cargando, usuario, router]);

  const cargarUsuarios = useCallback(async () => {
    setCargandoDatos(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/api/admin/users?limit=100`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setUsuarios(data.items || []);
      setTotalUsuarios(data.total || 0);
    } catch {
      setError("No se pudieron cargar los usuarios.");
    } finally {
      setCargandoDatos(false);
    }
  }, []);

  useEffect(() => {
    if (usuario?.role === "admin") {
      cargarUsuarios();
    }
  }, [usuario, cargarUsuarios]);

  async function cambiarRol(userId: string, nuevoRol: string) {
    setError("");
    setMensajeExito("");
    try {
      const res = await fetch(`${API_URL}/api/admin/users/${userId}/role?role=${nuevoRol}`, {
        method: "PATCH",
        credentials: "include",
      });
      if (!res.ok) throw new Error();
      setMensajeExito("Rol actualizado");
      cargarUsuarios();
    } catch {
      setError("Error al cambiar el rol.");
    }
  }

  async function eliminarAlerta() {
    if (!alertaIdEliminar.trim()) return;
    setError("");
    setMensajeExito("");
    try {
      const res = await fetch(`${API_URL}/api/admin/alerts/${alertaIdEliminar.trim()}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        setMensajeExito("Alerta eliminada");
        setAlertaIdEliminar("");
      } else if (res.status === 404) {
        setError("Alerta no encontrada.");
      } else {
        throw new Error();
      }
    } catch {
      setError("Error al eliminar la alerta.");
    }
  }

  async function eliminarTodosMesh() {
    setError("");
    setMensajeExito("");
    try {
      const res = await fetch(`${API_URL}/api/admin/mesh`, {
        method: "DELETE",
        credentials: "include",
      });
      if (res.status === 204) {
        setMensajeExito("Mensajes mesh eliminados");
      } else {
        throw new Error();
      }
    } catch {
      setError("Error al eliminar mensajes mesh.");
    }
  }

  function formatearFecha(iso: string): string {
    return new Date(iso).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  if (cargando || !usuario || usuario.role !== "admin") {
    return <div className="admin"><p className="admin__estado">Cargando...</p></div>;
  }

  return (
    <div className="admin">
      <div className="admin__cabecera">
        <h1 className="admin__titulo">Panel de administración</h1>
        <p className="admin__subtitulo">{totalUsuarios} usuarios registrados</p>
      </div>

      <div className="admin__tabs">
        <button
          className={`admin__tab ${seccion === "usuarios" ? "admin__tab--activo" : ""}`}
          onClick={() => setSeccion("usuarios")}
        >
          Usuarios
        </button>
        <button
          className={`admin__tab ${seccion === "alertas" ? "admin__tab--activo" : ""}`}
          onClick={() => setSeccion("alertas")}
        >
          Gestión de alertas
        </button>
      </div>

      {error && <p className="admin__error">{error}</p>}
      {mensajeExito && <p className="admin__exito">{mensajeExito}</p>}

      {seccion === "usuarios" && (
        <div className="admin__seccion">
          {cargandoDatos ? (
            <p className="admin__estado">Cargando usuarios...</p>
          ) : (
            <div className="admin__tabla-contenedor">
              <table className="admin__tabla">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Rol</th>
                    <th>Estado</th>
                    <th>Registro</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((u) => (
                    <tr key={u.id}>
                      <td>{u.email}</td>
                      <td>
                        <span className={`admin__badge admin__badge--${u.role}`}>
                          {u.role === "admin" ? "Admin" : "Usuario"}
                        </span>
                      </td>
                      <td>{u.is_active ? "Activo" : "Inactivo"}</td>
                      <td>{formatearFecha(u.created_at)}</td>
                      <td>
                        {u.id !== usuario.id && (
                          <button
                            className="admin__btn-accion"
                            onClick={() => cambiarRol(u.id, u.role === "admin" ? "user" : "admin")}
                          >
                            {u.role === "admin" ? "Quitar admin" : "Hacer admin"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {seccion === "alertas" && (
        <div className="admin__seccion">
          <div className="admin__bloque">
            <h3 className="admin__bloque-titulo">Eliminar alerta por ID</h3>
            <div className="admin__fila-input">
              <input
                className="admin__input"
                type="text"
                value={alertaIdEliminar}
                onChange={(e) => setAlertaIdEliminar(e.target.value)}
                placeholder="UUID de la alerta"
              />
              <button className="admin__btn-danger" onClick={eliminarAlerta}>
                Eliminar
              </button>
            </div>
          </div>

          <div className="admin__bloque">
            <h3 className="admin__bloque-titulo">Mensajes Meshtastic</h3>
            <p className="admin__bloque-desc">
              Eliminar todos los mensajes recibidos de la red mesh.
            </p>
            <button className="admin__btn-danger" onClick={eliminarTodosMesh}>
              Eliminar todos los mensajes mesh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
