import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Iniciar sesión | ESPAlert",
  description: "Accede a tu cuenta de ESPAlert para gestionar alertas favoritas y suscripciones.",
};

export default function LoginLayout({ children }: { children: React.ReactNode }) {
  return children;
}
