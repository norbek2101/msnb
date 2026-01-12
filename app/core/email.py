from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from starlette.background import BackgroundTasks
import os
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "user"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "password"),
    MAIL_FROM = os.getenv("MAIL_FROM", "admin@example.com"),
    MAIL_PORT = 587,
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS = True,
    MAIL_SSL_TLS = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    SUPPRESS_SEND = 0, 
)

async def send_verification_email(email: EmailStr, code: str, background_tasks: BackgroundTasks = None):
    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[email],
        body=f"<h1>Welcome!</h1><p>Your verification code is: <strong>{code}</strong></p>",
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    
    if background_tasks:
        background_tasks.add_task(fm.send_message, message)
    else:
        await fm.send_message(message)