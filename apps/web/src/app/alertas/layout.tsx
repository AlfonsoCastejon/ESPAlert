import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Alertas | ESPAlert",
  description: "Listado de alertas activas en España: AEMET, IGN, DGT, MeteoAlarm y red mesh.",
};

export default function AlertasLayout({ children }: { children: React.ReactNode }) {
  return children;
}
