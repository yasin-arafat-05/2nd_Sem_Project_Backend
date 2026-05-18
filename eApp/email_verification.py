import jwt
from eApp import models
from typing import List
from eApp.config import CONFIG
from dotenv import dotenv_values
from datetime import datetime, timezone,timedelta
from pydantic import BaseModel, EmailStr
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType


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
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    token_data = {
        "id": instance.id,
        "username": instance.username,
        "exp":expire
    }

    token = jwt.encode(token_data,key=CONFIG.SECRET_KEY,algorithm=CONFIG.ALGORITHM)

    # Extracting the list of emails from the EmailSchema object
    email_list = tuple(email.email)
    template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Account Verification</title>
        <style>
            @media screen and (max-width: 600px) {{
                .email-container {{
                    width: 100% !important;
                    padding: 20px !important;
                }}
                .btn {{
                    display: block !important;
                    width: auto !important;
                    text-align: center !important;
                }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; -webkit-font-smoothing: antialiased;">

        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f6f9; padding: 40px 0;">
            <tr>
                <td align="center">
                    <table class="email-container" border="0" cellpadding="0" cellspacing="0" width="550" style="background-color: #ffffff; border-radius: 12px; padding: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;">
                        
                        <tr>
                            <td align="center" style="padding-bottom: 20px;">
                                <div style="background-color: #e6f0fa; width: 60px; height: 60px; border-radius: 50%; line-height: 60px; font-size: 28px; color: #0275d8; display: inline-block;">
                                    ✉️
                                </div>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding-bottom: 15px;">
                                <h2 style="margin: 0; color: #1a1a1a; font-size: 24px; font-weight: 700; line-height: 1.3;">
                                    Verify Your Email Address
                                </h2>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <p style="margin: 0; color: #555555; font-size: 15px; line-height: 1.6;">
                                    Thanks for choosing our services! Please click the button below to verify your account and complete your business registration.
                                </p>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="padding-bottom: 30px;">
                                <a class="btn" href="http://103.133.254.2:6085/verification?token={token}" style="background-color: #0275d8; color: #ffffff; text-decoration: none; padding: 14px 32px; font-size: 16px; font-weight: 600; border-radius: 6px; display: inline-block; transition: background-color 0.3s ease; box-shadow: 0 3px 10px rgba(2, 117, 216, 0.3);">
                                    Verify Email Account
                                </a>
                            </td>
                        </tr>

                        <tr>
                            <td align="center" style="border-top: 1px solid #eef2f5; padding-top: 20px;">
                                <p style="margin: 0; color: #999999; font-size: 12px; line-height: 1.5;">
                                    If you did not request this email, you can safely ignore it.<br>
                                    &copy; {datetime.now().year if 'datetime' in globals() else 2026} Galacticart . All rights reserved.
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>

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
