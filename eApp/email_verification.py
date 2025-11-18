import jwt
from eApp import models
from typing import List
from eApp.config import CONFIG
from dotenv import dotenv_values
from pydantic import BaseModel, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

config_credentials = dotenv_values("eApp/.env")

class EmailSchema(BaseModel):
    email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME =CONFIG.MAIL_USERNAME,
    MAIL_PASSWORD =CONFIG.MAIL_PASSWORD,
    MAIL_FROM =CONFIG.MAIL_FROM,
    MAIL_PORT = CONFIG.MAIL_PORT,
    MAIL_SERVER = CONFIG.MAIL_SERVER,
    MAIL_STARTTLS = False,
    MAIL_SSL_TLS = True,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_email(email: EmailSchema, instance: models.User):
    token_data = {
        "id": instance.id,
        "username": instance.username
    }
    token = jwt.encode(token_data,key=CONFIG.SECRET_KEY,algorithm=CONFIG.ALGORITHM)

    # Extracting the list of emails from the EmailSchema object
    email_list = tuple(email.email)

    template = f"""
    <!DOCTYPE html> 
    <html>
        <head>

        </head>
        <body>
            <div style="display: flex;align-items:center;justify-content:center;flex-direction: column">
                <h3>Account Verification</h3>
                <br>
                <p> Thanks for choosing our services. Please click on the button below to
                verify your account. </p>

                <a style="margin-top : 1rem; padding: 1rem;border-radius: 0.5rem;
                font-size:1rem;text-direction: none;background: #0275d8;color:white;"
                href="http://127.0.0.1:8000/verification/?token={token}">
                Verify your email
                </a>
            </div>
        </body>
    </html>
    """
    
    # Correct the recipients to be a list
    recipients = [str(email) for email in email_list]
    
    message = MessageSchema(
        subject="Email Verification.",
        recipients=recipients,
        body=template,
        subtype=MessageType.html)
    
    fm = FastMail(conf)
    
    await fm.send_message(message)


async def send_html_email(recipients: List[str], subject: str, html_body: str):
    """Send HTML email to recipients"""
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_body,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_subscription_expired_email(email: str, username: str, expires_at: str):
    """Send subscription expired email"""
    from eApp.internal.html_templates import payment_subscription_expired
    html = payment_subscription_expired(expires_at, username)
    await send_html_email([email], "Your Subscription has Expired", html)
