export default function AvisoLegal() {
  return (
    <div className="legal">
      <h1 className="legal__titulo">Aviso legal</h1>
      <p className="legal__subtitulo">
        Información legal sobre el uso y condiciones de uso de ESPAlert
      </p>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">01</span>
          Identificación del titular
        </h2>
        <p className="legal__texto">
          En cumplimiento del artículo 10 de la Ley 34/2002, de 11 de julio, de
          Servicios de la Sociedad de la Información y del Comercio Electrónico
          (LSSI-CE), se pone a disposición del usuario la siguiente información.
        </p>
        <p className="legal__texto">
          ESPAlert es un proyecto académico desarrollado como Trabajo Final del
          Ciclo Superior de Desarrollo de Aplicaciones Web. Responsable: Alfonso
          Castejón. Contacto: alfonso@espalert.es
        </p>
      </section>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">02</span>
          Objeto y condiciones de uso
        </h2>
        <p className="legal__texto">
          ESPAlert es una plataforma de visualización de alertas de riesgo para
          España. La información mostrada proviene exclusivamente de fuentes
          públicas oficiales: Agencia Estatal de Meteorología (AEMET), Instituto
          Geográfico Nacional (IGN), Dirección General de Tráfico (DGT) y
          MeteoAlarm.
        </p>
        <p className="legal__texto">
          El acceso y uso de este sitio web es libre y gratuito. El usuario se
          compromete a hacer un uso lícito y adecuado del servicio, de conformidad
          con la legislación vigente, la moral y el orden público.
        </p>
        <p className="legal__texto">
          Esta plataforma no sustituye en ningún caso a los canales oficiales de
          emergencias. Ante cualquier situación de riesgo, el usuario debe
          contactar con el número de emergencias 112.
        </p>
      </section>

      <section className="legal__seccion">
        <h2 className="legal__encabezado">
          <span className="legal__numero">03</span>
          Propiedad intelectual
        </h2>
        <p className="legal__texto">
          El código fuente de ESPAlert se distribuye bajo licencia MIT. Los
          conjuntos de datos mostrados son propiedad de sus respectivos organismos
          públicos y se utilizan conforme a sus condiciones de reutilización de
          información del sector público.
        </p>
      </section>
    </div>
  );
}
