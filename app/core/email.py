from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from starlette.background import BackgroundTasks
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=0,
)


async def send_verification_email(email: EmailStr, token: str, background_tasks: BackgroundTasks = None):
    verification_url = f"http://localhost:8000/auth/verify-email?token={token}"

    message = MessageSchema(
        subject="Verify Your Email",
        recipients=[email],
        body=f"""
        <h1>Welcome to Mini Social Network!</h1>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verification_url}">Verify Email</a></p>
        <p>Or copy this link: {verification_url}</p>
        <p>This link will expire in 24 hours.</p>
        """,
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    if background_tasks:
        background_tasks.add_task(fm.send_message, message)
    else:
        await fm.send_message(message)