"use client";

/** Formulario de inicio de sesión con email y contraseña. */

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCargando(true);

    try {
      const err = await login(email, password);
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
        <h1 className="auth__titulo">Iniciar sesión</h1>
        <p className="auth__subtitulo">
          Accede a tu cuenta de ESPAlert
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
            placeholder="Tu contraseña"
            required
            autoComplete="current-password"
          />
        </label>

        <button className="auth__boton" type="submit" disabled={cargando}>
          {cargando ? "Entrando..." : "Iniciar sesión"}
        </button>

        <p className="auth__enlace">
          ¿No tienes cuenta?{" "}
          <Link href="/registro">Regístrate</Link>
        </p>
      </form>
    </div>
  );
}
