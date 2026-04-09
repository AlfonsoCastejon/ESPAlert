"""Enumeraciones compartidas por los modelos de alerta y fetch_log."""

import enum


class AlertSource(str, enum.Enum):
    AEMET = "aemet"
    IGN = "ign"
    DGT = "dgt"
    METEOALARM = "meteoalarm"
    MESHTASTIC = "meshtastic"


class AlertType(str, enum.Enum):
    METEOROLOGICAL = "meteorological"
    SEISMIC = "seismic"
    TRAFFIC = "traffic"
    MESH = "mesh"
    OTHER = "other"


class AlertSeverity(str, enum.Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"
    UNKNOWN = "unknown"


class AlertStatus(str, enum.Enum):
    ACTUAL = "actual"
    EXERCISE = "exercise"
    SYSTEM = "system"
    TEST = "test"
    DRAFT = "draft"
    EXPIRED = "expired"


class FetchStatus(str, enum.Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
