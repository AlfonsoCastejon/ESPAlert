import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import PrediccionPage from "@/app/prediccion/page";

const mockFetch = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", mockFetch);
});

afterEach(() => {
  vi.restoreAllMocks();
  mockFetch.mockReset();
});

describe("PrediccionPage", () => {
  it("renderiza el buscador con titulo", () => {
    render(<PrediccionPage />);
    expect(screen.getByRole("heading", { name: "Predicción meteorológica" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Escribe un municipio...")).toBeInTheDocument();
  });

  it("no busca si el texto tiene menos de 2 caracteres", async () => {
    render(<PrediccionPage />);
    fireEvent.change(screen.getByPlaceholderText("Escribe un municipio..."), {
      target: { value: "a" },
    });
    await new Promise((r) => setTimeout(r, 400));
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("busca municipios con debounce y muestra sugerencias", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { codigo: "28079", nombre: "Madrid" },
        { codigo: "28080", nombre: "Madridejos" },
      ],
    });

    render(<PrediccionPage />);
    fireEvent.change(screen.getByPlaceholderText("Escribe un municipio..."), {
      target: { value: "Madr" },
    });

    await waitFor(
      () => expect(screen.getByText("Madrid")).toBeInTheDocument(),
      { timeout: 2000 },
    );
    expect(screen.getByText("Madridejos")).toBeInTheDocument();
  });

  it("muestra la prediccion al seleccionar un municipio", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ codigo: "28079", nombre: "Madrid" }],
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          municipio: "Madrid",
          provincia: "Madrid",
          elaborado: "2026-04-17T08:00:00",
          dias: [
            {
              fecha: "2030-04-17",
              temp_max: 22,
              temp_min: 10,
              sens_termica_max: 23,
              sens_termica_min: 9,
              humedad_max: 70,
              humedad_min: 40,
              prob_precipitacion: [{ periodo: "00-12", valor: 10 }],
              cota_nieve: [],
              estado_cielo: [{ periodo: "00-12", valor: "11", descripcion: "Despejado" }],
              viento: [{ periodo: "00-12", direccion: "N", velocidad: 10 }],
              racha_max: 30,
              uv_max: 5,
            },
          ],
        }),
      });

    render(<PrediccionPage />);
    fireEvent.change(screen.getByPlaceholderText("Escribe un municipio..."), {
      target: { value: "Madr" },
    });

    await waitFor(
      () => screen.getByRole("button", { name: "Madrid" }),
      { timeout: 2000 },
    );
    fireEvent.click(screen.getByRole("button", { name: "Madrid" }));

    await waitFor(() =>
      expect(screen.getByRole("heading", { level: 2, name: /Madrid/ })).toBeInTheDocument(),
    );
    expect(screen.getAllByText("Despejado").length).toBeGreaterThan(0);
  });

  it("muestra error si falla la prediccion", async () => {
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [{ codigo: "28079", nombre: "Madrid" }],
      })
      .mockResolvedValueOnce({ ok: false });

    render(<PrediccionPage />);
    fireEvent.change(screen.getByPlaceholderText("Escribe un municipio..."), {
      target: { value: "Madr" },
    });
    await waitFor(
      () => screen.getByRole("button", { name: "Madrid" }),
      { timeout: 2000 },
    );
    fireEvent.click(screen.getByRole("button", { name: "Madrid" }));

    await waitFor(() =>
      expect(
        screen.getByText("No se pudo obtener la predicción para este municipio."),
      ).toBeInTheDocument(),
    );
  });
});
