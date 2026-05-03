import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aviso legal | ESPAlert",
  description: "Aviso legal y condiciones de uso del servicio ESPAlert.",
};

export default function AvisoLegalLayout({ children }: { children: React.ReactNode }) {
  return children;
}
