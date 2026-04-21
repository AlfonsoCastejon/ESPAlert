import type { Metadata } from "next";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import CookieBanner from "@/components/layout/CookieBanner";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
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
    <html lang="es" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: `(function(){var t=localStorage.getItem('espalert_theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');document.documentElement.setAttribute('data-theme',t)})()` }} />
        <ThemeProvider>
          <AuthProvider>
            <div className="app-layout">
              <Header />
              <main className="contenido-principal">{children}</main>
              <Footer />
            </div>
            <CookieBanner />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
