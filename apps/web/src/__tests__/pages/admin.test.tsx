import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AdminPage from "@/app/admin/page";

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

describe("AdminPage", () => {
  it("redirige al home si el usuario no es admin", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "1", email: "user@test.com", role: "user" },
      cargando: false,
    });

    render(<AdminPage />);

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });

  it("redirige al home si no hay usuario", async () => {
    mockUseAuth.mockReturnValue({ usuario: null, cargando: false });

    render(<AdminPage />);

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });

  it("muestra la tabla de usuarios al cargar como admin", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "admin-1", email: "admin@test.com", role: "admin" },
      cargando: false,
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        total: 2,
        items: [
          {
            id: "admin-1",
            email: "admin@test.com",
            role: "admin",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
          },
          {
            id: "user-2",
            email: "juan@test.com",
            role: "user",
            is_active: true,
            created_at: "2026-02-01T00:00:00Z",
          },
        ],
      }),
    });

    render(<AdminPage />);

    await waitFor(() =>
      expect(screen.getByText("admin@test.com")).toBeInTheDocument(),
    );
    expect(screen.getByText("juan@test.com")).toBeInTheDocument();
    expect(screen.getByText("2 usuarios registrados")).toBeInTheDocument();
  });

  it("cambia a la pestaña de Meshtastic", async () => {
    mockUseAuth.mockReturnValue({
      usuario: { id: "admin-1", email: "admin@test.com", role: "admin" },
      cargando: false,
    });
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ total: 0, items: [] }),
    });

    render(<AdminPage />);

    await waitFor(() => screen.getByText("Meshtastic"));
    fireEvent.click(screen.getByText("Meshtastic"));

    expect(screen.getByText("Mensajes Meshtastic")).toBeInTheDocument();
    expect(screen.getByText("Eliminar todos los mensajes mesh")).toBeInTheDocument();
  });

  it("llama al endpoint al cambiar rol de otro usuario", async () => {
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
              id: "user-2",
              email: "juan@test.com",
              role: "user",
              is_active: true,
              created_at: "2026-02-01T00:00:00Z",
            },
          ],
        }),
      })
      .mockResolvedValueOnce({ ok: true })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total: 1, items: [] }),
      });

    render(<AdminPage />);

    await waitFor(() => screen.getByText("Hacer admin"));
    fireEvent.click(screen.getByText("Hacer admin"));

    await waitFor(() => {
      const urls = mockFetch.mock.calls.map((c) => c[0]);
      expect(urls.some((u) => String(u).includes("/api/admin/users/user-2/role?role=admin"))).toBe(true);
    });
  });
});
