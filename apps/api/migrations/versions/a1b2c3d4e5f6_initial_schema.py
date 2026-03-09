"""Esquema inicial: alerts, push_subscriptions, mesh_messages, fetch_logs

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-03-09 00:00:00.000000
"""

from alembic import op
import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # Extensión PostGIS necesaria para el tipo geometry y los índices espaciales
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Enumerados nativos de PostgreSQL
    alert_source = postgresql.ENUM(
        "aemet", "ign", "dgt", "meteoalarm", "meshtastic",
        name="alert_source",
        create_type=False,
    )
    alert_type = postgresql.ENUM(
        "meteorological", "seismic", "traffic", "mesh", "other",
        name="alert_type",
        create_type=False,
    )
    alert_severity = postgresql.ENUM(
        "minor", "moderate", "severe", "extreme", "unknown",
        name="alert_severity",
        create_type=False,
    )
    alert_status = postgresql.ENUM(
        "actual", "exercise", "system", "test", "draft",
        name="alert_status",
        create_type=False,
    )
    fetch_status = postgresql.ENUM(
        "running", "success", "failure", "partial",
        name="fetch_status",
        create_type=False,
    )

    alert_source.create(op.get_bind(), checkfirst=True)
    alert_type.create(op.get_bind(), checkfirst=True)
    alert_severity.create(op.get_bind(), checkfirst=True)
    alert_status.create(op.get_bind(), checkfirst=True)
    fetch_status.create(op.get_bind(), checkfirst=True)

    # Tabla alerts
    op.create_table(
        "alerts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(255),
            nullable=True,
            comment="Identificador original en la fuente externa",
        ),
        sa.Column("source", alert_source, nullable=False),
        sa.Column("alert_type", alert_type, nullable=False),
        sa.Column(
            "severity",
            alert_severity,
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "status",
            alert_status,
            nullable=False,
            server_default="actual",
        ),
        sa.Column("headline", sa.Text, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("area_description", sa.String(512), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                nullable=True,
            ),
            nullable=True,
            comment="Geometría del área de la alerta en WGS84",
        ),
        sa.Column(
            "effective_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "fetched_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "raw_data",
            postgresql.JSONB,
            nullable=True,
            comment="Payload original sin procesar de la fuente",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id", name="uq_alerts_external_id"),
    )
    op.create_index("ix_alerts_external_id", "alerts", ["external_id"])
    op.create_index("ix_alerts_source", "alerts", ["source"])
    op.create_index("ix_alerts_alert_type", "alerts", ["alert_type"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_effective_at", "alerts", ["effective_at"])
    op.create_index("ix_alerts_expires_at", "alerts", ["expires_at"])
    op.create_index(
        "ix_alerts_source_severity",
        "alerts",
        ["source", "severity"],
    )
    op.create_index(
        "ix_alerts_geometry",
        "alerts",
        ["geometry"],
        postgresql_using="gist",
    )

    # Tabla push_subscriptions
    op.create_table(
        "push_subscriptions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "endpoint",
            sa.Text,
            nullable=False,
            comment="URL del endpoint del servicio push del navegador",
        ),
        sa.Column(
            "p256dh",
            sa.Text,
            nullable=False,
            comment="Clave pública del cliente para cifrado ECDH",
        ),
        sa.Column(
            "auth",
            sa.Text,
            nullable=False,
            comment="Secreto de autenticación del cliente",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )
    op.create_index(
        "ix_push_subscriptions_endpoint",
        "push_subscriptions",
        ["endpoint"],
    )

    # Tabla mesh_messages
    op.create_table(
        "mesh_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "node_id",
            sa.String(32),
            nullable=False,
            comment="Identificador hexadecimal del nodo Meshtastic emisor",
        ),
        sa.Column(
            "channel",
            sa.String(64),
            nullable=True,
            comment="Canal del nodo en la red mesh",
        ),
        sa.Column(
            "packet_id",
            sa.BigInteger,
            nullable=True,
            comment="ID de paquete asignado por el protocolo Meshtastic",
        ),
        sa.Column(
            "message",
            sa.Text,
            nullable=False,
            comment="Contenido del mensaje recibido",
        ),
        sa.Column(
            "latitude",
            sa.Float,
            nullable=True,
            comment="Latitud del nodo emisor en WGS84",
        ),
        sa.Column(
            "longitude",
            sa.Float,
            nullable=True,
            comment="Longitud del nodo emisor en WGS84",
        ),
        sa.Column(
            "altitude",
            sa.Integer,
            nullable=True,
            comment="Altitud del nodo emisor en metros",
        ),
        sa.Column(
            "snr",
            sa.Float,
            nullable=True,
            comment="Relación señal/ruido (dB)",
        ),
        sa.Column(
            "rssi",
            sa.Integer,
            nullable=True,
            comment="Intensidad de señal recibida (dBm)",
        ),
        sa.Column(
            "received_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "raw_payload",
            postgresql.JSONB,
            nullable=True,
            comment="Payload MQTT completo sin procesar",
        ),
        sa.Column(
            "alert_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="Alerta asociada si el mensaje ha generado o está vinculado a una alerta",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["alert_id"],
            ["alerts.id"],
            name="fk_mesh_messages_alert_id",
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_mesh_messages_node_id", "mesh_messages", ["node_id"])
    op.create_index("ix_mesh_messages_alert_id", "mesh_messages", ["alert_id"])
    op.create_index(
        "ix_mesh_messages_received_at",
        "mesh_messages",
        ["received_at"],
    )

    # Tabla fetch_logs
    op.create_table(
        "fetch_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "source",
            alert_source,
            nullable=False,
            comment="Fuente de datos consultada",
        ),
        sa.Column(
            "status",
            fetch_status,
            nullable=False,
            server_default="running",
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "finished_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "alerts_fetched",
            sa.Integer,
            server_default=sa.text("0"),
            nullable=False,
            comment="Total de alertas obtenidas de la fuente",
        ),
        sa.Column(
            "alerts_new",
            sa.Integer,
            server_default=sa.text("0"),
            nullable=False,
            comment="Alertas nuevas insertadas en esta ejecución",
        ),
        sa.Column(
            "duration_ms",
            sa.Integer,
            nullable=True,
            comment="Duración total de la consulta en milisegundos",
        ),
        sa.Column(
            "error_message",
            sa.Text,
            nullable=True,
            comment="Mensaje de error si el estado es FAILURE o PARTIAL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fetch_logs_source", "fetch_logs", ["source"])
    op.create_index("ix_fetch_logs_started_at", "fetch_logs", ["started_at"])


def downgrade() -> None:
    op.drop_table("fetch_logs")
    op.drop_table("mesh_messages")
    op.drop_table("push_subscriptions")
    op.drop_table("alerts")

    op.execute("DROP TYPE IF EXISTS fetch_status")
    op.execute("DROP TYPE IF EXISTS alert_status")
    op.execute("DROP TYPE IF EXISTS alert_severity")
    op.execute("DROP TYPE IF EXISTS alert_type")
    op.execute("DROP TYPE IF EXISTS alert_source")
