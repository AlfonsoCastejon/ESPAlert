import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import Home from "@/app/page";

// Mock del mapa (maplibre-gl no corre bien en jsdom)
vi.mock("@/components/map/AlertMap", () => ({
  default: ({ alertas }: { alertas: unknown[] }) => (
    <div data-testid="alert-map">{alertas.length} alertas</div>
  ),
}));

vi.mock("@/components/filters/AlertFilters", () => ({
  default: () => <div data-testid="alert-filters">Filtros</div>,
}));

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
  mockFetch.mockReset();
});

describe("Home", () => {
  it("renderiza el mapa y el boton de filtros", async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ items: [] }) });
    render(<Home />);
    await waitFor(() => expect(screen.getByTestId("alert-map")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Filtros" })).toBeInTheDocument();
  });

  it("carga alertas de las 5 fuentes al montar", async () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ items: [] }) });
    render(<Home />);
    await waitFor(() => expect(mockFetch).toHaveBeenCalled());
    const urls = mockFetch.mock.calls.map((c) => String(c[0]));
    expect(urls.some((u) => u.includes("source=aemet"))).toBe(true);
    expect(urls.some((u) => u.includes("source=ign"))).toBe(true);
    expect(urls.some((u) => u.includes("source=dgt"))).toBe(true);
    expect(urls.some((u) => u.includes("source=meteoalarm"))).toBe(true);
    expect(urls.some((u) => u.includes("source=meshtastic"))).toBe(true);
  });

  it("muestra banner de error si falla la carga", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));
    render(<Home />);
    await waitFor(() =>
      expect(screen.getByText("Sin conexión con el servidor")).toBeInTheDocument(),
    );
  });

  it("muestra alertas recibidas (filtradas por tipos activos por defecto)", async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "1",
            alert_type: "meteorological",
            color: "red",
            severity: "extreme",
            headline: "Tormenta",
            effective_at: new Date().toISOString(),
          },
        ],
      }),
    });
    render(<Home />);
    await waitFor(() =>
      expect(screen.getByTestId("alert-map").textContent).toContain("5 alertas"),
    );
  });

  it("abre la bandeja de filtros al pulsar el boton", () => {
    mockFetch.mockResolvedValue({ ok: true, json: async () => ({ items: [] }) });
    render(<Home />);
    fireEvent.click(screen.getByRole("button", { name: "Filtros" }));
    const overlays = document.querySelectorAll(".overlay--bandeja");
    expect(overlays.length).toBeGreaterThan(0);
  });
});
