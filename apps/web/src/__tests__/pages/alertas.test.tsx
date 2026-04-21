import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import AlertasPage from "@/app/alertas/page";

const mockUseAuth = vi.fn();

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => mockUseAuth(),
}));

const mockFetch = vi.fn();

beforeEach(() => {
  mockUseAuth.mockReturnValue({ usuario: null, cargando: false });
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
  mockUseAuth.mockReset();
  mockFetch.mockReset();
});

describe("AlertasPage", () => {
  it("muestra estado de carga inicialmente", () => {
    mockFetch.mockReturnValueOnce(new Promise(() => {})); // nunca resuelve
    render(<AlertasPage />);
    expect(screen.getByText("Cargando alertas...")).toBeInTheDocument();
  });

  it("muestra alertas tras carga exitosa", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total: 1,
        items: [
          {
            id: "abc-123",
            headline: "Alerta de prueba",
            source: "aemet",
            severity: "moderate",
            color: "yellow",
            status: "active",
            alert_type: "meteorological",
            onset: "2026-04-14T00:00:00Z",
            expires: "2026-04-15T00:00:00Z",
            area_description: "Madrid",
          },
        ],
      }),
    });

    render(<AlertasPage />);

    await waitFor(() =>
      expect(screen.getByText("Alerta de prueba")).toBeInTheDocument(),
    );
  });

  it("muestra mensaje si no hay alertas", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    });

    render(<AlertasPage />);

    await waitFor(() =>
      expect(
        screen.getByText("No se han encontrado alertas con estos filtros."),
      ).toBeInTheDocument(),
    );
  });

  it("muestra error si falla la peticion", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<AlertasPage />);

    await waitFor(() =>
      expect(
        screen.getByText("No se pudieron cargar las alertas. Comprueba la conexión."),
      ).toBeInTheDocument(),
    );
  });

  it("renderiza los filtros de fuente y severidad", () => {
    mockFetch.mockReturnValueOnce(new Promise(() => {}));
    render(<AlertasPage />);
    expect(screen.getByDisplayValue("Todas las fuentes")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Todas")).toBeInTheDocument();
  });

  it("muestra UUID y botón eliminar en cada fila si el usuario es admin", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "admin-1", email: "admin@test.com", role: "admin" },
      cargando: false,
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total: 1,
        items: [
          {
            id: "abcdef12-3456-7890-abcd-ef1234567890",
            headline: "Alerta admin",
            source: "aemet",
            severity: "moderate",
            color: "yellow",
            status: "active",
            alert_type: "meteorological",
            onset: "2026-04-14T00:00:00Z",
            expires: "2026-04-15T00:00:00Z",
            area_description: "Madrid",
          },
        ],
      }),
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ items: [] }),
    });

    render(<AlertasPage />);

    await waitFor(() =>
      expect(screen.getByText("Alerta admin")).toBeInTheDocument(),
    );
    expect(screen.getByTitle("Copiar UUID")).toBeInTheDocument();
    expect(screen.getByText("Eliminar")).toBeInTheDocument();
    expect(screen.getByText(/abcdef12…/)).toBeInTheDocument();
  });
});
