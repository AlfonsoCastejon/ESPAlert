import Link from "next/link";

export default function Footer() {
  return (
    <footer className="pie">
      <div className="pie__marca">
        <span className="pie__marca-esp">ESP</span>Alert
      </div>
      <div className="pie__enlaces">
        <Link href="/aviso-legal">Aviso legal</Link>
        <Link href="/privacidad">Política de cookies</Link>
      </div>
    </footer>
  );
}
