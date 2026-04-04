"use client";

export default function Error({
  reset,
}: {
  error: Error;
  reset: () => void;
}) {
  return (
    <div className="pagina-estado">
      <h1 className="pagina-estado__titulo">Error</h1>
      <p className="pagina-estado__texto">Ha ocurrido un problema inesperado.</p>
      <button onClick={reset}>Reintentar</button>
    </div>
  );
}
