import type { Metadata } from "next";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import CookieBanner from "@/components/layout/CookieBanner";
import { ThemeProvider } from "@/context/ThemeContext";
import { AuthProvider } from "@/context/AuthContext";
import "@/styles/main.scss";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://espalert.app";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "ESPAlert",
    template: "%s | ESPAlert",
  },
  description: "Plataforma de alertas multi-riesgo para España: AEMET, IGN, DGT, MeteoAlarm y red mesh.",
  applicationName: "ESPAlert",
  manifest: "/manifest.json",
  icons: { icon: "/icon.png", apple: "/icon.png" },
  openGraph: {
    type: "website",
    locale: "es_ES",
    url: SITE_URL,
    siteName: "ESPAlert",
    title: "ESPAlert — Alertas multi-riesgo para España",
    description: "Avisos de AEMET, IGN, DGT, MeteoAlarm y red mesh Meshtastic en tiempo real.",
    images: [{ url: "/icon.png", width: 512, height: 512, alt: "ESPAlert" }],
  },
  twitter: {
    card: "summary",
    title: "ESPAlert — Alertas multi-riesgo para España",
    description: "Avisos de AEMET, IGN, DGT, MeteoAlarm y red mesh Meshtastic en tiempo real.",
    images: ["/icon.png"],
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://tiles.openfreemap.org" crossOrigin="anonymous" />
        <link rel="preconnect" href="https://public.opendatasoft.com" crossOrigin="anonymous" />
      </head>
      <body suppressHydrationWarning>
        <script dangerouslySetInnerHTML={{ __html: `(function(){var t=localStorage.getItem('espalert_theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light');document.documentElement.setAttribute('data-theme',t)})()` }} />
        <ThemeProvider>
          <AuthProvider>
            <a href="#contenido-principal" className="skip-link">
              Saltar al contenido principal
            </a>
            <div className="app-layout">
              <Header />
              <main id="contenido-principal" className="contenido-principal">{children}</main>
              <Footer />
            </div>
            <CookieBanner />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
