"""
Email service for sending transactional emails.

This module provides email functionality for user verification and password reset
using FastMail with HTML templates and SMTP configuration.
"""

from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, NameEmail

from src.services.auth import create_email_token
from src.conf.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.SMTP_FROM,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME=settings.SMTP_FROM_NAME,
    MAIL_STARTTLS=settings.SMTP_STARTTLS,
    MAIL_SSL_TLS=settings.SMTP_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).cwd() / "templates",
)
"""FastMail configuration using SMTP settings from application config."""


async def send_verification_email(email: EmailStr, username: str, host: str) -> None:
    """
    Send email verification message to user.

    Sends an HTML email with a verification token link to confirm the user's email address.
    Uses the 'email-verification.html' template.

    :param email: Recipient's email address.
    :type email: EmailStr
    :param username: Recipient's username for personalization.
    :type username: str
    :param host: Application host URL for building verification link.
    :type host: str
    :return: None
    :raises ConnectionErrors: If email sending fails (caught and logged).
    """
    try:
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[NameEmail(email=email, name=username)],
            template_body={
                "host": host,
                "username": username,
                "token": create_email_token({"sub": email}),
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email-verification.html")
    except ConnectionErrors as e:
        print(f"Failed to send email to {email}: {e}")


async def send_reset_password_email(
    email: EmailStr, username: str, host: str, reset_token: str
) -> None:
    """
    Send password reset email to user.

    Sends an HTML email with a password reset token link to allow the user
    to reset their password. Uses the 'reset-password.html' template.

    :param email: Recipient's email address.
    :type email: EmailStr
    :param username: Recipient's username for personalization.
    :type username: str
    :param host: Application host URL for building reset link.
    :type host: str
    :param reset_token: Password reset token for verification.
    :type reset_token: str
    :return: None
    :raises ConnectionErrors: If email sending fails (caught and logged).
    """
    try:
        message = MessageSchema(
            subject="Reset your password",
            recipients=[NameEmail(email=email, name=username)],
            template_body={
                "host": host,
                "username": username,
                "token": reset_token,
            },
            subtype=MessageType.html,
        )
        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset-password.html")
    except ConnectionErrors as e:
        print(f"Failed to send email to {email}: {e}")
