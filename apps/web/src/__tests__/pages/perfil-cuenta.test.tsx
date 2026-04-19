import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import CuentaPage from "@/app/perfil/cuenta/page";

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
  mockUseAuth.mockReturnValue({
    usuario: { id: "user-1", email: "user@test.com", role: "user" },
    cargando: false,
  });
});

afterEach(() => {
  vi.restoreAllMocks();
  mockPush.mockReset();
  mockUseAuth.mockReset();
  mockFetch.mockReset();
});

describe("CuentaPage", () => {
  it("redirige a login si no hay usuario", async () => {
    mockUseAuth.mockReturnValue({ usuario: null, cargando: false });
    render(<CuentaPage />);
    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/login"));
  });

  it("muestra los datos del usuario", () => {
    render(<CuentaPage />);
    expect(screen.getAllByText("user@test.com").length).toBeGreaterThan(0);
    expect(screen.getByText("user-1")).toBeInTheDocument();
  });

  it("muestra error si las contrasenas nuevas no coinciden", async () => {
    render(<CuentaPage />);
    fireEvent.change(screen.getByLabelText("Contraseña actual"), {
      target: { value: "Oldpass1" },
    });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Repetir nueva contraseña"), {
      target: { value: "Different1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cambiar contraseña" }));

    await waitFor(() =>
      expect(screen.getByText("Las contraseñas nuevas no coinciden.")).toBeInTheDocument(),
    );
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("cambia la contrasena correctamente", async () => {
    mockFetch.mockResolvedValueOnce({ status: 204 });
    render(<CuentaPage />);

    fireEvent.change(screen.getByLabelText("Contraseña actual"), {
      target: { value: "Oldpass1" },
    });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Repetir nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cambiar contraseña" }));

    await waitFor(() =>
      expect(screen.getByText("Contraseña actualizada correctamente.")).toBeInTheDocument(),
    );
  });

  it("muestra error si la contrasena actual es incorrecta (401)", async () => {
    mockFetch.mockResolvedValueOnce({ status: 401 });
    render(<CuentaPage />);

    fireEvent.change(screen.getByLabelText("Contraseña actual"), {
      target: { value: "Wrongpass1" },
    });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Repetir nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cambiar contraseña" }));

    await waitFor(() =>
      expect(screen.getByText("La contraseña actual es incorrecta.")).toBeInTheDocument(),
    );
  });

  it("muestra error si la nueva contrasena no cumple los requisitos (422)", async () => {
    mockFetch.mockResolvedValueOnce({ status: 422 });
    render(<CuentaPage />);

    fireEvent.change(screen.getByLabelText("Contraseña actual"), {
      target: { value: "Oldpass1" },
    });
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "shortpw1" },
    });
    fireEvent.change(screen.getByLabelText("Repetir nueva contraseña"), {
      target: { value: "shortpw1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Cambiar contraseña" }));

    await waitFor(() =>
      expect(
        screen.getByText(/no cumple los requisitos/),
      ).toBeInTheDocument(),
    );
  });
});
