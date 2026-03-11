from pydantic import BaseModel, Field


class PushSubscribeRequest(BaseModel):
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


class PushSubscribeResponse(BaseModel):
    ok: bool
    message: str
