"use client";

/** Cabecera con logo, navegación, auth contextual y menú hamburguesa en móvil. */

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Sun, Moon, Menu, X } from "lucide-react";
import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/context/AuthContext";

export default function Header() {
  const { tema, toggleTema } = useTheme();
  const { usuario, cargando, logout } = useAuth();
  const [menuAbierto, setMenuAbierto] = useState(false);

  const cerrarSesion = async () => {
    await logout();
    setMenuAbierto(false);
  };

  return (
    <header className="cabecera">
      <Link href="/" className="cabecera__logo" aria-label="ESPAlert - Inicio">
        <Image src="/icon.png" alt="" width={66} height={36} priority />
        <span className="cabecera__marca" aria-hidden="true"><span className="cabecera__marca-esp">ESP</span>Alert</span>
      </Link>

      <div className="cabecera__acciones">
        <nav className="cabecera__nav">
          <Link href="/prediccion">Predicción</Link>
          <Link href="/alertas">Alertas</Link>
        </nav>
        <button className="cabecera__tema" aria-label="Cambiar tema" title="Cambiar tema" onClick={toggleTema}>
          {tema === "dark" ? <Sun size={20} /> : <Moon size={20} />}
        </button>

        {!cargando && (
          usuario ? (
            <>
              {usuario.role === "admin" && (
                <Link href="/admin" className="cabecera__btn cabecera__btn--admin">
                  Admin
                </Link>
              )}
              <Link href="/perfil" className="cabecera__usuario">
                {usuario.email}
              </Link>
              <button className="cabecera__btn cabecera__btn--login" onClick={cerrarSesion}>
                Cerrar sesión
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="cabecera__btn cabecera__btn--login">
                Iniciar sesión
              </Link>
              <Link href="/registro" className="cabecera__btn cabecera__btn--registro">
                Registrarse
              </Link>
            </>
          )
        )}
      </div>

      <div className="cabecera__movil">
        <button className="cabecera__tema" aria-label="Cambiar tema" title="Cambiar tema" onClick={toggleTema}>
          {tema === "dark" ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button
          className="cabecera__burger"
          aria-label={menuAbierto ? "Cerrar menú" : "Abrir menú"}
          title={menuAbierto ? "Cerrar menú" : "Abrir menú"}
          onClick={() => setMenuAbierto(!menuAbierto)}
        >
          {menuAbierto ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {menuAbierto && (
        <nav className="cabecera__desplegable" onClick={() => setMenuAbierto(false)}>
          <Link href="/prediccion" className="cabecera__desplegable-enlace">Predicción</Link>
          <Link href="/alertas" className="cabecera__desplegable-enlace">Alertas</Link>
          <hr className="cabecera__desplegable-separador" />
          {usuario ? (
            <>
              <Link href="/perfil" className="cabecera__desplegable-enlace">Mi perfil</Link>
              {usuario.role === "admin" && (
                <Link href="/admin" className="cabecera__desplegable-enlace">Administración</Link>
              )}
              <button className="cabecera__desplegable-enlace" onClick={cerrarSesion}>
                Cerrar sesión
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="cabecera__desplegable-enlace">Iniciar sesión</Link>
              <Link href="/registro" className="cabecera__desplegable-enlace">Registrarse</Link>
            </>
          )}
        </nav>
      )}
    </header>
  );
}
