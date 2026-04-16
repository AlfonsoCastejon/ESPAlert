import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import RegistroPage from "@/app/registro/page";

const mockRegistro = vi.fn();
const mockPush = vi.fn();

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    registro: mockRegistro,
    usuario: null,
    cargando: false,
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("RegistroPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza el formulario con los campos necesarios", () => {
    render(<RegistroPage />);
    expect(screen.getByText("Crear cuenta")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("tu@email.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Mínimo 8 caracteres")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Repite la contraseña")).toBeInTheDocument();
  });

  it("muestra feedback en tiempo real de requisitos de contraseña", () => {
    render(<RegistroPage />);

    fireEvent.change(screen.getByPlaceholderText("Mínimo 8 caracteres"), {
      target: { value: "short" },
    });

    expect(screen.getByText("Mínimo 8 caracteres")).toBeInTheDocument();
    expect(screen.getByText("Una letra mayúscula")).toBeInTheDocument();
    expect(screen.getByText("Un número")).toBeInTheDocument();
  });

  it("muestra aviso si las contraseñas no coinciden", () => {
    render(<RegistroPage />);

    fireEvent.change(screen.getByPlaceholderText("Mínimo 8 caracteres"), {
      target: { value: "Password1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Repite la contraseña"), {
      target: { value: "Different1" },
    });

    expect(screen.getByText("Las contraseñas no coinciden")).toBeInTheDocument();
  });

  it("deshabilita el boton si la contraseña no cumple requisitos", () => {
    render(<RegistroPage />);

    fireEvent.change(screen.getByPlaceholderText("Mínimo 8 caracteres"), {
      target: { value: "short" },
    });

    expect(screen.getByRole("button", { name: /registrarse/i })).toBeDisabled();
  });

  it("redirige al home tras registro exitoso", async () => {
    mockRegistro.mockResolvedValueOnce(null);
    render(<RegistroPage />);

    fireEvent.change(screen.getByPlaceholderText("tu@email.com"), {
      target: { value: "new@test.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Mínimo 8 caracteres"), {
      target: { value: "Password1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Repite la contraseña"), {
      target: { value: "Password1" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /registrarse/i }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });

  it("tiene enlace al login", () => {
    render(<RegistroPage />);
    expect(screen.getByText("Inicia sesión")).toBeInTheDocument();
  });
});
