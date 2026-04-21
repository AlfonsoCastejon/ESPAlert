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

  it("muestra aviso en tiempo real si las contrasenas no coinciden", async () => {
    render(<CuentaPage />);
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "Newpass1" },
    });
    fireEvent.change(screen.getByLabelText("Repetir nueva contraseña"), {
      target: { value: "Different1" },
    });

    await waitFor(() =>
      expect(screen.getByText(/Las contraseñas no coinciden/)).toBeInTheDocument(),
    );
    expect(screen.getByRole("button", { name: "Cambiar contraseña" })).toBeDisabled();
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it("muestra los requisitos en tiempo real mientras se escribe", () => {
    render(<CuentaPage />);
    fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
      target: { value: "abc" },
    });
    expect(screen.getByText(/Al menos 8 caracteres/)).toBeInTheDocument();
    expect(screen.getByText(/Una letra mayúscula/)).toBeInTheDocument();
    expect(screen.getByText(/Un número/)).toBeInTheDocument();
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

  it("muestra error si el servidor responde 422 pese a pasar la validación del cliente", async () => {
    // La contraseña pasa los requisitos del formulario, pero imaginamos un
    // endpoint más estricto que la rechaza igualmente.
    mockFetch.mockResolvedValueOnce({ status: 422 });
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
      expect(
        screen.getByText(/no cumple los requisitos/),
      ).toBeInTheDocument(),
    );
  });
});
