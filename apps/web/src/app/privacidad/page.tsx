export default function Privacidad() {
  return (
    <div className="legal">
      <h1 className="legal__titulo">Política de cookies</h1>
      <p className="legal__subtitulo">
        Información del uso de cookies en la plataforma ESPAlert
      </p>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">01</span>
          Qué son las cookies
        </h2>
        <p className="legal__texto">
          Las cookies son pequeños archivos de texto que un sitio web deposita en
          el dispositivo del usuario cuando este lo visita. Permiten que el sitio
          recuerde información entre visitas, como preferencias de usuario o el
          estado de la sesión.
        </p>
        <p className="legal__texto">
          De conformidad con la Ley 34/2002 (LSSI-CE) y el Reglamento (UE)
          2016/679 (RGPD), ESPAlert informa al usuario del uso de cookies en este
          sitio.
        </p>
      </section>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">02</span>
          Cookies utilizadas
        </h2>
        <p className="legal__texto">
          <strong>espalert_session</strong> — Cookie técnica de sesión. Almacena
          el token de autenticación JWT del usuario. Duración: 7 días. Su uso es
          estrictamente necesario para mantener la sesión activa.
        </p>
        <p className="legal__texto">
          <strong>espalert_prefs</strong> — Cookie de preferencias. Guarda los
          filtros de alerta y la zona geográfica seleccionada por el usuario.
          Duración: 30 días. Solo se genera si el usuario guarda sus preferencias.
        </p>
        <p className="legal__texto">
          <strong>espalert_cookie_consent</strong> — Registro del consentimiento
          del usuario. Duración: 365 días. Necesaria para no mostrar el aviso de
          cookies en visitas posteriores.
        </p>
      </section>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">03</span>
          Cookies de terceros
        </h2>
        <p className="legal__texto">
          El mapa interactivo se sirve mediante MapLibre GL con tiles de
          OpenStreetMap. Estos servicios pueden establecer sus propias cookies
          conforme a sus respectivas políticas de privacidad.
        </p>
        <p className="legal__texto">
          ESPAlert no utiliza cookies de rastreo publicitario, de redes sociales
          ni servicios de analítica de terceros.
        </p>
      </section>
    </div>
  );
}
