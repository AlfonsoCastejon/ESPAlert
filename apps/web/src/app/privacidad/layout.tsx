import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de privacidad | ESPAlert",
  description: "Información sobre el tratamiento de datos personales en ESPAlert.",
};

export default function PrivacidadLayout({ children }: { children: React.ReactNode }) {
  return children;
}
