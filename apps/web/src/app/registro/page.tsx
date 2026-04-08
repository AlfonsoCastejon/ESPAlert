"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegistroPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmar, setConfirmar] = useState("");
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmar) {
      setError("Las contraseñas no coinciden");
      return;
    }

    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    setCargando(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        setError(data?.detail || "Error al crear la cuenta");
        return;
      }

      router.push("/");
    } catch {
      setError("Error de conexión con el servidor");
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
        </label>

        <button className="auth__boton" type="submit" disabled={cargando}>
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
