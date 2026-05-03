import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Predicción | ESPAlert",
  description: "Consulta la predicción meteorológica diaria por municipio (datos AEMET).",
};

export default function PrediccionLayout({ children }: { children: React.ReactNode }) {
  return children;
}
