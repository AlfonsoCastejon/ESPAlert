import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import PerfilPage from "@/app/perfil/page";

const mockPush = vi.fn();
const mockLogout = vi.fn();
const mockUseAuth = vi.fn();
const mockFetch = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
  mockUseAuth.mockReturnValue({
    usuario: { id: "u1", email: "user@test.com", role: "user" },
    cargando: false,
    logout: mockLogout,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  mockPush.mockReset();
  mockLogout.mockReset();
  mockFetch.mockReset();
});

describe("PerfilPage", () => {
  it("redirige a /login si no hay usuario", async () => {
    mockUseAuth.mockReturnValue({ usuario: null, cargando: false, logout: mockLogout });

    render(<PerfilPage />);

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/login"));
  });

  it("muestra email y pestañas al cargar", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    });

    render(<PerfilPage />);

    expect(screen.getByText("user@test.com")).toBeInTheDocument();
    expect(screen.getByText("Usuario")).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByText("No tienes alertas favoritas.")).toBeInTheDocument(),
    );
  });

  it("muestra la lista de favoritos", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total: 1,
          items: [
            {
              id: "a1",
              headline: "Alerta favorita",
              severity: "moderate",
              color: "yellow",
              area_description: "Madrid",
              effective_at: "2026-04-10T00:00:00Z",
            },
          ],
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ region: null, filters: null, theme: null }),
      });

    render(<PerfilPage />);

    await waitFor(() =>
      expect(screen.getByText("Alerta favorita")).toBeInTheDocument(),
    );
    expect(screen.getByText(/Madrid/)).toBeInTheDocument();
  });

  it("cambia a la pestaña de preferencias y guarda", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total: 0, items: [] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ region: null, filters: null, theme: null }),
      });

    render(<PerfilPage />);

    await waitFor(() => screen.getByText("Zona de alertas"));
    fireEvent.click(screen.getByText("Zona de alertas"));

    expect(screen.getByText("Región de interés")).toBeInTheDocument();

    mockFetch.mockResolvedValueOnce({ ok: true });
    fireEvent.click(screen.getByText("Guardar preferencias"));

    await waitFor(() =>
      expect(screen.getByText("Preferencias guardadas")).toBeInTheDocument(),
    );
  });

  it("cambia a notificaciones y cierra sesión", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    });

    render(<PerfilPage />);

    await waitFor(() => screen.getByText("Notificaciones"));
    fireEvent.click(screen.getByText("Notificaciones"));

    expect(screen.getByRole("heading", { name: "Cerrar sesión" })).toBeInTheDocument();

    mockLogout.mockResolvedValueOnce(undefined);
    fireEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    await waitFor(() => expect(mockLogout).toHaveBeenCalled());
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });
});
