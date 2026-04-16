"use client";

/** Formulario de registro: email, contraseña y confirmación. */

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function RegistroPage() {
  const router = useRouter();
  const { registro } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const tieneMinLength = password.length >= 8;
  const tieneMayuscula = /[A-Z]/.test(password);
  const tieneMinuscula = /[a-z]/.test(password);
  const tieneNumero = /\d/.test(password);
  const passwordValida = tieneMinLength && tieneMayuscula && tieneMinuscula && tieneNumero;
  const noCoinciden = confirmar.length > 0 && password !== confirmar;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (!passwordValida) return;
    if (password !== confirmar) {
      setError("Las contraseñas no coinciden");
      return;
    }

    setCargando(true);

    try {
      const err = await registro(email, password);
      if (err) {
        setError(err);
      } else {
        router.push("/");
      }
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="pagina-auth">
      <form className="auth" onSubmit={handleSubmit}>
        <h1 className="auth__titulo">Crear cuenta</h1>
        <p className="auth__subtitulo">
          Regístrate para recibir alertas personalizadas
        </p>

        {error && <p className="auth__error">{error}</p>}

        <label className="auth__campo">
          <span className="auth__etiqueta">Correo electrónico</span>
          <input
            className="auth__input"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="tu@email.com"
            required
            autoComplete="email"
          />
        </label>

        <label className="auth__campo">
          <span className="auth__etiqueta">Contraseña</span>
          <input
            className="auth__input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Mínimo 8 caracteres"
            required
            autoComplete="new-password"
          />
          {password.length > 0 && (
            <ul className="auth__requisitos">
              <li className={tieneMinLength ? "auth__requisito--ok" : "auth__requisito--pendiente"}>
                Mínimo 8 caracteres
              </li>
              <li className={tieneMayuscula ? "auth__requisito--ok" : "auth__requisito--pendiente"}>
                Una letra mayúscula
              </li>
              <li className={tieneMinuscula ? "auth__requisito--ok" : "auth__requisito--pendiente"}>
                Una letra minúscula
              </li>
              <li className={tieneNumero ? "auth__requisito--ok" : "auth__requisito--pendiente"}>
                Un número
              </li>
            </ul>
          )}
        </label>

        <label className="auth__campo">
          <span className="auth__etiqueta">Confirmar contraseña</span>
          <input
            className="auth__input"
            type="password"
            value={confirmar}
            onChange={(e) => setConfirmar(e.target.value)}
            placeholder="Repite la contraseña"
            required
            autoComplete="new-password"
          />
          {noCoinciden && (
            <span className="auth__requisito--pendiente">Las contraseñas no coinciden</span>
          )}
        </label>

        <button className="auth__boton" type="submit" disabled={cargando || !passwordValida || noCoinciden}>
          {cargando ? "Creando cuenta..." : "Registrarse"}
        </button>

        <p className="auth__enlace">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login">Inicia sesión</Link>
        </p>
      </form>
    </div>
  );
}
