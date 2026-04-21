"use client";

/**
 * Página de cuenta del usuario: datos básicos y cambio de contraseña.
 */

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Check, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CuentaPage() {
  const router = useRouter();
  const { usuario, cargando } = useAuth();

  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [repetir, setRepetir] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState("");

  // Requisitos evaluados en tiempo real sobre la nueva contraseña
  const requisitos = {
    longitud: nueva.length >= 8,
    mayuscula: /[A-Z]/.test(nueva),
    minuscula: /[a-z]/.test(nueva),
    numero: /\d/.test(nueva),
  };
  const coinciden = repetir.length > 0 && nueva === repetir;
  const todoOk =
    Object.values(requisitos).every(Boolean) && coinciden && actual.length > 0;

  useEffect(() => {
    if (!cargando && !usuario) {
      router.push("/login");
    }
  }, [cargando, usuario, router]);

  async function cambiarContrasena(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setExito("");

    if (nueva !== repetir) {
      setError("Las contraseñas nuevas no coinciden.");
      return;
    }

    setGuardando(true);
    try {
      const res = await fetch(`${API_URL}/api/auth/password`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: actual,
          new_password: nueva,
        }),
      });
      if (res.status === 204) {
        setExito("Contraseña actualizada correctamente.");
        setActual("");
        setNueva("");
        setRepetir("");
      } else if (res.status === 401) {
        setError("La contraseña actual es incorrecta.");
      } else if (res.status === 422) {
        setError("La nueva contraseña no cumple los requisitos (8+ caracteres, mayúscula, minúscula y número).");
      } else {
        setError("Error al cambiar la contraseña.");
      }
    } catch {
      setError("Error de conexión con el servidor.");
    } finally {
      setGuardando(false);
    }
  }

  if (cargando || !usuario) {
    return <div className="perfil"><p className="perfil__estado">Cargando...</p></div>;
  }

  return (
    <div className="perfil">
      <div className="perfil__cabecera">
        <h1 className="perfil__titulo">Mi cuenta</h1>
        <div className="perfil__info">
          <span className="perfil__email">{usuario.email}</span>
          <span className="perfil__role">
            {usuario.role === "admin" ? "Administrador" : "Usuario"}
          </span>
        </div>
      </div>

      <div className="perfil__seccion">
        <div className="perfil__bloque">
          <h3 className="perfil__bloque-titulo">Datos de la cuenta</h3>
          <dl className="perfil__datos">
            <dt>Correo electrónico</dt>
            <dd>{usuario.email}</dd>
            <dt>Rol</dt>
            <dd>{usuario.role === "admin" ? "Administrador" : "Usuario"}</dd>
            <dt>Identificador</dt>
            <dd><code>{usuario.id}</code></dd>
          </dl>
        </div>

        <div className="perfil__bloque">
          <h3 className="perfil__bloque-titulo">Cambiar contraseña</h3>

          {error && <p className="perfil__error">{error}</p>}
          {exito && <p className="perfil__exito">{exito}</p>}

          <form onSubmit={cambiarContrasena} className="perfil__form">
            <label className="perfil__label">
              Contraseña actual
              <input
                type="password"
                className="perfil__input"
                value={actual}
                onChange={(e) => setActual(e.target.value)}
                required
              />
            </label>
            <label className="perfil__label">
              Nueva contraseña
              <input
                type="password"
                className="perfil__input"
                value={nueva}
                onChange={(e) => setNueva(e.target.value)}
                required
              />
            </label>

            <ul className="perfil__requisitos">
              <li className={requisitos.longitud ? "perfil__requisito--ok" : "perfil__requisito--pendiente"}>
                {requisitos.longitud ? <Check size={14} /> : <X size={14} />} Al menos 8 caracteres
              </li>
              <li className={requisitos.mayuscula ? "perfil__requisito--ok" : "perfil__requisito--pendiente"}>
                {requisitos.mayuscula ? <Check size={14} /> : <X size={14} />} Una letra mayúscula
              </li>
              <li className={requisitos.minuscula ? "perfil__requisito--ok" : "perfil__requisito--pendiente"}>
                {requisitos.minuscula ? <Check size={14} /> : <X size={14} />} Una letra minúscula
              </li>
              <li className={requisitos.numero ? "perfil__requisito--ok" : "perfil__requisito--pendiente"}>
                {requisitos.numero ? <Check size={14} /> : <X size={14} />} Un número
              </li>
            </ul>

            <label className="perfil__label">
              Repetir nueva contraseña
              <input
                type="password"
                className="perfil__input"
                value={repetir}
                onChange={(e) => setRepetir(e.target.value)}
                required
              />
            </label>
            {repetir.length > 0 && (
              <p className={coinciden ? "perfil__requisito--ok" : "perfil__requisito--pendiente"}>
                {coinciden ? <Check size={14} /> : <X size={14} />} {coinciden ? "Las contraseñas coinciden" : "Las contraseñas no coinciden"}
              </p>
            )}

            <button
              type="submit"
              className="perfil__btn-guardar"
              disabled={guardando || !todoOk}
            >
              {guardando ? "Guardando..." : "Cambiar contraseña"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
