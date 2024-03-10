from typing import List
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from dotenv import dotenv_values
import models
import jwt

config_credentials = dotenv_values(".env")

class EmailSchema(BaseModel):
    email: List[EmailStr]

conf = ConnectionConfig(
    MAIL_USERNAME = config_credentials["EMAIL"],
    MAIL_PASSWORD = "emeo yzdy zuuj vtlw",
    MAIL_FROM = config_credentials["EMAIL"],
    MAIL_PORT = 465,
    MAIL_SERVER = "smtp.gmail.com",
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
    token = jwt.encode(token_data, config_credentials["SECRET"], algorithm='HS256')

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
