import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import AlertasPage from "@/app/alertas/page";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
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
});
