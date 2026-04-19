import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AdminMeshPage from "@/app/admin/mesh/page";

const mockPush = vi.fn();
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
});

afterEach(() => {
  vi.restoreAllMocks();
  mockPush.mockReset();
  mockUseAuth.mockReset();
  mockFetch.mockReset();
});

describe("AdminMeshPage", () => {
  it("redirige al home si no es admin", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "1", email: "user@test.com", role: "user" },
      cargando: false,
    });
    render(<AdminMeshPage />);
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });

  it("muestra los mensajes mesh al cargar como admin", async () => {
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
            id: "m1",
            node_id: "abcd1234",
            channel: "LongFast",
            message: "Hola mundo",
            latitude: 40.4,
            longitude: -3.7,
            snr: 5.0,
            rssi: -90,
            received_at: "2026-04-17T10:00:00Z",
          },
        ],
      }),
    });

    render(<AdminMeshPage />);

    await waitFor(() => expect(screen.getByText("abcd1234")).toBeInTheDocument());
    expect(screen.getByText("Hola mundo")).toBeInTheDocument();
    expect(screen.getByText("1 mensajes recibidos")).toBeInTheDocument();
  });

  it("muestra estado vacio si no hay mensajes", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "admin-1", email: "admin@test.com", role: "admin" },
      cargando: false,
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    });

    render(<AdminMeshPage />);

    await waitFor(() =>
      expect(screen.getByText("No hay mensajes mesh almacenados.")).toBeInTheDocument(),
    );
  });

  it("elimina un mensaje al pulsar el boton", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "admin-1", email: "admin@test.com", role: "admin" },
      cargando: false,
    });
    mockFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          total: 1,
          items: [
            {
              id: "m1",
              node_id: "abcd1234",
              channel: null,
              message: "test",
              latitude: null,
              longitude: null,
              snr: null,
              rssi: null,
              received_at: null,
            },
          ],
        }),
      })
      .mockResolvedValueOnce({ status: 204 });

    render(<AdminMeshPage />);
    await waitFor(() => screen.getByText("abcd1234"));

    fireEvent.click(screen.getByText("Eliminar"));

    await waitFor(() =>
      expect(screen.getByText("Mensaje eliminado")).toBeInTheDocument(),
    );
  });
});
