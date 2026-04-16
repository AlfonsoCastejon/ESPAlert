import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import LoginPage from "@/app/login/page";

const mockLogin = vi.fn();
const mockPush = vi.fn();

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    login: mockLogin,
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

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renderiza el formulario con email, password y boton", () => {
    render(<LoginPage />);
    expect(screen.getByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("tu@email.com")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Tu contraseña")).toBeInTheDocument();
  });

  it("redirige al home tras login exitoso", async () => {
    mockLogin.mockResolvedValueOnce(null);
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("tu@email.com"), {
      target: { value: "user@test.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Tu contraseña"), {
      target: { value: "Password1" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /iniciar sesión/i }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith("/"));
  });

  it("muestra error si login falla", async () => {
    mockLogin.mockResolvedValueOnce("Credenciales inválidas");
    render(<LoginPage />);

    fireEvent.change(screen.getByPlaceholderText("tu@email.com"), {
      target: { value: "bad@test.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("Tu contraseña"), {
      target: { value: "wrong123" },
    });
    fireEvent.submit(screen.getByRole("button", { name: /iniciar sesión/i }));

    await waitFor(() =>
      expect(screen.getByText("Credenciales inválidas")).toBeInTheDocument(),
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("tiene enlace al registro", () => {
    render(<LoginPage />);
    expect(screen.getByText("Regístrate")).toBeInTheDocument();
  });
});
