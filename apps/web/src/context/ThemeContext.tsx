"use client";

/**
 * Contexto de tema claro/oscuro.
 * Lee la preferencia guardada en localStorage o la del sistema operativo.
 */

import { createContext, useContext, useEffect, useState } from "react";

type Tema = "light" | "dark";

interface ThemeContextValue {
  tema: Tema;
  toggleTema: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  tema: "light",
  toggleTema: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [tema, setTema] = useState<Tema>("light");

  useEffect(() => {
    const guardado = localStorage.getItem("espalert_theme") as Tema | null;
    const preferOscuro = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const inicial = guardado || (preferOscuro ? "dark" : "light");
    setTema(inicial);
    document.documentElement.setAttribute("data-theme", inicial);
  }, []);

  function toggleTema() {
    const nuevo = tema === "light" ? "dark" : "light";
    setTema(nuevo);
    localStorage.setItem("espalert_theme", nuevo);
    document.documentElement.setAttribute("data-theme", nuevo);
  }

  return (
    <ThemeContext.Provider value={{ tema, toggleTema }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
