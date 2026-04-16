import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Header from "@/components/layout/Header";

// Mock de contextos
const mockToggleTema = vi.fn();
const mockLogout = vi.fn();

let mockUsuario: { email: string; role: string } | null = null;
let mockCargando = false;

vi.mock("@/context/ThemeContext", () => ({
  useTheme: () => ({ tema: "light", toggleTema: mockToggleTema }),
}));

vi.mock("@/context/AuthContext", () => ({
  useAuth: () => ({
    usuario: mockUsuario,
    cargando: mockCargando,
    logout: mockLogout,
  }),
}));

vi.mock("next/link", () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe("Header", () => {
  beforeEach(() => {
    mockUsuario = null;
    mockCargando = false;
    vi.clearAllMocks();
  });

  it("muestra botones de login y registro cuando no hay usuario", () => {
    render(<Header />);
    expect(screen.getByText("Iniciar sesión")).toBeInTheDocument();
    expect(screen.getByText("Registrarse")).toBeInTheDocument();
  });

  it("muestra email y boton cerrar sesion cuando hay usuario", () => {
    mockUsuario = { email: "test@test.com", role: "user" };
    render(<Header />);
    expect(screen.getByText("test@test.com")).toBeInTheDocument();
    expect(screen.getByText("Cerrar sesión")).toBeInTheDocument();
    expect(screen.queryByText("Iniciar sesión")).not.toBeInTheDocument();
  });

  it("no muestra botones de auth mientras carga", () => {
    mockCargando = true;
    render(<Header />);
    expect(screen.queryByText("Iniciar sesión")).not.toBeInTheDocument();
    expect(screen.queryByText("Cerrar sesión")).not.toBeInTheDocument();
  });

  it("llama a logout al pulsar cerrar sesion", async () => {
    mockUsuario = { email: "test@test.com", role: "user" };
    render(<Header />);
    fireEvent.click(screen.getByText("Cerrar sesión"));
    await waitFor(() => expect(mockLogout).toHaveBeenCalled());
  });

  it("cambia el tema al pulsar el boton", () => {
    render(<Header />);
    fireEvent.click(screen.getAllByLabelText("Cambiar tema")[0]);
    expect(mockToggleTema).toHaveBeenCalled();
  });

  it("muestra enlaces de navegacion", () => {
    render(<Header />);
    expect(screen.getByText("Predicción")).toBeInTheDocument();
    expect(screen.getByText("Alertas")).toBeInTheDocument();
  });

  it("muestra el logo con alt text", () => {
    render(<Header />);
    expect(screen.getByAltText("ESPAlert")).toBeInTheDocument();
  });
});
