import Link from "next/link";

export default function NotFound() {
  return (
    <div className="pagina-estado">
      <h1 className="pagina-estado__codigo">ERROR</h1>
      <h2 className="pagina-estado__codigo">404</h2>
      <Link href="/" className="pagina-estado__enlace">
        Volver al mapa
      </Link>
    </div>
  );
}
