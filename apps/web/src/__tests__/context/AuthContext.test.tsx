import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/context/AuthContext";

// Componente auxiliar para acceder al contexto en tests
function ConsumidorAuth() {
  const { usuario, cargando } = useAuth();
  if (cargando) return <p>cargando</p>;
  if (usuario) return <p>{usuario.email} - {usuario.role}</p>;
  return <p>sin sesion</p>;
}

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AuthContext", () => {
  it("muestra cargando inicialmente y luego sin sesion si /me falla", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    render(
      <AuthProvider>
        <ConsumidorAuth />
      </AuthProvider>,
    );

    expect(screen.getByText("cargando")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText("sin sesion")).toBeInTheDocument());
  });

  it("carga el usuario si /me devuelve datos", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "1", email: "admin@espalert.es", role: "admin" }),
    });

    render(
      <AuthProvider>
        <ConsumidorAuth />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText("admin@espalert.es - admin")).toBeInTheDocument(),
    );
  });

  it("gestiona error de red en /me sin romper", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(
      <AuthProvider>
        <ConsumidorAuth />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("sin sesion")).toBeInTheDocument());
  });
});

describe("AuthContext login", () => {
  it("actualiza el usuario tras login exitoso", async () => {
    // Primera llamada: /me falla (no logueado)
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    let loginFn: (email: string, password: string) => Promise<string | null>;

    function ConsumidorLogin() {
      const { usuario, cargando, login } = useAuth();
      loginFn = login;
      if (cargando) return <p>cargando</p>;
      if (usuario) return <p>{usuario.email}</p>;
      return <p>sin sesion</p>;
    }

    render(
      <AuthProvider>
        <ConsumidorLogin />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("sin sesion")).toBeInTheDocument());

    // Login exitoso
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ id: "2", email: "user@test.com", role: "user" }),
    });

    await act(async () => {
      const err = await loginFn!("user@test.com", "pass1234");
      expect(err).toBeNull();
    });

    expect(screen.getByText("user@test.com")).toBeInTheDocument();
  });

  it("devuelve error si las credenciales son invalidas", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 });

    let loginFn: (email: string, password: string) => Promise<string | null>;

    function ConsumidorLogin() {
      const { cargando, login } = useAuth();
      loginFn = login;
      if (cargando) return <p>cargando</p>;
      return <p>listo</p>;
    }

    render(
      <AuthProvider>
        <ConsumidorLogin />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByText("listo")).toBeInTheDocument());

    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Credenciales inválidas" }),
    });

    let resultado: string | null;
    await act(async () => {
      resultado = await loginFn!("bad@test.com", "wrong");
    });

    expect(resultado!).toBe("Credenciales inválidas");
  });
});
