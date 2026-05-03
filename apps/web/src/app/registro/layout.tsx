import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Crear cuenta | ESPAlert",
  description: "Regístrate en ESPAlert para recibir alertas personalizadas de riesgo en España.",
};

export default function RegistroLayout({ children }: { children: React.ReactNode }) {
  return children;
}
