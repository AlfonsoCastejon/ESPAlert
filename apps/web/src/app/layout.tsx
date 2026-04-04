import type { Metadata } from "next";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import CookieBanner from "@/components/layout/CookieBanner";
import { ThemeProvider } from "@/context/ThemeContext";
import "@/styles/main.scss";

export const metadata: Metadata = {
  title: "ESPAlert",
  description: "Plataforma de alertas de riesgo para España",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <body>
        <ThemeProvider>
          <div className="app-layout">
            <Header />
            <div className="contenido-principal">{children}</div>
            <Footer />
          </div>
          <CookieBanner />
        </ThemeProvider>
      </body>
    </html>
  );
}
