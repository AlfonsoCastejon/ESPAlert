"use client";

/**
 * Contexto de autenticación.
 * Gestiona sesión del usuario y expone login/logout al resto de la app.
 */

import { createContext, useContext, useState, useEffect, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// FastAPI devuelve detail como string o como array de objetos (422 Pydantic).
// Normalizamos a string para poder renderizarlo en React.
function normalizarDetalle(detail: unknown): string | null {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const primero = detail[0];
    if (typeof primero === "string") return primero;
    if (primero && typeof primero === "object" && "msg" in primero) {
      return String((primero as { msg: unknown }).msg);
    }
  }
  return null;
}

interface Usuario {
  id: string;
  email: string;
  role: "user" | "admin";
}

interface AuthContextValue {
  usuario: Usuario | null;
  cargando: boolean;
  login: (email: string, password: string) => Promise<string | null>;
  registro: (email: string, password: string) => Promise<string | null>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const comprobarSesion = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/auth/me`, { credentials: "include" });
      if (res.ok) {
        const data = await res.json();
        setUsuario({ id: data.id, email: data.email, role: data.role });
      } else {
        setUsuario(null);
      }
    } catch {
      setUsuario(null);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    comprobarSesion();
  }, [comprobarSesion]);

  const login = async (email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setUsuario({ id: data.id, email: data.email, role: data.role });
        return null;
      }
      const err = await res.json().catch(() => null);
      return normalizarDetalle(err?.detail) || "Credenciales inválidas";
    } catch {
      return "Error de conexión con el servidor";
    }
  };

  const registro = async (email: string, password: string): Promise<string | null> => {
    try {
      const res = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setUsuario({ id: data.id, email: data.email, role: data.role });
        return null;
      }
      const err = await res.json().catch(() => null);
      return err?.detail || "Error al crear la cuenta";
    } catch {
      return "Error de conexión con el servidor";
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch {
      /* ignorar */
    }
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, registro, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
