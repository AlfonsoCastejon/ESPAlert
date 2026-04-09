"use client";

/** Banner de cookies: se muestra hasta que el usuario acepta. */

import { useState, useEffect } from "react";
import Link from "next/link";

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem("espalert_cookie_consent")) {
      setVisible(true);
    }
  }, []);

  function aceptar() {
    localStorage.setItem("espalert_cookie_consent", "accepted");
    setVisible(false);
  }

  if (!visible) return null;

  return (
    <div className="banner-cookies" role="banner">
      <p className="banner-cookies__texto">
        ESPAlert utiliza cookies técnicas necesarias para el funcionamiento del
        sitio. No utilizamos cookies de rastreo publicitario ni de analítica de
        terceros.
      </p>
      <div className="banner-cookies__acciones">
        <Link href="/privacidad" className="banner-cookies__enlace">
          Más información
        </Link>
        <button className="banner-cookies__aceptar" onClick={aceptar}>
          Acepto las cookies
        </button>
      </div>
    </div>
  );
}
