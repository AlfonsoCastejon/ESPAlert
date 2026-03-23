import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionCreate(BaseModel):
    endpoint: str = Field(
        ...,
        description="URL del endpoint push del navegador",
        examples=["https://fcm.googleapis.com/fcm/send/..."],
    )
    p256dh: str = Field(
        ...,
        description="Clave pública ECDH del cliente en base64url",
    )
    auth: str = Field(
        ...,
        description="Secreto de autenticación del cliente en base64url",
    )


class PushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(
        ...,
        description="Endpoint de la suscripción a eliminar",
    )


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    endpoint: str
    p256dh: str
    auth: str
    created_at: datetime
    updated_at: datetime


class PushSubscribeResponse(BaseModel):
    ok: bool
    message: str
